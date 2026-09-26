from ameri.auth import authenticate, hash_password, load_users, verify_password


def test_hash_roundtrip():
    stored = hash_password("секрет")
    assert verify_password("секрет", stored)
    assert not verify_password("не то", stored)
    assert not verify_password("секрет", "garbage")


def test_load_and_authenticate(tmp_path):
    users_file = tmp_path / "users.toml"
    users_file.write_text(
        f'[users.anna]\nname = "Анна"\nrole = "manager"\npassword_hash = "{hash_password("pw")}"\n',
        encoding="utf-8",
    )
    users = load_users(users_file)
    assert users["anna"].name == "Анна"
    assert authenticate(users, "anna", "pw").login == "anna"
    assert authenticate(users, "anna", "bad") is None
    assert authenticate(users, "nobody", "pw") is None


def test_missing_users_file(tmp_path):
    assert load_users(tmp_path / "none.toml") == {}


def test_save_users_roundtrip(tmp_path):
    from ameri.auth import User, save_users

    path = tmp_path / "users.toml"
    users = {"o'brien": User("o'brien", 'Имя "в кавычках"', "admin", hash_password("pw"))}
    save_users(path, users)
    loaded = load_users(path)
    assert loaded["o'brien"].name == 'Имя "в кавычках"'
    assert authenticate(loaded, "o'brien", "pw")
    assert oct(path.stat().st_mode)[-3:] == "600"
