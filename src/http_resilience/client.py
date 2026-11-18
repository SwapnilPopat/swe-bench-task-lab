import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable
from .exceptions import MaxRetriesExceededError

@dataclass
class Request:
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None

@dataclass
class Response:
    status_code: int
    headers: Dict[str, str]
    body: bytes
    url: str

class HttpClient:
    """Production HTTP Client simulation with redirect and retry policies."""

    def __init__(self, transport_handler: Optional[Callable[[Request], Response]] = None, max_retries: int = 3):
        self.transport_handler = transport_handler or self._default_transport
        self.max_retries = max_retries

    def _default_transport(self, req: Request) -> Response:
        raise NotImplementedError("Transport handler must be provided for simulated runtime.")

    def send(self, req: Request, max_redirects: int = 5) -> Response:
        current_req = req
        redirect_count = 0

        while True:
            response = self.transport_handler(current_req)

            # Check for HTTP redirect status codes
            if response.status_code in (301, 302, 303, 307, 308):
                if redirect_count >= max_redirects:
                    raise MaxRetriesExceededError("Exceeded maximum redirect ceiling")

                location = response.headers.get("Location")
                if not location:
                    return response

                # Resolve relative redirects
                next_url = urllib.parse.urljoin(current_req.url, location)

                # Prepare next headers
                new_headers = dict(current_req.headers)

                # BUG HERE (Base Commit Defect):
                # We forward headers verbatim without stripping Authorization on cross-origin redirects!
                # Proper behaviour requires checking if host/scheme/port changed, and stripping sensitive auth headers.

                redirect_count += 1
                current_req = Request(
                    url=next_url,
                    method="GET" if response.status_code == 303 else current_req.method,
                    headers=new_headers,
                    body=current_req.body if response.status_code not in (301, 302, 303) else None
                )
                continue

            return response
