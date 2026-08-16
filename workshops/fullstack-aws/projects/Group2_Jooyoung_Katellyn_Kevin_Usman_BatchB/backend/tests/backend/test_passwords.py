from backend.auth.passwords import hash_password, verify_password


def test_hash_password_is_not_plaintext():
    hashed = hash_password("password")
    assert hashed != "password"
    assert hashed.startswith("$2")


def test_same_password_hashes_differ_but_both_verify():
    first = hash_password("password")
    second = hash_password("password")
    assert first != second
    assert verify_password("password", first)
    assert verify_password("password", second)


def test_verify_password_correct():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("secret")
    assert verify_password("nope", hashed) is False


def test_verify_password_invalid_hash_returns_false():
    assert verify_password("secret", "not-a-bcrypt-hash") is False
