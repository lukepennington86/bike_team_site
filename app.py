import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
JPG_EXTENSIONS = {".jpg", ".jpeg"}
SIGNATURE_READ_BYTES = 16

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(Path(__file__).parent / "uploads")


def _is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def _detect_image_extension(header_bytes: bytes) -> str | None:
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header_bytes.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if header_bytes.startswith(b"RIFF") and b"WEBP" in header_bytes[:16]:
        return ".webp"
    return None


@app.get("/")
def index():
    return render_template("upload.html")


@app.post("/upload")
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "Missing image file"}), 400

    image = request.files["image"]
    if image.filename == "":
        return jsonify({"error": "Image file is required"}), 400

    if not _is_allowed_image(image.filename):
        return jsonify({"error": "Only image files are allowed"}), 400

    signature = image.stream.read(SIGNATURE_READ_BYTES)
    image.stream.seek(0)
    detected_extension = _detect_image_extension(signature)
    if detected_extension is None:
        return jsonify({"error": "Only image files are allowed"}), 400

    requested_extension = Path(image.filename).suffix.lower()
    extensions_match = requested_extension == detected_extension
    jpg_equivalent = (
        requested_extension in JPG_EXTENSIONS and detected_extension in JPG_EXTENSIONS
    )
    if not (extensions_match or jpg_equivalent):
        return jsonify({"error": "Only image files are allowed"}), 400

    upload_dir = Path(app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = secure_filename(image.filename)
    final_name = f"{uuid.uuid4().hex}-{original_name}"
    image.save(upload_dir / final_name)

    return jsonify(
        {
            "message": "Image uploaded successfully",
            "filename": final_name,
            "url": f"/uploads/{final_name}",
        }
    )


@app.get("/uploads/<filename>")
def uploaded_file(filename: str):
    if secure_filename(filename) != filename:
        abort(404)

    if not _is_allowed_image(filename):
        abort(404)

    upload_dir = Path(app.config["UPLOAD_FOLDER"]).resolve()
    requested_path = (upload_dir / filename).resolve()
    if not requested_path.is_relative_to(upload_dir) or not requested_path.exists():
        abort(404)

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(_error):
    return jsonify({"error": "Image exceeds max size (10MB)"}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
