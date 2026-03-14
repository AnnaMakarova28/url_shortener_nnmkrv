def test_redirect(client):
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
    )

    short_code = response.json()["short_code"]

    redirect = client.get(f"/{short_code}", follow_redirects=False)

    assert redirect.status_code in (302, 307)


def test_redirect_not_found(client):
    response = client.get("/unknown-code", follow_redirects=False)
    assert response.status_code == 404


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
