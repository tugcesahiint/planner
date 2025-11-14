# app.py

import os
from flask import Flask, render_template, request
from planner_ai import generate_style_with_ai, draw_planner_collection

app = Flask(__name__)

# static/generated klasörünü hazırla
GENERATED_DIR = os.path.join(app.static_folder, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    user_prompt = request.form.get("prompt", "").strip()

    # 1) AI ile stil üret
    style = generate_style_with_ai(user_prompt)

    # 2) A4 ve US Letter için bundle (çok sayfalı PDF + preview PNG) oluştur
    a4_files = draw_planner_collection(style, "a4", GENERATED_DIR)
    us_files = draw_planner_collection(style, "us_letter", GENERATED_DIR)

    # 3) Sonuç sayfasına gönder
    return render_template(
        "result.html",
        style=style,
        a4_preview=a4_files["preview"],
        a4_pdf=a4_files["pdf"],
        us_preview=us_files["preview"],
        us_pdf=us_files["pdf"],
        user_prompt=user_prompt,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
