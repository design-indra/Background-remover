from flask import Flask, render_template, request, send_file
import os
import io
import base64
from rembg import remove
from PIL import Image

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

MAX_SIZE = 5 * 1024 * 1024  # 5MB

def process_remove_bg(file_bytes):
    input_image = Image.open(io.BytesIO(file_bytes))
    output_image = remove(input_image)
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        file = request.files.get("image")
        if not file or file.filename == "":
            error = "Pilih file gambar terlebih dahulu."
        elif not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            error = "Format file tidak didukung. Gunakan PNG, JPG, atau WEBP."
        else:
            file_bytes = file.read()
            if len(file_bytes) > MAX_SIZE:
                error = "Ukuran file terlalu besar. Maksimal 5MB."
            else:
                try:
                    output_bytes = process_remove_bg(file_bytes)
                    img_base64 = base64.b64encode(output_bytes).decode("utf-8")
                    orig_base64 = base64.b64encode(file_bytes).decode("utf-8")
                    result = {
                        "output": img_base64,
                        "original": orig_base64,
                        "original_ext": file.filename.rsplit('.', 1)[-1].lower()
                    }
                except Exception as e:
                    print(f"Error: {e}")
                    error = "Gagal memproses gambar. Coba dengan gambar lain."

    return render_template("index.html", result=result, error=error)

@app.route("/download", methods=["POST"])
def download():
    img_data = request.form.get("image_data")
    if not img_data:
        return "Invalid", 400
    try:
        img_bytes = base64.b64decode(img_data)
        buffer = io.BytesIO(img_bytes)
        return send_file(buffer, mimetype="image/png",
                         as_attachment=True, download_name="RemoveBG_result.png")
    except Exception as e:
        print(f"Download error: {e}")
        return "Error", 500

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True)
