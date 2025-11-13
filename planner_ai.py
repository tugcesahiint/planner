# planner_ai.py

import os
import json
import uuid
from typing import Dict, List

from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

client = OpenAI()  # OPENAI_API_KEY ortam değişkeninden okunur


# --- AI TARAFI -------------------------------------------------------------

DEFAULT_STYLE = {
    "title": "Daily Planner",
    "style_name": "Soft Minimal",
    "background_color": "#FDF7F2",
    "accent_color": "#FFC4D6",
    "accent_color_2": "#FDE2E4",
    "text_color": "#333333",
    "quote": "Small steps every day.",
    "sections": [
        "Top Priorities",
        "Schedule",
        "To-Do List",
        "Notes"
    ]
}


def generate_style_with_ai(user_prompt: str = "") -> Dict:
    """
    OpenAI kullanarak planner için rastgele / prompt'a göre stil JSON'u üretir.
    JSON formatı DEFAULT_STYLE ile aynı yapıda.
    """
    base_instruction = """
You are a graphic designer specialized in printable planners for Etsy.
Design a beautiful, aesthetic planner page.

Return ONLY valid JSON (no markdown, no explanation).
Schema:

{
  "title": "Short title for the page, e.g. 'Daily Planner'",
  "style_name": "Short style name, e.g. 'Pastel Minimal'",
  "background_color": "#RRGGBB",
  "accent_color": "#RRGGBB",
  "accent_color_2": "#RRGGBB",
  "text_color": "#RRGGBB",
  "quote": "A short motivational quote (max 80 chars)",
  "sections": [
    "Section title 1",
    "Section title 2",
    "Section title 3",
    "Section title 4"
  ]
}

Rules:
- Use soft, print-friendly colors.
- Choose 3 harmonious colors.
- Provide 3–6 section titles.
- Keep everything in English.
"""

    user_content = f"User style prompt: {user_prompt or 'Surprise me with a unique planner style.'}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            messages=[
                {"role": "system", "content": base_instruction},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message.content.strip()
        style = json.loads(content)
        # Basit doğrulama
        if "sections" not in style or not isinstance(style["sections"], list):
            style["sections"] = DEFAULT_STYLE["sections"]
        return style
    except Exception as e:
        print("AI style generation failed, using default style:", e)
        return DEFAULT_STYLE.copy()


# --- GÖRSEL OLUŞTURMA TARAFI ----------------------------------------------


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Sunucuda her zaman font olmayabilir, bu yüzden try/except ile default'a düş.
    """
    try:
        # Sunucuda Arial yoksa farklı bir ttf dosyası ekleyebilirsin.
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_planner(style: Dict, size_name: str, output_dir: str) -> str:
    """
    Pillow kullanarak planner görseli üretir.
    size_name: 'a4' veya 'us_letter'
    output_dir: static/generated gibi bir klasör
    Geriye, static altında kullanılacak relative path döner. (ör: 'generated/abc.png')
    """

    if size_name == "a4":
        # 210 x 297 mm @ 300 DPI ≈ 2480 x 3508 px
        width, height = 2480, 3508
    else:
        # US Letter 8.5 x 11 in @ 300 DPI ≈ 2550 x 3300 px
        width, height = 2550, 3300

    bg_color = hex_to_rgb(style.get("background_color", "#FFFFFF"))
    accent_color = hex_to_rgb(style.get("accent_color", "#E0E0E0"))
    accent_color_2 = hex_to_rgb(style.get("accent_color_2", "#F0F0F0"))
    text_color = hex_to_rgb(style.get("text_color", "#000000"))

    title = style.get("title", "Planner")
    quote = style.get("quote", "")
    sections: List[str] = style.get("sections", DEFAULT_STYLE["sections"])

    # Görsel oluştur
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    margin_x = int(width * 0.08)
    margin_y = int(height * 0.06)

    # Header (üst bant)
    header_height = int(height * 0.12)
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, margin_y + header_height],
        radius=40,
        fill=accent_color,
    )

    # Başlık
    title_font = load_font(int(header_height * 0.45))
    title_w, title_h = draw.textsize(title, font=title_font)
    title_x = (width - title_w) // 2
    title_y = margin_y + (header_height - title_h) // 3
    draw.text((title_x, title_y), title, fill=(255, 255, 255), font=title_font)

    # Quote (başlığın altına)
    if quote:
        quote_font = load_font(int(header_height * 0.2))
        quote_w, quote_h = draw.textsize(quote, font=quote_font)
        quote_x = (width - quote_w) // 2
        quote_y = margin_y + header_height - quote_h - int(header_height * 0.15)
        draw.text((quote_x, quote_y), quote, fill=(255, 255, 255), font=quote_font)

    # Stil ismi (küçük, sağ üst)
    style_name = style.get("style_name", "")
    if style_name:
        style_font = load_font(int(header_height * 0.18))
        label = f"Style: {style_name}"
        label_w, label_h = draw.textsize(label, font=style_font)
        label_x = width - margin_x - label_w
        label_y = margin_y - int(header_height * 0.4)
        draw.text((label_x, label_y), label, fill=text_color, font=style_font)

    # Ana alan (section'lar)
    available_top = margin_y + header_height + int(height * 0.03)
    available_bottom = height - margin_y
    available_height = available_bottom - available_top

    num_sections = max(1, len(sections))
    gap = int(height * 0.015)
    section_height = (available_height - (num_sections - 1) * gap) // num_sections

    section_title_font = load_font(int(section_height * 0.18))
    section_body_font = load_font(int(section_height * 0.13))

    for i, section_name in enumerate(sections):
        top = available_top + i * (section_height + gap)
        bottom = top + section_height

        # Arka plan kutusu (çizgili varyasyon için iki renkli)
        if i % 2 == 0:
            fill_color = accent_color_2
        else:
            fill_color = (bg_color[0] + 10, bg_color[1] + 10, bg_color[2] + 10)
            fill_color = tuple(min(255, c) for c in fill_color)

        draw.rounded_rectangle(
            [margin_x, top, width - margin_x, bottom],
            radius=30,
            fill=fill_color,
        )

        # Section başlığı
        title_x = margin_x + int(width * 0.015)
        title_y = top + int(section_height * 0.08)
        draw.text((title_x, title_y), section_name, fill=text_color, font=section_title_font)

        # Yazı çizebileceği çizgiler (lined alan)
        line_top = title_y + int(section_height * 0.25)
        line_bottom = bottom - int(section_height * 0.10)
        num_lines = 8
        if section_height < 500:  # daha küçük planner ise çizgi sayısını azalt
            num_lines = 6

        if num_lines > 1:
            line_spacing = (line_bottom - line_top) // (num_lines - 1)
            line_margin = int(width * 0.03)
            for j in range(num_lines):
                y = line_top + j * line_spacing
                draw.line(
                    [margin_x + line_margin, y, width - margin_x - line_margin, y],
                    fill=(200, 200, 200),
                    width=2,
                )

    # Dosya kaydet
    os.makedirs(output_dir, exist_ok=True)
    filename = f"planner_{size_name}_{uuid.uuid4().hex}.png"
    full_path = os.path.join(output_dir, filename)

    img.save(full_path, format="PNG")
    # static altında relative path döndür (ör: 'generated/xyz.png')
    return f"generated/{filename}"
