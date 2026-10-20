from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from src.api.deps import FileServiceDep
from src.schemas import FileItem, FileUpdate
from src.schemas.file import TITLE_MAX_LENGTH

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[FileItem])
async def list_files(service: FileServiceDep):
    return await service.list_recent()


@router.post("", response_model=FileItem, status_code=201)
async def create_file(
    service: FileServiceDep,
    title: Annotated[str, Form(min_length=1, max_length=TITLE_MAX_LENGTH)],
    file: Annotated[UploadFile, File()],
):
    return await service.create(title=title, upload=file)


@router.get("/{file_id}", response_model=FileItem)
async def get_file(file_id: str, service: FileServiceDep):
    return await service.get(file_id)


@router.patch("/{file_id}", response_model=FileItem)
async def update_file(file_id: str, payload: FileUpdate, service: FileServiceDep):
    return await service.update_title(file_id, payload.title)


@router.get("/{file_id}/download")
async def download_file(file_id: str, service: FileServiceDep):
    file, path = await service.get_for_download(file_id)
    return FileResponse(path=path, media_type=file.mime_type, filename=file.original_name)


@router.delete("/{file_id}", status_code=204)
async def delete_file(file_id: str, service: FileServiceDep):
    await service.delete(file_id)
