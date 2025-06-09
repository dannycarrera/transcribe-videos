import os
from fastapi import UploadFile
import ffmpeg
import whisper
from pathlib import Path
from chromadb import ClientAPI
import uuid
from langchain_ollama import OllamaEmbeddings
import tempfile
import shutil
from app.schemas.transcription import ModelSize
from app.config import config  # Import config

print('config', config)

class TranscriptionService:
    def __init__(self, chroma_client: ClientAPI):
        # Use config for upload directory
        self.upload_dir = config.uploads_path
        self.upload_dir.mkdir(exist_ok=True)

        # Initialize ChromaDB client (persistent storage)
        self.chroma_client = chroma_client
        self.collection = self.chroma_client.get_or_create_collection(
            name="transcripts"
        )

        # Initialize embedding model from config
        self.embedding_model = OllamaEmbeddings(
            base_url=config.ollama_url.unicode_string(), model=config.ollama_model
        )

        # Cache for loaded models
        self._model_cache = {}

    def __get_model(self, model_size: str):
        """Get or load a Whisper model of the specified size"""
        if model_size not in self._model_cache:
            self._model_cache[model_size] = whisper.load_model(model_size)
        return self._model_cache[model_size]

    def __extract_audio(self, video_path: str, audio_path: str) -> bool:
        """Extract audio from video file using ffmpeg."""
        try:
            (
                ffmpeg.input(video_path)
                .output(audio_path, acodec="pcm_s16le", ac=1, ar="16k")
                .run(quiet=True, overwrite_output=True)
            )
            return True
        except ffmpeg.Error as e:
            print(f"Error extracting audio from {video_path}: {e.stderr.decode()}")
            return False

    def __transcribe_audio(self, audio_path: str, model: whisper.Whisper) -> str | None:
        """Transcribe audio file using Whisper model."""
        try:
            result = model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            print(f"Error transcribing {audio_path}: {e}")
            return None

    def __upsert_transcript(
        self, transcript_id: str, transcript: str, video_path: str, model_size: str
    ) -> bool:
        """Save transcript to ChromaDB with LLaMA embeddings and video path metadata."""
        try:
            # Generate embedding for the transcript
            embedding = self.embedding_model.embed_query(transcript)

            # Store in ChromaDB with video_path as metadata
            self.collection.upsert(
                embeddings=[embedding],
                documents=[transcript],
                metadatas=[{"video_path": video_path, "model_size": model_size}],
                ids=[transcript_id],
            )

            return True
        except Exception as e:
            print(f"Error saving transcript to ChromaDB for {video_path}: {e}")
            return False

    def __extract_and_transcribe_audio_and_save_transcript(
        self, transcript_id: str, video_path: str, model_size: str
    ):
        """Extract audio from video file and transcribe it using Whisper model."""
        try:
            model = self.__get_model(model_size)
            # Create temporary directory for audio extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                video_name = os.path.basename(video_path)
                video_stem = Path(video_name).stem

                # Create temporary audio file
                audio_path = os.path.join(temp_dir, f"{video_stem}.wav")

                if not self.__extract_audio(video_path, audio_path):
                    return None

                transcript = self.__transcribe_audio(audio_path, model)

                self.__upsert_transcript(
                    transcript_id, transcript, video_path, model_size
                )

            return transcript
        except Exception as e:
            print(f"Error extracting and transcribing audio and saving transcript: {e}")
            return None

    async def create_transcript(
        self, file: UploadFile, model_size: ModelSize = ModelSize.base
    ):
        """Create a transcript by processing a video file and return
        the processed video path, transcript, and transcript ID."""

        # Create a unique ID for new entry
        transcript_id = str(uuid.uuid4())

        # Generate unique filename and create full path
        unique_filename = f"{transcript_id}_{file.filename}"
        file_path = self.upload_dir / unique_filename

        # Save uploaded file
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            print(f"Error saving file: {e}")
            return {
                "success": False,
                "video_path": str(file_path),
                "transcript": None,
                "transcript_id": None,
                "model_size": model_size,
            }
        finally:
            file.file.close()

        video_path = str(file_path)

        # Extract and Transcribe audio then save transcript to ChromaDB
        transcript = self.__extract_and_transcribe_audio_and_save_transcript(
            transcript_id, video_path, model_size
        )
        if not transcript:
            # Delete the file if there's an error
            if file_path.exists():
                file_path.unlink()
            return {
                "success": False,
                "video_path": video_path,
                "transcript": None,
                "transcript_id": None,
                "model_size": model_size,
            }

        return {
            "success": True,
            "video_path": video_path,
            "transcript": transcript,
            "transcript_id": transcript_id,
            "model_size": model_size,
        }

    def get_transcript(self, transcript_id: str) -> dict | None:
        """Retrieve a single transcript by its ID."""
        try:
            result = self.collection.get(
                ids=[transcript_id], include=["documents", "metadatas"]
            )

            if not result["ids"]:
                return None

            return {
                "transcript_id": result["ids"][0],
                "transcript": result["documents"][0],
                "metadata": result["metadatas"][0],
            }
        except Exception as e:
            print(f"Error retrieving transcript {transcript_id}: {e}")
            return None

    def list_transcripts(self, limit: int = 10, offset: int = 0) -> list[dict]:
        """List all transcripts with pagination."""
        try:
            result = self.collection.get(
                include=["documents", "metadatas"], limit=limit, offset=offset
            )
            return [
                {"transcript_id": id_, "transcript": doc, "metadata": meta}
                for id_, doc, meta in zip(
                    result["ids"], result["documents"], result["metadatas"]
                )
            ]
        except Exception as e:
            print(f"Error listing transcripts: {e}")
            return []

    def update_transcript(self, transcript_id: str, model_size: str) -> dict:
        """Update an existing transcript with a new model size.

        Args:
            transcript_id (str): The ID of the transcript to update.
            model_size (str): The new model size to use for transcription.

        Returns:
            dict: A dictionary containing the success status and a message or error detail.
        """
        try:
            # Check if transcript exists
            existing = self.get_transcript(transcript_id)
            if not existing:
                return {"success": False, "message": "Transcript not found"}

            # Check if model size is the same
            if existing["metadata"]["model_size"] == model_size:
                return {"success": False, "message": "Model size is already the same"}

            # Perform the update by re-transcribing the audio with the new model size
            transcript = self.__extract_and_transcribe_audio_and_save_transcript(
                transcript_id, existing["metadata"]["video_path"], model_size
            )

            if transcript is None:
                return {
                    "success": False,
                    "message": "Failed to update transcript due to transcription error",
                }

            return {
                "success": True,
                "message": "Transcript updated successfully",
                "transcript_id": transcript_id,
                "new_model_size": model_size,
            }
        except Exception as e:
            print(f"Error updating transcript {transcript_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update transcript: {str(e)}",
            }

    def delete_transcript(self, transcript_id: str) -> bool:
        """Delete a transcript by its ID."""
        try:
            # Check if transcript exists
            existing = self.get_transcript(transcript_id)
            if not existing:
                return False

            self.collection.delete(ids=[transcript_id])

            return True
        except Exception as e:
            print(f"Error deleting transcript {transcript_id}: {e}")
            return False
