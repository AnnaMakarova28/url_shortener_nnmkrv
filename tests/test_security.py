from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    password = "12345678"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token({"sub": "user@test.com"})
    payload = decode_access_token(token)

    assert payload["sub"] == "user@test.com"
    assert "exp" in payload
