"""文档上传与导入任务状态接口。"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status

from app.schemas.imports import ImportAcceptedResponse, ImportTaskResponse
from app.services.import_files import ImportFileService, get_import_file_service

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post(
    "",
    response_model=ImportAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_import(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="待导入的 PDF 或 Markdown 文档")],
    service: Annotated[ImportFileService, Depends(get_import_file_service)],
) -> ImportAcceptedResponse:
    """保存上传文件并安排后台导入，立即返回供轮询的任务 ID。"""

    task = service.accept_upload(file)
    background_tasks.add_task(service.run_task, task.task_id)
    return ImportAcceptedResponse(
        message="文件已接收，正在后台导入",
        task_id=task.task_id,
        status=task.status,
        filename=task.filename,
        status_url=f"/api/imports/{task.task_id}",
    )


@router.get("/{task_id}", response_model=ImportTaskResponse)
def get_import_status(
    task_id: str,
    service: Annotated[ImportFileService, Depends(get_import_file_service)],
) -> ImportTaskResponse:
    """返回任务进度与安全结果摘要，供前端低频轮询。"""

    return ImportTaskResponse.from_record(service.get_task(task_id))
