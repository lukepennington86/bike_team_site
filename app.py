import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(Path(__file__).parent / "uploads")


def _is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


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


@app.get("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
