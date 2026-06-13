import httpx
from .modules import MetaModule

class ArdentClient:

    _base_url: str = "https://api.ardent-insight.com/v2"
    _client: httpx.Client

    meta: MetaModule

    def __init__(self, base_url: str | None = None):
        if base_url:
            self._base_url = base_url

        self._client = httpx.Client(base_url=self._base_url)
        self.meta = MetaModule(self._client)
