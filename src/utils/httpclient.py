from aiohttp import ClientSession, ClientError


class HTTPClient:
    _session: ClientSession | None = None

    def __init__(self): pass

    @property
    def session(self):
        if type(self)._session is None:
            type(self)._session = ClientSession()
        return type(self)._session

    @classmethod
    async def close(cls):
        if cls._session is not None:
            await cls._session.close()
            cls._session = None

    async def get(self, url: str) -> dict | None:
        async with self.session.get(url) as response:
            try: response.raise_for_status()
            except ClientError as e:
                print("[ERROR] HTTPClient GET request failed:", e)
                return None
            return await response.json()

    async def post(self, url: str, data: dict) -> dict | None:
        async with self.session.post(url, json=data) as response:
            try: response.raise_for_status()
            except ClientError as e:
                print("[ERROR] HTTPClient POST request failed:", e)
                return None
            return await response.json()


http_client = HTTPClient()
