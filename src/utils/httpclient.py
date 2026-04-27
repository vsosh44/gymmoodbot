import asyncio
import logging
from typing import Any

from aiohttp import (
    ClientConnectionError,
    ClientError,
    ClientResponseError,
    ClientSession,
    ContentTypeError,
    ServerTimeoutError,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    _session: ClientSession | None = None
    _retry_count = 3
    _retry_delay = 1

    def __init__(self):
        pass

    @property
    def session(self):
        if type(self)._session is None or type(self)._session.closed:
            type(self)._session = ClientSession()
        return type(self)._session

    @classmethod
    async def close(cls):
        if cls._session is not None:
            await cls._session.close()
            cls._session = None

    async def _request(self, method: str, url: str, **kwargs: Any) -> dict | None:
        for attempt in range(1, self._retry_count + 1):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()

            except (ClientConnectionError, ServerTimeoutError, asyncio.TimeoutError) as e:
                logger.warning(
                    "HTTPClient %s request network error. Attempt %s/%s. URL: %s. Error: %s",
                    method.upper(),
                    attempt,
                    self._retry_count,
                    url,
                    e,
                )

                if attempt == self._retry_count:
                    logger.error(
                        "HTTPClient %s request failed after %s attempts. URL: %s",
                        method.upper(),
                        self._retry_count,
                        url,
                    )
                    return None

                await asyncio.sleep(self._retry_delay)
            except ContentTypeError as e:
                logger.error(
                    "HTTPClient %s request returned invalid JSON. URL: %s. Error: %s",
                    method.upper(),
                    url,
                    e,
                )
                return None
            except ClientResponseError as e:
                logger.error(
                    "HTTPClient %s request failed with HTTP status %s. URL: %s. Error: %s",
                    method.upper(),
                    e.status,
                    url,
                    e,
                )
                return None
            except ClientError as e:
                logger.error(
                    "HTTPClient %s request failed. URL: %s. Error: %s",
                    method.upper(),
                    url,
                    e,
                )
                return None
        return None

    async def get(self, url: str) -> dict | None:
        return await self._request("GET", url)

    async def post(self, url: str, data: dict) -> dict | None:
        return await self._request("POST", url, json=data)


http_client = HTTPClient()
