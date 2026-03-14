def test_create_short_link(client):
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://google.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "short_code" in data


def test_link_stats(client):
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
    )

    short_code = response.json()["short_code"]

    stats = client.get(f"/links/{short_code}/stats")

    assert stats.status_code == 200
    assert stats.json()["clicks"] == 0


def test_create_short_link_with_custom_alias(client):
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "custom_alias": "myalias",
            "expires_at": None,
            "project_name": "proj1",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "myalias"
    assert data["project_name"] == "proj1"


def test_create_short_link_duplicate_alias(client):
    payload = {
        "original_url": "https://example.com",
        "custom_alias": "samealias",
        "expires_at": None,
        "project_name": None,
    }

    client.post("/links/shorten", json=payload)
    response = client.post("/links/shorten", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Custom alias already exists"


def test_search_link_by_original_url(client):
    client.post(
        "/links/shorten",
        json={"original_url": "https://search.com", "project_name": None},
    )

    response = client.get(
        "/links/search", params={"original_url": "https://search.com/"}
    )

    assert response.status_code == 200
    assert response.json()["original_url"] == "https://search.com/"


def test_search_link_not_found(client):
    response = client.get(
        "/links/search", params={"original_url": "https://notfound.com"}
    )
    assert response.status_code == 404


def test_stats_not_found(client):
    response = client.get("/links/unknown/stats")
    assert response.status_code == 404


def test_update_link_unauthorized(client):
    create_resp = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com", "project_name": None},
    )
    short_code = create_resp.json()["short_code"]

    response = client.put(
        f"/links/{short_code}",
        json={
            "original_url": "https://python.org",
            "custom_alias": None,
            "expires_at": None,
            "project_name": None,
        },
    )

    assert response.status_code == 401


def test_delete_link_unauthorized(client):
    create_resp = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com", "project_name": None},
    )
    short_code = create_resp.json()["short_code"]

    response = client.delete(f"/links/{short_code}")

    assert response.status_code == 401


def test_update_link_as_owner(client, auth_headers):
    create_resp = client.post(
        "/links/shorten",
        json={
            "original_url": "https://google.com",
            "custom_alias": "ownerlink",
            "expires_at": None,
            "project_name": None,
        },
        headers=auth_headers,
    )
    short_code = create_resp.json()["short_code"]

    response = client.put(
        f"/links/{short_code}",
        json={
            "original_url": "https://python.org",
            "custom_alias": None,
            "expires_at": None,
            "project_name": None,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["original_url"] == "https://python.org/"


def test_delete_link_as_owner(client, auth_headers):
    create_resp = client.post(
        "/links/shorten",
        json={
            "original_url": "https://google.com",
            "custom_alias": "deletelink",
            "expires_at": None,
            "project_name": None,
        },
        headers=auth_headers,
    )
    short_code = create_resp.json()["short_code"]

    response = client.delete(f"/links/{short_code}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Link deleted"


def test_update_link_forbidden_for_other_user(client, auth_headers):
    create_resp = client.post(
        "/links/shorten",
        json={
            "original_url": "https://google.com",
            "custom_alias": "private1",
            "expires_at": None,
            "project_name": None,
        },
        headers=auth_headers,
    )
    short_code = create_resp.json()["short_code"]

    client.post(
        "/auth/register",
        json={"email": "other@test.com", "password": "12345678"},
    )
    login_response = client.post(
        "/auth/login",
        data={"username": "other@test.com", "password": "12345678"},
    )
    other_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = client.put(
        f"/links/{short_code}",
        json={
            "original_url": "https://python.org",
            "custom_alias": None,
            "expires_at": None,
            "project_name": None,
        },
        headers=other_headers,
    )

    assert response.status_code == 403
