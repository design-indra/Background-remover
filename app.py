from flask import Flask, render_template, request, send_file
import requests
import os
import io
import base64

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

RAPIDAPI_KEY = "f30b4baaecmsh7d04f39e3f19019p15339bjsnad800cd8c0d2"
RAPIDAPI_HOST = "remove-background18.p.rapidapi.com"
IMGBB_API_KEY = "3c82513a7b37b9f8610656309cd6e2d1"
MAX_SIZE = 5 * 1024 * 1024  # 5MB

def upload_to_imgbb(image_bytes):
    """Upload gambar ke ImgBB, dapat URL publik"""
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": IMGBB_API_KEY,
                "image": b64,
            },
            timeout=20
        )
        print(f"[imgbb] status={r.status_code}")
        data = r.json()
        if data.get("success"):
            url = data["data"]["url"]
            print(f"[imgbb] URL: {url}")
            return url
        else:
            print(f"[imgbb] failed: {data}")
    except Exception as e:
        print(f"[imgbb] error: {e}")
    return None

def remove_background(image_url):
    """Kirim URL ke RapidAPI remove-background"""
    try:
        r = requests.post(
            f"https://{RAPIDAPI_HOST}/public/remove-background/url",
            data={"url": image_url},
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=30
        )
        print(f"[removebg] status={r.status_code} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
        else:
            print(f"[removebg] response: {r.text[:300]}")
    except Exception as e:
        print(f"[removebg] error: {e}")
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
                    # Step 1: Upload ke ImgBB → dapat URL publik
                    public_url = upload_to_imgbb(image_bytes)

                    if not public_url:
                        error = "Gagal mengupload gambar ke server. Silakan coba lagi."
                    else:
                        # Step 2: Kirim URL ke RapidAPI
                        result_bytes = remove_background(public_url)
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
