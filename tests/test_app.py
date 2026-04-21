import io
import tempfile
import unittest
from pathlib import Path

from app import app


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.temp_dir = tempfile.TemporaryDirectory()
        app.config["UPLOAD_FOLDER"] = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upload_form_is_public(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Upload an image", response.data)

    def test_upload_image_success(self):
        response = self.client.post(
            "/upload",
            data={"image": (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "photo.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["message"], "Image uploaded successfully")
        self.assertIn("/uploads/", payload["url"])

        uploaded_filename = payload["filename"]
        self.assertTrue(Path(self.temp_dir.name, uploaded_filename).exists())

    def test_upload_rejects_non_image_extension(self):
        response = self.client.post(
            "/upload",
            data={"image": (io.BytesIO(b"hello"), "notes.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Only image files are allowed")


if __name__ == "__main__":
    unittest.main()
