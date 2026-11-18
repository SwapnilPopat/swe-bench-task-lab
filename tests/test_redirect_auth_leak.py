import unittest
from http_resilience.client import HttpClient, Request, Response

class TestRedirectAuthLeak(unittest.TestCase):
    """FAIL_TO_PASS: Defect reproduction and security verifier suite."""

    def test_cross_origin_redirect_strips_auth_header(self):
        """FAIL_TO_PASS: Verifies Authorization header is stripped when host changes."""
        requests_received = []

        def mock_transport(req: Request) -> Response:
            requests_received.append(req)
            if req.url == "https://api.example.com/download":
                return Response(
                    status_code=302,
                    headers={"Location": "https://mirrors.external-untrusted.com/pkg.tar.gz"},
                    body=b"",
                    url=req.url
                )
            return Response(status_code=200, headers={}, body=b"BINARY_DATA", url=req.url)

        client = HttpClient(transport_handler=mock_transport)
        initial_request = Request(
            url="https://api.example.com/download",
            headers={
                "Authorization": "Bearer secret_user_token_abc123",
                "Proxy-Authorization": "Basic proxy_auth_xyz",
                "Accept": "application/octet-stream"
            }
        )

        resp = client.send(initial_request)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(requests_received), 2)

        # Second request to mirrors.external-untrusted.com MUST NOT contain Authorization
        second_req = requests_received[1]
        self.assertEqual(second_req.url, "https://mirrors.external-untrusted.com/pkg.tar.gz")
        self.assertNotIn("Authorization", second_req.headers, "Security Defect: Authorization header leaked across origin!")
        self.assertNotIn("Proxy-Authorization", second_req.headers, "Security Defect: Proxy-Authorization header leaked!")
        self.assertEqual(second_req.headers.get("Accept"), "application/octet-stream")

    def test_same_origin_redirect_preserves_auth_header(self):
        """FAIL_TO_PASS: Verifies Authorization header is preserved when host remains identical."""
        requests_received = []

        def mock_transport(req: Request) -> Response:
            requests_received.append(req)
            if req.url == "https://api.example.com/v1/profile":
                return Response(
                    status_code=301,
                    headers={"Location": "https://api.example.com/v2/profile"},
                    body=b"",
                    url=req.url
                )
            return Response(status_code=200, headers={}, body=b"PROFILE_DATA", url=req.url)

        client = HttpClient(transport_handler=mock_transport)
        initial_request = Request(
            url="https://api.example.com/v1/profile",
            headers={"Authorization": "Bearer secret_user_token_abc123"}
        )

        resp = client.send(initial_request)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(requests_received), 2)

        second_req = requests_received[1]
        self.assertEqual(second_req.url, "https://api.example.com/v2/profile")
        self.assertEqual(second_req.headers.get("Authorization"), "Bearer secret_user_token_abc123")

if __name__ == "__main__":
    unittest.main()
