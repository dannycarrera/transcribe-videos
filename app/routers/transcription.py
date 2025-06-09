from fastapi import APIRouter, HTTPException, Depends, Form
import chromadb

from app.schemas.transcription import TranscriptionRequest, TranscriptionResponse, ErrorResponse
from app.services.transcription_service import TranscriptionService
from app.config import config  # Import config

router = APIRouter(prefix="/transcription", tags=["transcription"])


def get_transcription_service():
    chroma_client = chromadb.PersistentClient(path=str(config.chroma_db_path))  # Use config value
    return TranscriptionService(chroma_client)


@router.post(
    "/create",
    response_model=TranscriptionResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Transcribe a video file",
    description="Upload a video file and get its transcription using Whisper AI"
)
async def create_transcript(
    request: TranscriptionRequest = Form(..., media_type="multipart/form-data"),
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    try:
        result = await transcription_service.create_transcript(request.file, request.model_size)
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail="Failed to process video"
            )
        return TranscriptionResponse(**result)
    except Exception as e:
        print(f"Error processing video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video"
        )


@router.get(
    "/{transcript_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Retrieve a transcript",
    description="Get the transcription result by its ID"
)
async def get_transcript(
    transcript_id: str,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    try:
        result = transcription_service.get_transcript(transcript_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Transcript not found"
            )
        return result
    except HTTPException as e:
        if e.status_code == 404:
            raise e
        else:
            print(f"Error retrieving transcript: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve transcript"
            )
    except Exception as e:
        print(f"Error retrieving transcript: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve transcript"
        )


@router.get(
    "/",
    response_model=list[dict],
    responses={500: {"model": ErrorResponse}},
    summary="List all transcripts",
    description="Retrieve a paginated list of all transcripts"
)
async def list_transcripts(
    limit: int = 10,
    offset: int = 0,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    try:
        return transcription_service.list_transcripts(limit, offset)
    except Exception as e:
        print(f"Error listing transcripts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list transcripts"
        )


@router.put(
    "/{transcript_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Update a transcript",
    description="Update the transcription of a video with a different model size"
)
async def update_transcript(
    transcript_id: str,
    model_size: str,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    try:
        result = transcription_service.update_transcript(transcript_id, model_size)
        if not result["success"]:
            if result["message"] == "Transcript not found":
                raise HTTPException(
                    status_code=404,
                    detail="Transcript not found"
                )
            elif result["message"] == "Model size is already the same":
                return result
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update transcript"
                )
        return result
    except HTTPException as e:
        if e.status_code == 404:
            raise e
        else:
            print(f"Error updating transcript: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to update transcript"
            )
    except Exception as e:
        print(f"Error updating transcript: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update transcript"
        )


@router.delete(
    "/{transcript_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Delete a transcript",
    description="Delete a transcript by its ID"
)
async def delete_transcript(
    transcript_id: str,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    try:
        result = transcription_service.delete_transcript(transcript_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Transcript not found"
            )
        return {"message": "Transcript deleted successfully"}
    except HTTPException as e:
        if e.status_code == 404:
            raise e
        else:
            print(f"Error deleting transcript: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete transcript"
            )
    except Exception as e:
        print(f"Error deleting transcript: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete transcript"
        )

