"""Existing sources first; no new events or sounds unless the fallback is enabled."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
import sfx
import openverse_assets as ov


def test_audio_off_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("BOURIKO_OPENVERSE_AUDIO", raising=False)
    monkeypatch.setattr(sfx, "SFX_DIR", tmp_path)
    with patch.object(sfx, "fetch", return_value=False), patch.object(ov, "first") as get:
        assert not sfx.download_assets()
        get.assert_not_called()


def test_audio_fallback_keeps_rights(tmp_path, monkeypatch):
    monkeypatch.setenv("BOURIKO_OPENVERSE_AUDIO", "1")
    monkeypatch.setattr(sfx, "SFX_DIR", tmp_path)
    with patch.object(sfx, "fetch", return_value=False), \
            patch.object(ov, "first", return_value=(tmp_path / "cache", {"attribution": "CC0 credit"})), \
            patch("subprocess.run"):
        sources = sfx.download_assets()
    assert len(sources) == len(sfx.NIGHT_FILES_SFX)
    assert list(tmp_path.glob("*.license.json"))


def test_working_provider_not_replaced(tmp_path, monkeypatch):
    monkeypatch.setenv("BOURIKO_OPENVERSE_AUDIO", "1")
    monkeypatch.setattr(sfx, "SFX_DIR", tmp_path)
    with patch.object(sfx, "fetch", return_value=True), patch.object(ov, "first") as get:
        assert sfx.download_assets()
        get.assert_not_called()
