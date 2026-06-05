"""
MediVoice VN — Pre-flight environment checker.
Chạy trước khi start app: python scripts/check_env.py
Exit 0 = OK, Exit 1 = có lỗi cần fix.
"""
from __future__ import annotations
import sys
import json
import shutil
import socket
import importlib
from pathlib import Path

# Fix Windows console encoding (cp1252 → utf-8) để hiển thị emoji
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "facility_config.json"
MODEL_CACHE = Path.home() / ".cache" / "huggingface" / "hub"

MIN_PYTHON = (3, 10)
MIN_DISK_GB = 5.0
REQUIRED_PACKAGES = [
    "fastapi", "uvicorn", "transformers", "torch",
    "soundfile", "librosa", "cryptography", "reportlab", "pydantic",
]
REQUIRED_DATA = [
    ROOT / "data" / "reference" / "icd10vn.json",
    ROOT / "data" / "reference" / "drug_db.json",
]

PASS = "  ✅"
FAIL = "  ❌"
WARN = "  ⚠️ "


def check_python() -> bool:
    ok = sys.version_info >= MIN_PYTHON
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    status = PASS if ok else FAIL
    req = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}+"
    print(f"{status} Python {ver} (cần {req})")
    return ok


def check_packages() -> bool:
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"{FAIL} Packages thiếu: {', '.join(missing)}")
        print(f"       Chạy: pip install -r requirements-prod.txt")
        return False
    print(f"{PASS} Tất cả packages đã cài ({len(REQUIRED_PACKAGES)} packages)")
    return True


def check_disk() -> bool:
    total, used, free = shutil.disk_usage(ROOT)
    free_gb = free / (1024 ** 3)
    ok = free_gb >= MIN_DISK_GB
    status = PASS if ok else FAIL
    print(f"{status} Disk trống: {free_gb:.1f} GB (cần {MIN_DISK_GB:.0f} GB+)")
    return ok


def check_model() -> bool:
    # PhoWhisper-medium cached by HuggingFace transformers
    model_dirs = list(MODEL_CACHE.glob("models--vinai--PhoWhisper-medium")) if MODEL_CACHE.exists() else []
    if model_dirs:
        print(f"{PASS} PhoWhisper-medium model: đã cache tại {MODEL_CACHE}")
        return True
    print(f"{WARN} PhoWhisper-medium model: chưa download")
    print(f"       Sẽ tự download lần đầu chạy (~3GB). Cần Internet + ~10 phút.")
    return True  # Warning chỉ, không fail — model tự download khi chạy


def check_reference_data() -> bool:
    missing = [p for p in REQUIRED_DATA if not p.exists()]
    if missing:
        names = [p.name for p in missing]
        print(f"{FAIL} Reference data thiếu: {', '.join(names)}")
        return False
    print(f"{PASS} Reference data: icd10vn.json + drug_db.json")
    return True


def check_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        in_use = s.connect_ex(("127.0.0.1", port)) == 0
    if in_use:
        print(f"{FAIL} Port {port} đang bị chiếm — tắt app khác trước khi chạy")
        return False
    print(f"{PASS} Port {port}: trống, sẵn sàng")
    return True


def check_facility_config() -> bool:
    if not CONFIG_PATH.exists():
        print(f"{WARN} facility_config.json chưa có")
        print(f"       Chạy: python scripts/setup_facility.py")
        return True  # Warning only — app chạy được với defaults
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        missing_fields = [f for f in ("ten_co_so", "province_code") if not cfg.get(f)]
        if missing_fields:
            print(f"{WARN} facility_config.json thiếu: {missing_fields}")
            print(f"       Chạy: python scripts/setup_facility.py")
        else:
            name = cfg.get("ten_co_so", "")
            print(f"{PASS} Facility config: {name}")
        return True
    except Exception as e:
        print(f"{FAIL} facility_config.json lỗi: {e}")
        return False


def run_all(port: int = 8000) -> bool:
    print("=" * 50)
    print("  MediVoice VN — Pre-flight Check")
    print("=" * 50)
    results = [
        check_python(),
        check_disk(),
        check_packages(),
        check_reference_data(),
        check_model(),
        check_facility_config(),
        check_port(port),
    ]
    print("=" * 50)
    failed = results.count(False)
    if failed == 0:
        print("  ✅ Sẵn sàng khởi động MediVoice VN!")
    else:
        print(f"  ❌ {failed} lỗi cần sửa trước khi chạy app.")
    print("=" * 50)
    return failed == 0


if __name__ == "__main__":
    cfg_port = 8000
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg_port = int(cfg.get("app_port", 8000))
        except Exception:
            pass
    ok = run_all(port=cfg_port)
    sys.exit(0 if ok else 1)
