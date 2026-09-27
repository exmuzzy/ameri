import time

from ameri import session
from ameri.auth import User, hash_password


USERS = {"anna": User("anna", "Анна", "manager", hash_password("pw123456"))}


def users():
    return USERS


def test_roundtrip_and_tamper(tmp_path):
    secret = session.session_secret(tmp_path)
    assert (tmp_path / "secrets" / "session_secret").stat().st_mode & 0o777 == 0o600
    token = session.issue(secret, users()["anna"])
    assert session.read(secret, token, users()).login == "anna"
    payload, signature = token.split(".")
    assert session.read(secret, payload + "." + signature[:-2] + "xx", users()) is None
    assert session.read(b"other", token, users()) is None
    assert session.read(secret, None, users()) is None
    assert session.read(secret, "garbage", users()) is None


def test_expiry_and_password_change(tmp_path):
    secret = session.session_secret(tmp_path)
    anna = users()["anna"]
    old = session.issue(secret, anna, now=time.time() - session.SESSION_TTL - 10)
    assert session.read(secret, old, users()) is None
    token = session.issue(secret, anna)
    changed = {"anna": User("anna", "Анна", "manager", hash_password("new-pass-1"))}
    assert session.read(secret, token, changed) is None
    assert session.read(secret, token, {}) is None


def test_api_token_is_not_a_site_session(tmp_path):
    from ameri.api import issue_token

    secret = session.session_secret(tmp_path)
    api_token, _ = issue_token(secret, users()["anna"])
    assert session.read(secret, api_token, users()) is None


def test_cookie_script():
    assert "ameri_session=abc" in session.cookie_script("abc")
    assert "Max-Age=0" in session.cookie_script(None)
