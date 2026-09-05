import asyncio
import logging

from aiohttp import (
    ClientConnectionError,
    ClientError,
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    ContentTypeError,
    ServerTimeoutError,
)

from utils.config import settings

logger = logging.getLogger(__name__)


class HTTPClient:
    _session: ClientSession | None = None
    _retry_count = 5
    _retry_delay = 1
    _timeout = ClientTimeout(total=15, connect=5, sock_read=10)

    def __init__(self):
        pass

    @property
    def session(self) -> ClientSession:
        if type(self)._session is None or type(self)._session.closed:
            type(self)._session = ClientSession(timeout=self._timeout)
        return type(self)._session

    @classmethod
    async def close(cls):
        if cls._session is not None:
            await cls._session.close()
            cls._session = None

    async def _request(
        self,
        method: str,
        url: str,
        access_token: str,
        json: dict | None = None
    ) -> dict | list | None:
        headers = {
            "apikey": settings.apikey,
            "Authorization": f"Bearer {access_token}"
        }

        for attempt in range(1, self._retry_count + 1):
            try:
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    json=json
                ) as response:
                    if response.status in {429, 500, 502, 503, 504}:
                        text = await response.text()
                        logger.warning(
                            "HTTPClient %s request temporary HTTP error %s. Attempt %s/%s. URL: %s. Response: %s",
                            method.upper(),
                            response.status,
                            attempt,
                            self._retry_count,
                            url,
                            text[:500],
                        )

                        if attempt == self._retry_count:
                            return None

                        retry_after = response.headers.get("Retry-After")
                        delay = (
                            int(retry_after)
                            if retry_after is not None and retry_after.isdigit()
                            else self._retry_delay * attempt
                        )
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()

                    if response.content_length == 0:
                        return {}

                    try:
                        return await response.json()
                    except ContentTypeError:
                        text = await response.text()
                        logger.error(
                            "HTTPClient %s request returned invalid JSON. URL: %s. Response: %s",
                            method.upper(),
                            url,
                            text[:500],
                        )
                        return None

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

                await asyncio.sleep(self._retry_delay * attempt)

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
                logger.warning(
                    "HTTPClient %s request failed. Attempt %s/%s. URL: %s. Error: %s",
                    method.upper(),
                    attempt,
                    self._retry_count,
                    url,
                    e,
                )

                if attempt == self._retry_count:
                    return None

                await asyncio.sleep(self._retry_delay * attempt)

            except Exception as e:
                logger.exception(
                    "HTTPClient %s request unexpected error. Attempt %s/%s. URL: %s. Error: %s",
                    method.upper(),
                    attempt,
                    self._retry_count,
                    url,
                    e,
                )

                if attempt == self._retry_count:
                    return None

                await asyncio.sleep(self._retry_delay * attempt)

        return None

    async def get(self, url: str, access_token: str) -> dict | list | None:
        return await self._request("GET", url, access_token)

    async def post(self, url: str, access_token: str, data: dict) -> dict | list | None:
        return await self._request("POST", url, access_token, json=data)


http_client = HTTPClient()
