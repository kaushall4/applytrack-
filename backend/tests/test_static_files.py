"""The SPA file handler must never serve files outside the built frontend."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from applytrack.api.app import _static_file, create_app


@pytest.fixture
def site(tmp_path, monkeypatch):
    dist = tmp_path / "site" / "dist"
    (dist / "icons").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (dist / "icons" / "a.png").write_bytes(b"png")
    (tmp_path / "site" / "secret.env").write_text("DATABASE_URL=secret", encoding="utf-8")
    (tmp_path / "token.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("APPLYTRACK_STATIC_DIR", str(dist))
    return dist


@pytest.mark.parametrize("path", [
    "../secret.env", "..\\secret.env", "../../token.json", "icons/../../secret.env",
    "/etc/passwd", "C:/Windows/win.ini", "", ".", "icons",
])
def test_paths_outside_the_site_are_refused(site, path):
    assert _static_file(site, path) is None


def test_real_files_are_served(site):
    assert _static_file(site, "icons/a.png") == (site / "icons" / "a.png").resolve()
    assert _static_file(site, "index.html") is not None


@pytest.mark.parametrize("url", [
    "/..%2fsecret.env", "/..%2f..%2ftoken.json", "/%2e%2e/secret.env",
    "/..%5csecret.env", "/icons/..%2f..%2fsecret.env",
])
def test_traversal_urls_get_the_app_not_the_file(site, url):
    client = TestClient(create_app(), client=("127.0.0.1", 5))
    resp = client.get(url)
    assert "secret" not in resp.text and resp.text != "{}"
    assert resp.status_code in (200, 404)


def test_icon_url_still_works(site):
    client = TestClient(create_app(), client=("127.0.0.1", 5))
    assert client.get("/icons/a.png").content == b"png"
    assert "app" in client.get("/review").text  # SPA route falls back to index
