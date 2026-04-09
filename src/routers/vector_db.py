"""
Vector DB router module.
Provides endpoints for uploading and indexing files into the vector database.
"""

from fastapi import APIRouter, UploadFile, File, Query, status
from schemas.common import ResponseHandler, FileNotUploadedError
from services.vector_db import VectorDBUploadService
from routers.deps import UserDep

router = APIRouter(prefix="/vector-db", tags=["Vector DB"])

vector_db_service = VectorDBUploadService.get_instance()


@router.post("/upload", response_model=ResponseHandler)
async def upload_file(
    _current_user: UserDep,
    file: UploadFile = File(...),
    namespace: str = Query(
        "default", description="Namespace for data isolation in Pinecone"
    ),
):
    """
    Endpoint to upload a file and index its content into Pinecone.
    """
    try:
        # Read file content
        file_content = await file.read()
        file_name = file.filename

        if not file_name:
            raise FileNotUploadedError(message="File name is missing")

        # Call the service to process and index the file
        success = await vector_db_service.upload_and_index_file(
            file_content=file_content, file_name=file_name, namespace=namespace
        )

        if not success:
            raise FileNotUploadedError(
                message=f"Failed to process and index file: {file_name}"
            )

        return ResponseHandler(
            status_code=status.HTTP_201_CREATED,
            message=f"Successfully uploaded and indexed file: {file_name}",
            data={"filename": file_name, "namespace": namespace},
        )

    except Exception as e:
        if isinstance(e, FileNotUploadedError):
            raise e
        raise FileNotUploadedError(message=str(e)) from e
    finally:
        await file.close()
