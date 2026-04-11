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
import sys

# ── AUTO-GENERATED SECTION START ──────────────────────────────────────────
# PLACEHOLDER – sẽ được thay bằng giá trị thực khi chạy build_release.py
_APP_PASSWORD_HASH = "PLACEHOLDER_HASH"
_APP_PASSWORD_SALT = "PLACEHOLDER_SALT"
_ALLOWED_MAC_ADDRESS = "PLACEHOLDER_MAC"
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

def verify_mac_address() -> bool:
    """
    Kiểm tra máy hiện hành có MAC Address khớp với cấu hình lúc Build không.
    Nếu cấu hình là None/PLACEHOLDER, trả về True.
    """
    if _ALLOWED_MAC_ADDRESS == "PLACEHOLDER_MAC":
        return True
        
    import subprocess
    import re
    import uuid
    try:
        # Cách 1: Sử dụng Getmac trên windows để tìm tất cả các card mạng
        output = subprocess.check_output("getmac", text=True)
        valid_macs = [m.replace('-', ':').upper() for m in re.findall(r'([0-9A-Fa-f]{2}(?:-[0-9A-Fa-f]{2}){5})', output)]
    except Exception:
        # Cách 2: Sử dụng thư viện uuid fallback
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        valid_macs = [":".join([mac[e:e+2] for e in range(0, 11, 2)]).upper()]

    # Chuẩn hóa MAC cung cấp để so sánh
    target_mac = _ALLOWED_MAC_ADDRESS.replace('-', ':').upper()
    if len(target_mac) == 12 and ":" not in target_mac:
        target_mac = ":".join([target_mac[e:e+2] for e in range(0, 11, 2)])
        
    return target_mac in valid_macs
