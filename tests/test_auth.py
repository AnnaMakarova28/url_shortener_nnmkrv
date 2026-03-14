def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@test.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "test@test.com"


def test_login_user(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@test.com",
            "password": "12345678",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "test@test.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data


def test_register_duplicate_user(client):
    payload = {
        "email": "dup@test.com",
        "password": "12345678",
    }

    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "test2@test.com", "password": "12345678"},
    )

    response = client.post(
        "/auth/login",
        data={"username": "test2@test.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
