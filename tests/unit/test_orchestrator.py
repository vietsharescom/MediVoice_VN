# tests/unit/test_orchestrator.py
# Tests for detect_confusion / create_consultation_request / close_session [FID-VN-020, CT-011]

from unittest.mock import MagicMock, patch

from scripts.orchestrator import (
    _patch_backlog,
    _patch_changelog,
    _patch_claude_md,
    _patch_project_progress,
    close_session,
    create_consultation_request,
    detect_confusion,
)


class TestDetectConfusion:
    def test_detect_confusion_trigger_keywords(self):
        result = detect_confusion("Có 2 option cho kiến trúc này, chưa rõ option nào đúng cho VN")
        assert result["should_consult"] is True
        assert "T1" in result["matched_triggers"]

    def test_detect_confusion_t5_low_confidence(self):
        result = detect_confusion("Tôi không chắc về quyết định này, confidence < 70%")
        assert result["should_consult"] is True
        assert "T5" in result["matched_triggers"]

    def test_detect_confusion_no_trigger(self):
        result = detect_confusion("Đã viết xong 3 unit tests cho hàm parse_date, tất cả PASS")
        assert result["should_consult"] is False
        assert result["matched_triggers"] == []


class TestCreateConsultationRequest:
    def test_create_consultation_request_format_and_numbering(self, tmp_path, monkeypatch):
        import scripts.orchestrator as orch

        monkeypatch.setattr(orch, "ROOT", tmp_path)

        options = [
            {
                "name": "Option A",
                "description": "Mô tả A",
                "pros": ["pro1"],
                "cons": ["con1"],
                "risks": "low",
                "effort": "Low",
                "timeline": "1 day",
            },
        ]
        analysis = {
            "lean": "A", "confidence": 80,
            "main_reason": "Đơn giản hơn", "main_uncertainty": "Chưa rõ scale",
        }

        path1 = create_consultation_request(
            "Topic 1", "Question 1?", options, ["constraint 1"], analysis,
        )
        path2 = create_consultation_request(
            "Topic 2", "Question 2?", options, ["constraint 1"], analysis,
        )

        assert path1.name.endswith("-001.md")
        assert path2.name.endswith("-002.md")
        assert path1.parent == tmp_path / "docs" / "records" / "consultations"

        content = path1.read_text(encoding="utf-8")
        assert "CONSULTATION REQUEST [CONS-" in content
        assert "## QUESTION" in content
        assert "Question 1?" in content
        assert "### Option A: Option A" in content
        assert "## HARD CONSTRAINTS" in content
        assert "constraint 1" in content
        assert "## CLAUDE'S CURRENT ANALYSIS" in content
        assert "Lean toward: Option A" in content


class TestPatchHelpers:
    def test_patch_backlog_replaces_existing_heading(self, tmp_path):
        backlog_dir = tmp_path / "docs" / "records"
        backlog_dir.mkdir(parents=True)
        backlog = backlog_dir / "BACKLOG.md"
        backlog.write_text(
            "# BACKLOG.md — MediVoice VN\n"
            "# v0.9.4\n"
            "# Single source of truth\n"
            "\n"
            "## CT-100 — Old description [DOING]\n"
            "- [ ] something\n",
            encoding="utf-8",
        )

        _patch_backlog(tmp_path, [("CT-100", "DONE", "New description")])

        text = backlog.read_text(encoding="utf-8")
        assert "## CT-100 — New description [DONE]" in text
        assert "[DOING]" not in text

    def test_patch_backlog_inserts_new_heading(self, tmp_path):
        backlog_dir = tmp_path / "docs" / "records"
        backlog_dir.mkdir(parents=True)
        backlog = backlog_dir / "BACKLOG.md"
        backlog.write_text(
            "# BACKLOG.md — MediVoice VN\n"
            "# v0.9.4\n"
            "# Single source of truth\n"
            "\n"
            "## CT-100 — Old [DOING]\n",
            encoding="utf-8",
        )

        _patch_backlog(tmp_path, [("CT-200", "NEW", "Brand new task")])

        text = backlog.read_text(encoding="utf-8")
        assert "## CT-200 — Brand new task [NEW]" in text

    def test_patch_project_progress_appends_row(self, tmp_path):
        progress_dir = tmp_path / "docs" / "records"
        progress_dir.mkdir(parents=True)
        progress = progress_dir / "PROJECT_PROGRESS.md"
        progress.write_text(
            "## LỊCH SỬ PHIÊN\n"
            "\n"
            "| Phiên | Ngày | Version | Highlights |\n"
            "|---|---|---|---|\n"
            "| SES-20260601 | 2026-06-01 | v0.1 | First session |\n"
            "\n"
            "---\n",
            encoding="utf-8",
        )

        _patch_project_progress(tmp_path, "| SES-20260613 | 2026-06-13 | v0.2 | New session |")

        lines = progress.read_text(encoding="utf-8").splitlines()
        assert lines[5] == "| SES-20260613 | 2026-06-13 | v0.2 | New session |"
        assert lines[4] == "| SES-20260601 | 2026-06-01 | v0.1 | First session |"

    def test_patch_changelog_inserts_before_first_entry(self, tmp_path):
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# CHANGELOG — MediVoice VN\n"
            "# ISO/IEC 42001:2023 Clause 10.2\n"
            "\n"
            "## [v0.1.0] — 2026-06-01 — first entry\n"
            "\n"
            "### Added\n"
            "- thing\n",
            encoding="utf-8",
        )

        _patch_changelog(tmp_path, "## [v0.2.0] — 2026-06-13 — new entry\n\n### Added\n- new thing")

        lines = changelog.read_text(encoding="utf-8").splitlines()
        assert lines[3] == "## [v0.2.0] — 2026-06-13 — new entry"
        assert "## [v0.1.0] — 2026-06-01 — first entry" in lines

    def test_patch_claude_md_updates_current_state(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# CLAUDE.md\n"
            "\n"
            "## CURRENT STATE\n"
            "\n"
            "| Field | Value |\n"
            "|---|---|\n"
            "| Version | v0.1.0 |\n"
            "| Status | old status |\n"
            "\n"
            "## NEXT SECTION\n"
            "| Field | Value |\n"
            "| Version | should not change |\n",
            encoding="utf-8",
        )

        _patch_claude_md(tmp_path, {"Version": "v0.2.0", "Status": "new status"})

        text = claude_md.read_text(encoding="utf-8")
        assert "| Version | v0.2.0 |" in text
        assert "| Status | new status |" in text
        assert "| Version | should not change |" in text


class TestCloseSessionPushDefault:
    def test_close_session_push_false_by_default(self):
        with patch("scripts.orchestrator.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = close_session({}, commit_message="test commit")

        assert result["pushed"] is False
        for call in mock_run.call_args_list:
            args = call.args[0]
            assert "push" not in args

    def test_close_session_push_true_calls_git_push(self):
        with patch("scripts.orchestrator.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = close_session({}, commit_message="test commit", push=True)

        assert result["pushed"] is True
        pushed = any("push" in call.args[0] for call in mock_run.call_args_list)
        assert pushed
