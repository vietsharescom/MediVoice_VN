"""
Tests for scripts/check_env.py
@verifies DEPLOY-001 (CT-005)
"""
from __future__ import annotations
import sys
import json
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add scripts/ to path so we can import check_env
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import check_env


class TestCheckPython:
    def test_current_python_passes(self):
        assert check_env.check_python() is True

    def test_old_python_fails(self):
        # Raise MIN_PYTHON requirement above any real interpreter version
        orig = check_env.MIN_PYTHON
        check_env.MIN_PYTHON = (3, 99)
        try:
            assert check_env.check_python() is False
        finally:
            check_env.MIN_PYTHON = orig


class TestCheckDisk:
    def test_sufficient_disk_passes(self):
        # shutil.disk_usage returns a namedtuple (total, used, free) — patch as tuple
        with patch("check_env.shutil.disk_usage", return_value=(20 * 1024**3, 10 * 1024**3, 10 * 1024**3)):
            assert check_env.check_disk() is True

    def test_low_disk_fails(self):
        with patch("check_env.shutil.disk_usage", return_value=(5 * 1024**3, 4 * 1024**3, 1 * 1024**3)):
            assert check_env.check_disk() is False


class TestCheckPackages:
    def test_all_present_passes(self):
        with patch("importlib.import_module", return_value=MagicMock()):
            assert check_env.check_packages() is True

    def test_missing_package_fails(self):
        def fake_import(name):
            if name == "torch":
                raise ImportError("No module named 'torch'")
            return MagicMock()

        with patch("importlib.import_module", side_effect=fake_import):
            assert check_env.check_packages() is False


class TestCheckReferenceData:
    def test_existing_data_passes(self, tmp_path):
        ref = tmp_path / "reference"
        ref.mkdir()
        (ref / "icd10vn.json").write_text("{}", encoding="utf-8")
        (ref / "drug_db.json").write_text("{}", encoding="utf-8")
        orig = check_env.REQUIRED_DATA
        check_env.REQUIRED_DATA = [ref / "icd10vn.json", ref / "drug_db.json"]
        try:
            assert check_env.check_reference_data() is True
        finally:
            check_env.REQUIRED_DATA = orig

    def test_missing_data_fails(self, tmp_path):
        orig = check_env.REQUIRED_DATA
        check_env.REQUIRED_DATA = [tmp_path / "nonexistent.json"]
        try:
            assert check_env.check_reference_data() is False
        finally:
            check_env.REQUIRED_DATA = orig


class TestCheckPort:
    def test_free_port_passes(self):
        # Find a guaranteed-free port
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]
        assert check_env.check_port(free_port) is True

    def test_occupied_port_fails(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            used_port = s.getsockname()[1]
            assert check_env.check_port(used_port) is False


class TestCheckFacilityConfig:
    def test_valid_config_passes(self, tmp_path):
        cfg_file = tmp_path / "facility_config.json"
        cfg_file.write_text(
            json.dumps({"ten_co_so": "Test PK", "province_code": "48"}),
            encoding="utf-8",
        )
        orig = check_env.CONFIG_PATH
        check_env.CONFIG_PATH = cfg_file
        try:
            assert check_env.check_facility_config() is True
        finally:
            check_env.CONFIG_PATH = orig

    def test_missing_config_returns_true_warn_only(self, tmp_path):
        orig = check_env.CONFIG_PATH
        check_env.CONFIG_PATH = tmp_path / "nonexistent.json"
        try:
            assert check_env.check_facility_config() is True  # warning only
        finally:
            check_env.CONFIG_PATH = orig

    def test_malformed_config_fails(self, tmp_path):
        cfg_file = tmp_path / "facility_config.json"
        cfg_file.write_text("not valid json", encoding="utf-8")
        orig = check_env.CONFIG_PATH
        check_env.CONFIG_PATH = cfg_file
        try:
            assert check_env.check_facility_config() is False
        finally:
            check_env.CONFIG_PATH = orig


class TestRunAll:
    def test_all_pass_returns_true(self):
        with (
            patch.object(check_env, "check_python", return_value=True),
            patch.object(check_env, "check_disk", return_value=True),
            patch.object(check_env, "check_packages", return_value=True),
            patch.object(check_env, "check_reference_data", return_value=True),
            patch.object(check_env, "check_model", return_value=True),
            patch.object(check_env, "check_facility_config", return_value=True),
            patch.object(check_env, "check_port", return_value=True),
        ):
            assert check_env.run_all(port=8000) is True

    def test_one_fail_returns_false(self):
        with (
            patch.object(check_env, "check_python", return_value=True),
            patch.object(check_env, "check_disk", return_value=False),
            patch.object(check_env, "check_packages", return_value=True),
            patch.object(check_env, "check_reference_data", return_value=True),
            patch.object(check_env, "check_model", return_value=True),
            patch.object(check_env, "check_facility_config", return_value=True),
            patch.object(check_env, "check_port", return_value=True),
        ):
            assert check_env.run_all(port=8000) is False
