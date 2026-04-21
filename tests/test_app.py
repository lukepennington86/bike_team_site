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
        tiny_png = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDAT\x08\x99c```\x00\x00\x00\x04\x00\x01\xf6\x178U"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        response = self.client.post(
            "/upload",
            data={"image": (io.BytesIO(tiny_png), "photo.png")},
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

    def test_upload_rejects_invalid_image_content(self):
        response = self.client.post(
            "/upload",
            data={"image": (io.BytesIO(b"not-a-real-image"), "photo.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Only image files are allowed")

    def test_upload_rejects_file_over_limit(self):
        # Size is enforced by Flask before content validation is evaluated.
        oversized = io.BytesIO(
            b"\x89PNG\r\n\x1a\n" + (b"a" * ((10 * 1024 * 1024) + 1))
        )
        response = self.client.post(
            "/upload",
            data={"image": (oversized, "photo.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.get_json()["error"], "Image exceeds max size (10MB)")

    def test_upload_accepts_jpeg_extension_variants(self):
        response = self.client.post(
            "/upload",
            data={"image": (io.BytesIO(b"\xff\xd8\xff\xdb"), "photo.jpeg")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message"], "Image uploaded successfully")


if __name__ == "__main__":
    unittest.main()
