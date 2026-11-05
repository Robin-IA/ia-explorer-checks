"""check_setup.py: the Python version gate and the fix it gives."""

import pathlib
import sys
from collections import namedtuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import check_setup  # noqa: E402

V = namedtuple("V", "major minor micro releaselevel serial")


def run_gate(monkeypatch, version, exe="/opt/homebrew/bin/python3", mac=True):
    monkeypatch.setattr(check_setup, "rows", [])
    monkeypatch.setattr(check_setup, "MAC", mac)
    monkeypatch.setattr(sys, "version_info", V(*version, "final", 0))
    monkeypatch.setattr(sys, "executable", exe)
    ok = check_setup.check_python()
    return ok, check_setup.rows[0]


def test_apple_stub_is_refused_before_its_version_is_considered(monkeypatch):
    monkeypatch.setattr(sys, "prefix", sys.base_prefix)
    ok, (status, what, detail, fix) = run_gate(
        monkeypatch, (3, 9, 6), exe="/usr/bin/python3")
    assert not ok and status == "MISSING"
    assert what == "a real Python" and "Apple" in detail
    assert "brew install python" in fix


def test_too_old_homebrew_python_is_refused(monkeypatch):
    ok, (status, _, detail, fix) = run_gate(monkeypatch, (3, 9, 18))
    assert not ok and status == "MISSING"
    assert "3.9.18" in detail and "brew upgrade python" in fix


def test_old_but_supported_python_passes_with_a_note(monkeypatch):
    ok, (status, _, detail, _) = run_gate(monkeypatch, (3, 11, 9))
    assert ok and status == "OK"
    assert "3.12 or newer is recommended" in detail


def test_current_python_passes_quietly(monkeypatch):
    ok, (status, _, detail, fix) = run_gate(monkeypatch, (3, 13, 1))
    assert ok and status == "OK" and not fix
    assert "recommended" not in detail
