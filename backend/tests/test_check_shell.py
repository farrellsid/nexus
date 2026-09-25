"""The shell build check refuses what the shell must not ship. Pinned with synthetic file lists."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_shell.py"


@pytest.fixture(scope="module")
def shell_check():
    spec = importlib.util.spec_from_file_location("check_shell", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bundled_data_and_media_are_named(shell_check):
    files = [
        "index.html",
        "assets/index-abc.js",
        "cesium/Workers/x.js",
        "datacenters.geojsonl",
        "models/aircraft.glb",
        "events/clip.mp4",
        "local_data/regions.json",
    ]
    assert shell_check.dataset_files(files) == [
        "datacenters.geojsonl",
        "events/clip.mp4",
        "local_data/regions.json",
        "models/aircraft.glb",
    ]


def test_a_build_without_data_has_none_to_name(shell_check):
    assert shell_check.dataset_files(["index.html", "assets/a.js", "fonts/x.woff2"]) == []


def test_hard_coded_hosts_ignore_namespace_urls_only(shell_check):
    texts = {
        "index.html": '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        '<link href="https://fonts.googleapis.com/css2">',
        "assets/a.css": "body { background: url(//cdn.example.org/x.png); }",
        "assets/b.css": "a { color: red }",
    }
    assert shell_check.hard_coded_hosts(texts) == {
        "index.html": {"fonts.googleapis.com"},
        "assets/a.css": {"cdn.example.org"},
    }


def test_only_hosts_off_the_allowed_list_are_reported(shell_check):
    allowed = ["127.0.0.1:5175", "services.arcgisonline.com"]
    assert shell_check.disallowed_hosts(["127.0.0.1:5175", "services.arcgisonline.com"], allowed) == []
    assert shell_check.disallowed_hosts(["127.0.0.1:5175", "tracker.example"], allowed) == ["tracker.example"]
