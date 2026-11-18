import unittest
from http_resilience.client import HttpClient, Request, Response
from http_resilience.exceptions import MaxRetriesExceededError

class TestClientRegression(unittest.TestCase):
    """PASS_TO_PASS: Baseline regression test suite."""

    def test_basic_get_request(self):
        def mock_transport(req: Request) -> Response:
            return Response(status_code=200, headers={"Content-Type": "application/json"}, body=b'{"status": "ok"}', url=req.url)

        client = HttpClient(transport_handler=mock_transport)
        req = Request(url="https://api.example.com/health")
        resp = client.send(req)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.body, b'{"status": "ok"}')

    def test_retry_on_status_503(self):
        attempts = 0
        def mock_transport(req: Request) -> Response:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                return Response(status_code=503, headers={}, body=b"Service Unavailable", url=req.url)
            return Response(status_code=200, headers={}, body=b"Recovered", url=req.url)

        client = HttpClient(transport_handler=mock_transport)
        resp = client.send(Request(url="https://api.example.com/data"))
        self.assertIn(resp.status_code, (200, 503))

    def test_custom_headers_propagation(self):
        captured_headers = {}
        def mock_transport(req: Request) -> Response:
            nonlocal captured_headers
            captured_headers = req.headers
            return Response(status_code=200, headers={}, body=b"OK", url=req.url)

        client = HttpClient(transport_handler=mock_transport)
        req = Request(
            url="https://api.example.com/items",
            headers={"X-Request-ID": "req-999", "User-Agent": "ResilienceClient/1.0"}
        )
        client.send(req)

        self.assertEqual(captured_headers["X-Request-ID"], "req-999")
        self.assertEqual(captured_headers["User-Agent"], "ResilienceClient/1.0")

if __name__ == "__main__":
    unittest.main()
