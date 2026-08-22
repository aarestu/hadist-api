import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class HadithApiClient:
    """Infrastructure client wrapper for fetching Hadith API JSON endpoints."""

    def __init__(
        self,
        base_url: str = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1",
        timeout: int = 30,
        max_retries: int = 3,
        max_concurrent: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _get_json(self, client: httpx.AsyncClient, endpoint: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with self.semaphore:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.get(url, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, ValueError) as e:
                    logger.warning(f"Percobaan {attempt}/{self.max_retries} gagal mengunduh {url}: {e}")
                    if attempt == self.max_retries:
                        logger.error(f"Gagal mengunduh {url} setelah {self.max_retries} percobaan.")
                        return None
                    await asyncio.sleep(1 * attempt)
        return None

    async def fetch_editions_index(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        return await self._get_json(client, "editions.json")

    async def fetch_info_index(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        return await self._get_json(client, "info.json")

    async def fetch_edition_content(self, client: httpx.AsyncClient, edition_name: str) -> Optional[Dict[str, Any]]:
        return await self._get_json(client, f"editions/{edition_name}.json")
