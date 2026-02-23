from flask import Flask, render_template, request, send_file
import requests
import os
import io
import base64

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

RAPIDAPI_KEY = "f30b4baaecmsh7d04f39e3f19019p15339bjsnad800cd8c0d2"
RAPIDAPI_HOST = "remove-background18.p.rapidapi.com"
MAX_SIZE = 5 * 1024 * 1024  # 5MB

def remove_background(image_bytes, filename):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }

    # Tentukan mime type
    ext = filename.lower().split(".")[-1]
    mime = "image/png" if ext == "png" else "image/webp" if ext == "webp" else "image/jpeg"

    # Coba 1: multipart file upload
    try:
        r = requests.post(
            f"https://{RAPIDAPI_HOST}/public/remove-background/file",
            files={"image": (filename, image_bytes, mime)},
            headers=headers,
            timeout=30
        )
        print(f"[multipart] status={r.status_code} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except Exception as e:
        print(f"[multipart] error: {e}")

    # Coba 2: base64 encode lalu kirim
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        r = requests.post(
            f"https://{RAPIDAPI_HOST}/public/remove-background/base64",
            json={"image_base64": b64},
            headers={**headers, "Content-Type": "application/json"},
            timeout=30
        )
        print(f"[base64] status={r.status_code} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except Exception as e:
        print(f"[base64] error: {e}")

    # Coba 3: upload ke tmpfiles.org lalu kirim URL nya ke API
    try:
        up = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": (filename, image_bytes, mime)},
            timeout=20
        )
        if up.status_code == 200:
            data = up.json()
            tmp_url = data.get("data", {}).get("url", "").replace(
                "https://tmpfiles.org/", "https://tmpfiles.org/dl/"
            )
            print(f"Uploaded to: {tmp_url}")
            if tmp_url:
                r = requests.post(
                    f"https://{RAPIDAPI_HOST}/public/remove-background/url",
                    data={"url": tmp_url},
                    headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30
                )
                print(f"[url-via-tmp] status={r.status_code} size={len(r.content)}")
                if r.status_code == 200 and len(r.content) > 1000:
                    return r.content
    except Exception as e:
        print(f"[tmpfiles] error: {e}")

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
                        error = "Gagal menghapus background. Coba lagi dengan gambar lain."

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
