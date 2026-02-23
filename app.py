from flask import Flask, render_template, request, send_file
import requests
import os
import io
import base64

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

REMOVEBG_API_KEY = "X7Sz86eeZKNwHEtSDLh2MH9H"
MAX_SIZE = 5 * 1024 * 1024  # 5MB

def remove_background(image_bytes, filename):
    """Kirim file langsung ke remove.bg API"""
    try:
        ext = filename.lower().split(".")[-1]
        mime = "image/png" if ext == "png" else "image/webp" if ext == "webp" else "image/jpeg"

        r = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": (filename, image_bytes, mime)},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVEBG_API_KEY},
            timeout=30
        )
        print(f"[remove.bg] status={r.status_code} size={len(r.content)}")

        if r.status_code == 200:
            return r.content
        else:
            print(f"[remove.bg] error: {r.text}")
            return None

    except Exception as e:
        print(f"[remove.bg] exception: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        try:
            file = request.files.get("image")
            if not file or file.filename == "":
                error = "Pilih file gambar terlebih dahulu."
            elif not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                error = "Format tidak didukung. Gunakan JPG, PNG, atau WEBP."
            else:
                image_bytes = file.read()
                if len(image_bytes) > MAX_SIZE:
                    error = "Ukuran file terlalu besar. Maksimal 5MB."
                else:
                    result_bytes = remove_background(image_bytes, file.filename)
                    if result_bytes:
                        result_b64 = base64.b64encode(result_bytes).decode()
                        orig_b64 = base64.b64encode(image_bytes).decode()
                        ext = file.filename.lower().split(".")[-1]
                        orig_mime = "image/png" if ext == "png" else "image/jpeg"
                        result = {
                            "result": result_b64,
                            "original": orig_b64,
                            "orig_mime": orig_mime,
                        }
                    else:
                        error = "Gagal menghapus background. Coba dengan gambar lain."

        except Exception as e:
            print(f"Error: {e}")
            error = "Terjadi kesalahan. Silakan coba lagi."

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
                         as_attachment=True, download_name="removebg_result.png")
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True)
