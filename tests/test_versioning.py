from __future__ import annotations

import tomllib
from pathlib import Path

from app.cli import _build_parser
from app.version import __version__


def test_cli_reports_version(capsys) -> None:
    parser = _build_parser()
    try:
        parser.parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out.strip()
    assert out.endswith(__version__)


def test_pyproject_version_matches_app_version() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["version"] == __version__
