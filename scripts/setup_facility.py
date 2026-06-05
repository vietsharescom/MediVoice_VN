"""
MediVoice VN — Facility config wizard.
Chạy một lần khi cài lần đầu: python scripts/setup_facility.py
Ghi vào config/facility_config.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "facility_config.json"

PROVINCE_CODES = {
    "01": "Hà Nội",
    "48": "Đà Nẵng",
    "79": "TP. Hồ Chí Minh",
    "31": "Hải Phòng",
    "46": "Thừa Thiên Huế",
    "49": "Quảng Nam",
    "52": "Bình Định",
    "54": "Phú Yên",
    "82": "Tiền Giang",
    "91": "Kiên Giang",
}


def _prompt(label: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"  {label}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nHủy.")
        sys.exit(0)
    return val if val else default


def _load_existing() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def run_wizard() -> None:
    print("=" * 55)
    print("  MediVoice VN — Cài đặt thông tin phòng khám")
    print("=" * 55)
    print("  Nhấn Enter để giữ giá trị hiện tại.\n")

    existing = _load_existing()

    ten = _prompt("Tên phòng khám", existing.get("ten_co_so", "Phòng khám tư"))
    dia_chi = _prompt("Địa chỉ", existing.get("dia_chi", ""))
    sdt = _prompt("Số điện thoại", existing.get("so_dien_thoai", ""))

    print(f"\n  Mã tỉnh/thành phổ biến:")
    for code, name in PROVINCE_CODES.items():
        print(f"    {code} = {name}")
    province = _prompt("Mã tỉnh/thành", existing.get("province_code", "48"))

    so_yte = existing.get("so_y_te", "")
    if province in PROVINCE_CODES:
        so_yte = f"Sở Y tế {PROVINCE_CODES[province]}"
    so_yte = _prompt("Sở Y tế", so_yte)

    gphn = _prompt("Số GPHN/đăng ký cơ sở (BYT)", existing.get("byt_registration_number", ""))

    print("\n  Thông tin bác sĩ:")
    bs_ten = _prompt("Họ tên bác sĩ", existing.get("doctor_ho_ten", ""))
    bs_cchn = _prompt("Số CCHN bác sĩ", existing.get("doctor_cchn", ""))

    port = _prompt("Cổng ứng dụng", str(existing.get("app_port", 8000)))
    try:
        port_int = int(port)
    except ValueError:
        port_int = 8000

    import uuid
    fac_id = existing.get("facility_id") or f"FAC-{str(uuid.uuid4())[:8].upper()}"

    config = {
        "_comment": "MediVoice VN — Cấu hình cơ sở y tế. Chạy scripts/setup_facility.py để cập nhật.",
        "facility_id": fac_id,
        "ten_co_so": ten,
        "byt_registration_number": gphn,
        "province_code": province,
        "dia_chi": dia_chi,
        "so_dien_thoai": sdt,
        "so_y_te": so_yte,
        "doctor_ho_ten": bs_ten,
        "doctor_cchn": bs_cchn,
        "app_host": existing.get("app_host", "127.0.0.1"),
        "app_port": port_int,
        "db_path": existing.get("db_path", "medivoice.db"),
        "log_level": existing.get("log_level", "INFO"),
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n  ✅ Đã lưu config/facility_config.json")
    print(f"  Phòng khám: {ten}")
    print(f"  Tỉnh: {PROVINCE_CODES.get(province, province)}")
    print(f"  Port: {port_int}")
    print("\n  Chạy install.bat để hoàn thành cài đặt.")


if __name__ == "__main__":
    run_wizard()
