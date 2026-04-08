"""
src/utils/auth.py
=================
FILE NÀY ĐƯỢC TỰ ĐỘNG SINH BỞI scripts/build_release.py
KHÔNG CHỈNH SỬA TAY – MỌI THAY ĐỔI SẼ BỊ OVERRIDE KHI BUILD LẠI.

Chứa password hash được nhúng tại thời điểm build.
Sau khi PyArmor obfuscate + Nuitka compile, hash này nằm trong
native machine code và không thể đọc trực tiếp.
"""

import hashlib as _hashlib

# ── AUTO-GENERATED SECTION START ──────────────────────────────────────────
# PLACEHOLDER – sẽ được thay bằng giá trị thực khi chạy build_release.py
_APP_PASSWORD_HASH = "PLACEHOLDER_HASH"
_APP_PASSWORD_SALT = "PLACEHOLDER_SALT"
# ── AUTO-GENERATED SECTION END ────────────────────────────────────────────


def verify_password(password: str) -> bool:
    """
    So sánh password người dùng nhập với hash được nhúng lúc build.

    Dùng PBKDF2-HMAC-SHA256 với 200_000 iterations để chống brute-force.
    Salt được nhúng cứng (per-build), không lưu file ngoài.
    """
    if _APP_PASSWORD_HASH == "PLACEHOLDER_HASH":
        # Chế độ development: chưa build release → bỏ qua xác thực
        return True

    try:
        salt_bytes = bytes.fromhex(_APP_PASSWORD_SALT)
        attempt = _hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_bytes,
            200_000
        ).hex()
        return attempt == _APP_PASSWORD_HASH
    except Exception:
        return False
