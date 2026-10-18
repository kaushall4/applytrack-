"""Phone access: pairing-key guard and the PC-only pairing endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from applytrack import mobile
from applytrack.api.app import create_app

LOCAL = ("127.0.0.1", 50000)
PHONE = ("192.168.1.42", 50000)


def test_local_client_detection():
    assert mobile.is_local_client("127.0.0.1")
    assert mobile.is_local_client("::1")
    assert not mobile.is_local_client("192.168.1.42")
    assert not mobile.is_local_client("testclient")
    assert not mobile.is_local_client(None)


def test_pc_needs_no_key():
    resp = TestClient(create_app(), client=LOCAL).get("/api/applications")
    assert resp.status_code == 200


def test_phone_without_key_is_rejected():
    resp = TestClient(create_app(), client=PHONE).get("/api/applications")
    assert resp.status_code == 401
    assert resp.json()["code"] == "pairing_required"


def test_phone_with_wrong_key_is_rejected():
    client = TestClient(create_app(), client=PHONE)
    resp = client.get("/api/applications", headers={mobile.KEY_HEADER: "nope"})
    assert resp.status_code == 401


def test_phone_with_key_is_allowed():
    client = TestClient(create_app(), client=PHONE)
    key = mobile.get_or_create_key()
    resp = client.get("/api/applications", headers={mobile.KEY_HEADER: key})
    assert resp.status_code == 200


def test_health_is_open_for_the_phone():
    assert TestClient(create_app(), client=PHONE).get("/api/health").status_code == 200


def test_pairing_and_account_actions_stay_on_the_pc():
    client = TestClient(create_app(), client=PHONE)
    headers = {mobile.KEY_HEADER: mobile.get_or_create_key()}
    assert client.get("/api/mobile", headers=headers).status_code == 403
    resp = client.post("/api/account/disconnect", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == "pc_only"


def test_mobile_status_disabled_by_default():
    data = TestClient(create_app(), client=LOCAL).get("/api/mobile").json()
    assert data["enabled"] is False and data["restart_required"] is False
    assert data["url"] is None and data["pair_code"] is None


def test_key_is_stable():
    assert mobile.get_or_create_key() == mobile.get_or_create_key()


def test_enable_in_env_adds_and_replaces(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("IGNORED_SENDERS=example.com\nMOBILE_ACCESS=false\n", encoding="utf-8")
    monkeypatch.setenv("MOBILE_ACCESS", "false")
    mobile.enable_in_env(str(env))
    text = env.read_text(encoding="utf-8")
    assert "MOBILE_ACCESS=true" in text and "MOBILE_ACCESS=false" not in text
    assert "IGNORED_SENDERS=example.com" in text

    fresh = tmp_path / "new.env"
    mobile.enable_in_env(str(fresh))
    assert "MOBILE_ACCESS=true" in fresh.read_text(encoding="utf-8")


def test_qr_svg_renders():
    svg = mobile.qr_svg("http://192.168.1.10:8765/?key=abc")
    assert svg.lstrip().startswith("<svg")
    # Must scale to its container rather than be cropped.
    assert "viewBox" in svg and 'width="' not in svg.split(">", 1)[0]


def _reset_code():
    mobile._pair_code = None


def test_pair_code_trades_for_key(monkeypatch):
    monkeypatch.setattr("applytrack.api.routes.mobile.get_settings",
                        lambda: type("S", (), {"mobile_access": True})())
    _reset_code()
    code, ttl = mobile.current_pair_code()
    assert len(code) == 6 and code.isdigit() and ttl > 0
    phone = TestClient(create_app(), client=PHONE)
    resp = phone.post("/api/pair", json={"code": code})
    assert resp.status_code == 200
    assert resp.json()["key"] == mobile.get_or_create_key()
    # Single use.
    assert phone.post("/api/pair", json={"code": code}).status_code == 400


def test_pair_code_dies_after_wrong_guesses(monkeypatch):
    monkeypatch.setattr("applytrack.api.routes.mobile.get_settings",
                        lambda: type("S", (), {"mobile_access": True})())
    _reset_code()
    code, _ = mobile.current_pair_code()
    wrong = f"{(int(code) + 1) % 10**6:06d}"
    phone = TestClient(create_app(), client=PHONE)
    for _ in range(mobile.PAIR_CODE_MAX_FAILURES):
        assert phone.post("/api/pair", json={"code": wrong}).status_code == 400
    assert phone.post("/api/pair", json={"code": code}).status_code == 400


def test_pairing_off_when_phone_access_disabled():
    _reset_code()
    code, _ = mobile.current_pair_code()
    resp = TestClient(create_app(), client=PHONE).post("/api/pair", json={"code": code})
    assert resp.status_code == 404
