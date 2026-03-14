from locust import HttpUser, task


class LinkShortenerUser(HttpUser):
    @task
    def create_link(self):
        self.client.post(
            "/links/shorten",
            json={"original_url": "https://google.com"},
        )
