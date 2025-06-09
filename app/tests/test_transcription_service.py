import asyncio
from io import BytesIO
import unittest
import chromadb
import os
import shutil
from fastapi import UploadFile

from app.services.transcription_service import TranscriptionService
from app.config import config


class TestTranscriptionService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir_path = os.path.dirname(os.path.realpath(__file__))
        cls.client = chromadb.Client()
        cls.transcription_service = TranscriptionService(cls.client)
        cls.collection = cls.client.get_or_create_collection(name="transcripts")
        cls.video_path = os.path.join(
            cls.dir_path, "videos", "kennedy-inaugural-excerpt.mp4"
        )
        cls.collection.delete(where={"id": {"$ne": ""}})  # Delete all records

    @classmethod
    def tearDownClass(cls):
        # Clean up test uploads directory
        if config.uploads_path.exists():
            shutil.rmtree(config.uploads_path)

    def setUp(self):
        self.create_upload_file()

    def tearDown(self):
        self.collection.delete(where={"id": {"$ne": ""}})  # Delete all records

        # Clean up any files created during the test
        for file in config.uploads_path.glob("*"):
            if file.is_file():
                file.unlink()

    def create_upload_file(self):
        with open(self.video_path, "rb") as file:
            file_bytes = file.read()
            file_like = BytesIO(file_bytes)
            file_like.name = "kennedy-inaugural-excerpt.mp4"
            self.video_file = UploadFile(
                file=file_like,
                filename=file_like.name,
                headers={"content-type": "video/mp4"},
            )

    def test_create_transcript_success(self):
        model_size = "tiny"

        result = asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )

        self.assertTrue(result["success"])
        self.assertIsNotNone(result["video_path"])
        self.assertEqual(result["model_size"], model_size)
        self.assertIsNotNone(result["transcript"])
        self.assertIsNotNone(result["transcript_id"])

        video_path = result["video_path"]

        # Check the stored data in ChromaDB
        count = self.collection.count()
        self.assertEqual(count, 1)

        item = self.collection.get(
            where={"video_path": video_path},
            include=["documents", "embeddings", "metadatas"],
        )

        self.assertEqual(item["ids"][0], result["transcript_id"])
        self.assertEqual(len(item["embeddings"]), 1)
        self.assertEqual(len(item["documents"]), 1)
        self.assertIn("Let the word go", item["documents"][0])
        self.assertEqual(item["documents"][0], result["transcript"])
        self.assertEqual(item["metadatas"][0]["video_path"], video_path)
        self.assertEqual(item["metadatas"][0]["model_size"], model_size)

    def test_create_transcript_failure(self):
        model_size = "tiny"
        file_like = BytesIO(b"this is a fake video file")
        file_like.name = "test.mp4"

        upload_file = UploadFile(
            filename=file_like.name,
            file=file_like,
            headers={"content-type": "video/mp4"},
        )

        # Call the service method
        result = asyncio.run(
            self.transcription_service.create_transcript(upload_file, model_size)
        )

        # Verify the result
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["video_path"])
        self.assertEqual(result["model_size"], model_size)
        self.assertIsNone(result["transcript"])
        self.assertIsNone(result["transcript_id"])

    # Get transcript
    def test_get_transcript_success(self):
        model_size = "tiny"
        result = asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )
        transcript_id = result["transcript_id"]
        transcript = self.transcription_service.get_transcript(transcript_id)
        self.assertEqual(transcript["transcript"], result["transcript"])

    def test_get_transcript_failure(self):
        transcript_id = "nonexistent_id"
        result = self.transcription_service.get_transcript(transcript_id)
        self.assertIsNone(result)

    # List transcripts
    def test_list_transcripts_all(self):
        model_size = "tiny"
        asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )
        # Create a new video file since the previous one is closed
        self.create_upload_file()
        asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )

        transcripts = self.transcription_service.list_transcripts()
        self.assertEqual(len(transcripts), 2)

    def test_list_transcripts_paged(self):
        model_size = "tiny"
        asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )
        # Create a new video file since the previous one is closed
        self.create_upload_file()
        result_2 = asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )
        transcripts = self.transcription_service.list_transcripts(1, 1)
        self.assertEqual(len(transcripts), 1)
        self.assertEqual(transcripts[0]["transcript_id"], result_2["transcript_id"])

    def test_list_transcripts_paged_none(self):
        model_size = "tiny"
        asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )
        # Create a new video file since the previous one is closed
        self.create_upload_file()
        asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )
        transcripts = self.transcription_service.list_transcripts(10, 2)
        self.assertEqual(len(transcripts), 0)

    def test_list_transcripts_none(self):
        transcripts = self.transcription_service.list_transcripts()
        self.assertEqual(len(transcripts), 0)

    # Update transcript
    def test_update_transcript_success(self):
        model_size = "tiny"
        create_result = asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )

        transcript_id = create_result["transcript_id"]
        new_model_size = "base"
        result = self.transcription_service.update_transcript(
            transcript_id, new_model_size
        )
        self.assertTrue(result["success"])

        # Verify the transcript was updated in ChromaDB
        transcript = self.transcription_service.get_transcript(transcript_id)
        self.assertEqual(transcript["metadata"]["model_size"], new_model_size)

    def test_update_transcript_failure_nonexistent(self):
        transcript_id = "nonexistent_id"
        new_model_size = "base"
        result = self.transcription_service.update_transcript(
            transcript_id, new_model_size
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Transcript not found")

    def test_update_transcript_failure_same_model_size(self):
        model_size = "tiny"
        create_result = asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )

        transcript_id = create_result["transcript_id"]
        result = self.transcription_service.update_transcript(transcript_id, model_size)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Model size is already the same")

    # Delete transcript
    def test_delete_transcript_success(self):
        model_size = "tiny"
        create_result = asyncio.run(
            self.transcription_service.create_transcript(self.video_file, model_size)
        )

        transcript_id = create_result["transcript_id"]
        result = self.transcription_service.delete_transcript(transcript_id)
        self.assertTrue(result)

        # Verify the transcript is deleted
        result = self.transcription_service.get_transcript(transcript_id)
        self.assertIsNone(result)

    def test_delete_transcript_failure_nonexistent(self):
        transcript_id = "nonexistent_id"
        result = self.transcription_service.delete_transcript(transcript_id)
        self.assertFalse(result)
