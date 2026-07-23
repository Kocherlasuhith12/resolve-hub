from abc import ABC, abstractmethod
from contextlib import suppress

import anyio
import httpx

from resolvehub.app.core.config import Settings, get_settings


class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, storage_key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    async def read_file(self, storage_key: str) -> bytes: ...

    @abstractmethod
    async def delete_file(self, storage_key: str) -> None: ...

    @abstractmethod
    async def exists(self, storage_key: str) -> bool: ...


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "storage_data") -> None:
        self.base_dir = anyio.Path(base_dir)

    async def _resolve_path(self, storage_key: str) -> anyio.Path:
        clean_key = storage_key.lstrip("/")
        file_path = self.base_dir / clean_key
        await file_path.parent.mkdir(parents=True, exist_ok=True)
        return file_path

    async def save_file(self, storage_key: str, data: bytes, content_type: str) -> None:
        path = await self._resolve_path(storage_key)
        await path.write_bytes(data)

    async def read_file(self, storage_key: str) -> bytes:
        path = await self._resolve_path(storage_key)
        return await path.read_bytes()

    async def delete_file(self, storage_key: str) -> None:
        path = await self._resolve_path(storage_key)
        if await path.exists():
            await path.unlink()

    async def exists(self, storage_key: str) -> bool:
        path = await self._resolve_path(storage_key)
        return await path.exists()


class S3StorageProvider(StorageProvider):
    def __init__(self, settings: Settings) -> None:
        self.endpoint_url = (settings.s3_endpoint_url or "http://localhost:9000").rstrip("/")
        self.bucket = settings.s3_bucket
        self.access_key = settings.s3_access_key.get_secret_value()
        self.secret_key = settings.s3_secret_key.get_secret_value()
        self.region = settings.s3_region
        self._fallback_local = LocalStorageProvider(settings.storage_local_dir)

    async def save_file(self, storage_key: str, data: bytes, content_type: str) -> None:
        url = f"{self.endpoint_url}/{self.bucket}/{storage_key.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.put(url, content=data, headers={"Content-Type": content_type})
                if resp.status_code not in (200, 201):
                    await self._fallback_local.save_file(storage_key, data, content_type)
        except Exception:
            await self._fallback_local.save_file(storage_key, data, content_type)

    async def read_file(self, storage_key: str) -> bytes:
        url = f"{self.endpoint_url}/{self.bucket}/{storage_key.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.content
                return await self._fallback_local.read_file(storage_key)
        except Exception:
            return await self._fallback_local.read_file(storage_key)

    async def delete_file(self, storage_key: str) -> None:
        url = f"{self.endpoint_url}/{self.bucket}/{storage_key.lstrip('/')}"
        with suppress(Exception):
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.delete(url)
        await self._fallback_local.delete_file(storage_key)

    async def exists(self, storage_key: str) -> bool:
        url = f"{self.endpoint_url}/{self.bucket}/{storage_key.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.head(url)
                if resp.status_code == 200:
                    return True
                return await self._fallback_local.exists(storage_key)
        except Exception:
            return await self._fallback_local.exists(storage_key)


def get_storage_provider(settings: Settings | None = None) -> StorageProvider:
    st = settings or get_settings()
    if st.storage_provider == "s3":
        return S3StorageProvider(st)
    return LocalStorageProvider(st.storage_local_dir)
