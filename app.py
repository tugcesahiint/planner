# app.py

import os
from flask import Flask, render_template, request
from planner_ai import generate_style_with_ai, draw_planner

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

    # 2) A4 ve US Letter için planner görsellerini üret
    a4_rel_path = draw_planner(style, "a4", GENERATED_DIR)
    us_rel_path = draw_planner(style, "us_letter", GENERATED_DIR)

    # 3) Sonuç sayfasına gönder
    return render_template(
        "result.html",
        style=style,
        a4_image=a4_rel_path,
        us_image=us_rel_path,
        user_prompt=user_prompt,
    )


if __name__ == "__main__":
    # Lokalde test için
    app.run(host="0.0.0.0", port=5000, debug=True)
