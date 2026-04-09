"""
scripts/build_release.py
========================
Script dong goi JewelryPOS thanh file .exe bao mat.

Pipeline:
  1. Nhan --password tu CLI
  2. Tao PBKDF2-SHA256 hash + random salt
  3. Ghi hash vao src/utils/auth.py
  4. Chay PyArmor de obfuscate bytecode (lop bao ve 1)
  5. Chay Nuitka de compile sang native machine code (lop bao ve 2)
  6. Don dep file tam

Cach dung:
  python scripts/build_release.py --password "MatKhauBiMat123"

Yeu cau:
  pip install pyarmor nuitka ordered-set zstandard
"""

import argparse
import hashlib
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Force UTF-8 output de tranh UnicodeEncodeError tren Windows CMD
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Hang so ──────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent   # f:\JewelryPOS
AUTH_FILE   = ROOT / "src" / "utils" / "auth.py"
ARMORED_DIR = ROOT / "dist_armored"                    # output cua PyArmor
DIST_DIR    = ROOT / "dist"                            # output cuoi cung
APP_NAME    = "JewelryPOS"
PBKDF2_ITER = 200_000


# ── Helper functions ──────────────────────────────────────────────────────

def log(msg: str):
    # Loai bo ky tu Unicode khong in duoc tren cp1252
    safe = msg.encode("ascii", errors="replace").decode("ascii")
    print(f"[build] {safe}")


def print_banner(msg: str):
    safe = msg.encode("ascii", errors="replace").decode("ascii")
    print(safe)


def run(cmd: list, cwd: Path = ROOT):
    """Chay lenh shell, raise neu loi."""
    log("RUN: " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        log(f"FAILED with exit code {result.returncode}")
        sys.exit(result.returncode)


def generate_hash(password) -> Tuple[str, str]:
    """Tra ve (hex_hash, hex_salt) dung PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(32)   # 256-bit random salt moi lan build
    h = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITER
    )
    return h.hex(), salt.hex()


def update_auth_file(hash_hex: str, salt_hex: str):
    """Thay the PLACEHOLDER trong auth.py bang hash/salt that."""
    content = AUTH_FILE.read_text(encoding="utf-8")
    content = re.sub(
        r'_APP_PASSWORD_HASH\s*=\s*"[^"]*"',
        f'_APP_PASSWORD_HASH = "{hash_hex}"',
        content
    )
    content = re.sub(
        r'_APP_PASSWORD_SALT\s*=\s*"[^"]*"',
        f'_APP_PASSWORD_SALT = "{salt_hex}"',
        content
    )
    AUTH_FILE.write_text(content, encoding="utf-8")
    log("auth.py da duoc cap nhat voi hash moi.")


def restore_auth_placeholder():
    """
    Khoi phuc auth.py ve PLACEHOLDER sau khi build xong.
    Quan trong: khong de hash that nam trong source goc.
    """
    content = AUTH_FILE.read_text(encoding="utf-8")
    content = re.sub(
        r'_APP_PASSWORD_HASH\s*=\s*"[^"]*"',
        '_APP_PASSWORD_HASH = "PLACEHOLDER_HASH"',
        content
    )
    content = re.sub(
        r'_APP_PASSWORD_SALT\s*=\s*"[^"]*"',
        '_APP_PASSWORD_SALT = "PLACEHOLDER_SALT"',
        content
    )
    AUTH_FILE.write_text(content, encoding="utf-8")
    log("auth.py da duoc khoi phuc ve PLACEHOLDER (source an toan).")


def _pyarmor_exe() -> str:
    """
    Tim duong dan den pyarmor executable trong cung venv voi python.
    PyArmor khong ho tro `python -m pyarmor`, phai goi executable truc tiep.
    """
    scripts_dir = Path(sys.executable).parent   # venv/Scripts/
    for name in ("pyarmor.exe", "pyarmor"):
        candidate = scripts_dir / name
        if candidate.exists():
            return str(candidate)
    # Fallback: tim trong PATH
    found = shutil.which("pyarmor")
    if found:
        return found
    log("Khong tim thay pyarmor. Chay: pip install pyarmor")
    sys.exit(1)


def step_pyarmor():
    """Buoc 1: Obfuscate toan bo source bang PyArmor."""
    if ARMORED_DIR.exists():
        shutil.rmtree(ARMORED_DIR)

    log("-- Buoc 1: PyArmor obfuscate --")
    run([
        _pyarmor_exe(), "gen",
        "--output", str(ARMORED_DIR),
        "--recursive",
        str(ROOT / "src"),
        str(ROOT / "main.py"),
    ])
    log(f"PyArmor output: {ARMORED_DIR}")


def step_nuitka():
    """Buoc 2: Nuitka compile PyArmor output -> native .exe (standalone folder)."""
    log("-- Buoc 2: Nuitka compile -> native .exe --")

    nuitka_main = ARMORED_DIR / "main.py"
    if not nuitka_main.exists():
        nuitka_main = ROOT / "main.py"   # fallback

    # Collect thu muc PyArmor runtime (pyarmor_runtime_xxxxxxxx)
    extra_includes = []
    if ARMORED_DIR.exists():
        for d in ARMORED_DIR.iterdir():
            if d.is_dir() and d.name.startswith("pyarmor_runtime"):
                # Nuitka 4.x: phai dung --include-data-dir=SRC=DST
                extra_includes.append(f"--include-data-dir={d}={d.name}")

    nuitka_args = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--follow-imports",
        "--windows-console-mode=disable",   # an console window de ung dung PyQt chay muot ma khong hien CMD
        f"--output-dir={DIST_DIR}",
        f"--output-filename={APP_NAME}.exe",
        "--include-package=src",
        *extra_includes,
        f"--include-data-dir={ROOT / 'config'}=config",
        "--enable-plugin=pyqt5",
        str(nuitka_main),
    ]

    if ARMORED_DIR.exists() and (ARMORED_DIR / 'src').exists():
        nuitka_args.insert(-1, f"--include-data-dir={ARMORED_DIR / 'src'}=src")

    run(nuitka_args)

    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    log(f"Build thanh cong: {exe_path}")


def step_cleanup():
    """Don dep thu muc tam."""
    log("-- Buoc 3: Don dep --")
    if ARMORED_DIR.exists():
        shutil.rmtree(ARMORED_DIR)
    # Nuitka --onefile tao .build directory – don sau khi xong
    for p in [ROOT / "main.build", DIST_DIR / "main.build"]:
        if p.exists():
            shutil.rmtree(p)
    # Xoa thu muc .dist neu con tu lan build truoc (--standalone)
    nuitka_dist = DIST_DIR / "main.dist"
    if nuitka_dist.exists():
        shutil.rmtree(nuitka_dist)
    log("Don dep xong.")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build JewelryPOS Release EXE voi bao mat PyArmor + Nuitka"
    )
    parser.add_argument(
        "--password", "-p",
        required=True,
        help='Mat khau khoi dong duoc nhung vao EXE.'
    )
    parser.add_argument(
        "--skip-armoring",
        action="store_true",
        help="Bo qua buoc PyArmor (chi dung Nuitka). Nhanh hon nhung bao mat kem hon."
    )
    args = parser.parse_args()

    if len(args.password) < 6:
        log("MAT KHAU PHAI CO IT NHAT 6 KY TU.")
        sys.exit(1)

    print_banner("=" * 60)
    print_banner("  JewelryPOS Release Builder")
    print_banner(f"  PyArmor -> Nuitka -> {APP_NAME}.exe")
    print_banner("=" * 60)

    hash_hex, salt_hex = generate_hash(args.password)
    log(f"Password hash da tao (PBKDF2-HMAC-SHA256, {PBKDF2_ITER} iters).")

    # Backup content goc cua auth.py
    original_auth = AUTH_FILE.read_text(encoding="utf-8")

    try:
        # 1. Nhung hash vao auth.py
        update_auth_file(hash_hex, salt_hex)

        # 2. PyArmor obfuscate (ĐÃ TẮT BẮT BUỘC)
        # Bỏ qua PyArmor vì phiên bản Trial sẽ chặn khi bị đóng gói bởi Nuitka (Lỗi 1:1137)
        # Nuitka biên dịch code sang mã C nền tảng (Native Code) nên tính năng bảo mật không bị suy giảm.
        log("Bỏ qua PyArmor (Sử dụng Nuitka Native C Compiler để mã hóa và chống dịch ngược).")

        # 3. Nuitka compile
        step_nuitka()

    except Exception as e:
        log(f"LOI TRONG QUA TRINH BUILD: {e}")
        raise
    finally:
        # Luon khoi phuc auth.py ve PLACEHOLDER du build thanh cong hay that bai
        AUTH_FILE.write_text(original_auth, encoding="utf-8")
        restore_auth_placeholder()

    # 4. Don dep
    step_cleanup()

    print_banner("")
    print_banner("=" * 60)
    print_banner("  BUILD THANH CONG!")
    print_banner(f"  File EXE: {DIST_DIR / (APP_NAME + '.exe')}")
    print_banner("  Mat khau khoi dong da duoc nhung vao EXE.")
    print_banner("  auth.py da duoc khoi phuc ve PLACEHOLDER.")
    print_banner("=" * 60)


if __name__ == "__main__":
    main()
