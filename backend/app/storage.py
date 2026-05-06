"""Azure Blob Storage helper using Managed Identity."""
from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

from .config import get_settings

_settings = get_settings()
_credential = DefaultAzureCredential()
_account_url = f"https://{_settings.storage_account_name}.blob.core.windows.net"
_blob_service = BlobServiceClient(account_url=_account_url, credential=_credential)


async def upload_blob(blob_name: str, data: bytes, content_type: str) -> str:
    container = _blob_service.get_container_client(_settings.storage_container)
    try:
        await container.create_container()
    except Exception:
        pass  # already exists
    blob = container.get_blob_client(blob_name)
    await blob.upload_blob(
        data,
        overwrite=True,
        content_type=content_type,
    )
    return blob.url
