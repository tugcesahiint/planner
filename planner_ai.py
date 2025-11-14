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
    "collection_name": "Pastel Weekly Bundle",
    "title": "Weekly Planner",
    "style_name": "Soft Minimal",
    "background_color": "#FFFDF8",
    "accent_color": "#FFB7B2",
    "accent_color_2": "#FFE6A7",
    "text_color": "#333333",
    "quote": "Small steps every day.",
    "daily_sections": ["Top Priorities", "Schedule", "To-Do", "Self-care", "Notes"],
    "weekly_sections": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "monthly_sections": ["Goals", "Important Dates", "Bills", "To-Do", "Notes"],
    "yearly_sections": ["Q1", "Q2", "Q3", "Q4"],
    "decorations": ["stars", "hearts", "dots"],
    "notes_title": "Notes"
}


def generate_style_with_ai(user_prompt: str = "") -> Dict:
    """
    OpenAI kullanarak planner bundle için stil JSON'u üretir.
    Aynı stili cover + daily + weekly + monthly + yearly + notes sayfaları için kullanacağız.
    """
    base_instruction = """
You are a graphic designer specialized in printable planner bundles for Etsy.
Design a coordinated planner collection with a clear, aesthetically pleasing style.

Return ONLY valid JSON (no markdown, no explanation).
Schema:

{
  "collection_name": "Name of the set, e.g. 'Cozy Pastel Week'",
  "title": "Main title for weekly planner cover, e.g. 'Weekly Planner'",
  "style_name": "Short style name, e.g. 'Boho Pastel', 'Minimal Neutral'",
  "background_color": "#RRGGBB",
  "accent_color": "#RRGGBB",
  "accent_color_2": "#RRGGBB",
  "text_color": "#RRGGBB",
  "quote": "Short motivational quote (max 80 chars)",
  "daily_sections": [
    "Section title for daily page 1",
    "Section title for daily page 2",
    "..."
  ],
  "weekly_sections": [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
  ],
  "monthly_sections": [
    "Goals", "Important Dates", "Bills", "To-Do", "Notes"
  ],
  "yearly_sections": [
    "Q1", "Q2", "Q3", "Q4"
  ],
  "decorations": [
    "short words describing doodles, e.g. 'stars', 'plants', 'hearts', 'abstract shapes'"
  ],
  "notes_title": "Title for notes page, e.g. 'Notes' or 'Brain Dump'"
}

Rules:
- Use soft, print-friendly colors that look good when printed.
- Create a coherent aesthetic across all pages (same palette and vibe).
- daily_sections should have between 4 and 8 items.
- Keep all text in English.
- Make the overall style clearly different every time (e.g. kawaii pastel, boho, modern minimal, retro, etc.).
"""

    user_content = f"User style prompt: {user_prompt or 'Surprise me with a unique planner bundle style with fun decorations.'}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.95,
            messages=[
                {"role": "system", "content": base_instruction},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message.content.strip()
        style = json.loads(content)
    except Exception as e:
        print("AI style generation failed, using default style:", e)
        style = DEFAULT_STYLE.copy()

    # Eksik alanlar için fallback
    for key, value in DEFAULT_STYLE.items():
        if key not in style:
            style[key] = value

    # Weekly günleri garanti et
    if not isinstance(style.get("weekly_sections"), list) or len(style["weekly_sections"]) < 7:
        style["weekly_sections"] = DEFAULT_STYLE["weekly_sections"]

    return style


# --- ORTAK YARDIMCI FONKSİYONLAR ------------------------------------------


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
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def get_text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    """
    Pillow'un farklı sürümleri için güvenli text ölçüm fonksiyonu.
    Önce textbbox dener, olmazsa font.getsize'a düşer.
    """
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    except Exception:
        try:
            return font.getsize(text)
        except Exception:
            return 0, 0


def get_canvas(size_name: str, bg_color) -> (Image.Image, ImageDraw.ImageDraw, int, int, int, int):
    """
    Belirtilen boyutta boş planner sayfası oluşturur.
    """
    if size_name == "a4":
        # 210 x 297 mm @ 300 DPI ≈ 2480 x 3508 px
        width, height = 2480, 3508
    else:
        # US Letter 8.5 x 11 in @ 300 DPI ≈ 2550 x 3300 px
        width, height = 2550, 3300

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    margin_x = int(width * 0.06)
    margin_y = int(height * 0.06)

    return img, draw, width, height, margin_x, margin_y


def draw_decorations(draw, width, height, decorations, accent_color, accent_color_2):
    """
    Basit doodle tarzı süslemeler (daire, yıldız, nokta vb).
    """
    if not decorations:
        decorations = ["dots"]

    # köşelerde birkaç basit şekil
    r = int(min(width, height) * 0.02)

    def circle(cx, cy, color):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=None)

    circle(int(width * 0.12), int(height * 0.10), accent_color)
    circle(int(width * 0.88), int(height * 0.18), accent_color_2)
    circle(int(width * 0.16), int(height * 0.85), accent_color_2)
    circle(int(width * 0.84), int(height * 0.80), accent_color)


# --- SAYFA ÇİZİMLERİ ------------------------------------------------------


def draw_cover_page(style: Dict, size_name: str) -> Image.Image:
    bg = hex_to_rgb(style.get("background_color", "#FFFFFF"))
    accent = hex_to_rgb(style.get("accent_color", "#FFB7B2"))
    accent2 = hex_to_rgb(style.get("accent_color_2", "#FFE6A7"))
    text_color = hex_to_rgb(style.get("text_color", "#333333"))

    img, draw, width, height, margin_x, margin_y = get_canvas(size_name, bg)

    # Dış çerçeve
    border_radius = int(min(width, height) * 0.03)
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, height - margin_y],
        radius=border_radius,
        outline=accent,
        width=6,
    )

    collection_name = style.get("collection_name", "Planner Bundle")
    title = style.get("title", "Weekly Planner")
    quote = style.get("quote", "")

    # Başlık alanı
    title_font = load_font(int(height * 0.07))
    subtitle_font = load_font(int(height * 0.035))
    quote_font = load_font(int(height * 0.03))

    # Koleksiyon adı (üstte küçük)
    cn_w, cn_h = get_text_size(draw, collection_name, subtitle_font)
    cn_x = (width - cn_w) // 2
    cn_y = margin_y + int(height * 0.10)
    draw.text((cn_x, cn_y), collection_name, fill=text_color, font=subtitle_font)

    # Ana başlık
    t_w, t_h = get_text_size(draw, title, title_font)
    t_x = (width - t_w) // 2
    t_y = cn_y + cn_h + int(height * 0.03)
    draw.text((t_x, t_y), title, fill=text_color, font=title_font)

    # Alt çizgi
    line_y = t_y + t_h + int(height * 0.02)
    line_margin = int(width * 0.25)
    draw.line([line_margin, line_y, width - line_margin, line_y], fill=accent, width=5)

    # Quote
    if quote:
        q_w, q_h = get_text_size(draw, quote, quote_font)
        q_x = (width - q_w) // 2
        q_y = line_y + int(height * 0.03)
        draw.text((q_x, q_y), quote, fill=text_color, font=quote_font)

    # Alt tarafta sayfa tipi listesi
    footer_font = load_font(int(height * 0.03))
    footer_text = "Includes: Daily • Weekly • Monthly • Yearly • Notes"
    f_w, f_h = get_text_size(draw, footer_text, footer_font)
    f_x = (width - f_w) // 2
    f_y = height - margin_y - int(height * 0.10)
    draw.text((f_x, f_y), footer_text, fill=text_color, font=footer_font)

    # Dekorasyonlar
    draw_decorations(draw, width, height, style.get("decorations"), accent, accent2)

    return img


def draw_daily_page(style: Dict, size_name: str) -> Image.Image:
    bg = hex_to_rgb(style.get("background_color", "#FFFFFF"))
    accent = hex_to_rgb(style.get("accent_color", "#FFB7B2"))
    accent2 = hex_to_rgb(style.get("accent_color_2", "#FFE6A7"))
    text_color = hex_to_rgb(style.get("text_color", "#333333"))

    img, draw, width, height, margin_x, margin_y = get_canvas(size_name, bg)

    daily_sections: List[str] = style.get("daily_sections", DEFAULT_STYLE["daily_sections"])

    header_h = int(height * 0.10)
    # üst başlık bandı
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, margin_y + header_h],
        radius=30,
        fill=accent,
    )

    title_font = load_font(int(header_h * 0.45))
    title = "Daily Planner"
    t_w, t_h = get_text_size(draw, title, title_font)
    t_x = margin_x + int(width * 0.02)
    t_y = margin_y + (header_h - t_h) // 2
    draw.text((t_x, t_y), title, fill=(255, 255, 255), font=title_font)

    # Tarih alanı sağ üstte
    date_font = load_font(int(header_h * 0.28))
    date_label = "Date:"
    d_w, d_h = get_text_size(draw, date_label, date_font)
    d_x = width - margin_x - d_w - int(width * 0.08)
    d_y = margin_y + (header_h - d_h) // 2
    draw.text((d_x, d_y), date_label, fill=(255, 255, 255), font=date_font)
    # küçük çizgi
    line_start = d_x + d_w + 10
    line_end = width - margin_x - 10
    draw.line([line_start, d_y + d_h // 2, line_end, d_y + d_h // 2], fill=(255, 255, 255), width=2)

    # İç alan: iki sütunlu kutular (üstte büyük bloklar, altta 2x2 grid)
    body_top = margin_y + header_h + int(height * 0.03)
    body_bottom = height - margin_y
    body_height = body_bottom - body_top

    col_gap = int(width * 0.02)
    col_width = ((width - 2 * margin_x) - col_gap) // 2

    section_titles = daily_sections[:6]  # max 6 kutu çizeceğiz
    while len(section_titles) < 6:
        section_titles.append("Notes")

    section_font = load_font(int(height * 0.03))

    # İlk iki bölüm: her kolonun üstünde geniş blok
    top_block_h = int(body_height * 0.30)
    for i in range(2):
        left = margin_x + i * (col_width + col_gap)
        right = left + col_width
        top = body_top
        bottom = top + top_block_h

        fill_color = accent2 if i == 0 else (bg[0] + 10, bg[1] + 10, bg[2] + 10)
        fill_color = tuple(min(255, c) for c in fill_color)

        draw.rounded_rectangle([left, top, right, bottom], radius=24, fill=fill_color)

        s_title = section_titles[i]
        s_w, s_h = get_text_size(draw, s_title, section_font)
        s_x = left + int(col_width * 0.06)
        s_y = top + int((top_block_h * 0.18))
        draw.text((s_x, s_y), s_title, fill=text_color, font=section_font)

        # Altına çizgiler
        line_top = s_y + s_h + int(top_block_h * 0.10)
        line_bottom = bottom - int(top_block_h * 0.10)
        num_lines = 8
        if num_lines > 1:
            spacing = (line_bottom - line_top) // (num_lines - 1)
            line_margin = int(col_width * 0.08)
            for j in range(num_lines):
                y = line_top + j * spacing
                draw.line([left + line_margin, y, right - line_margin, y], fill=(190, 190, 190), width=2)

    # Alt 4 kutu (2x2 grid)
    grid_top = body_top + top_block_h + int(height * 0.03)
    grid_height = body_bottom - grid_top
    row_gap = int(height * 0.02)
    row_height = (grid_height - row_gap) // 2

    for row in range(2):
        for col in range(2):
            idx = 2 + row * 2 + col
            left = margin_x + col * (col_width + col_gap)
            right = left + col_width
            top = grid_top + row * (row_height + row_gap)
            bottom = top + row_height

            fill_color = bg if (row + col) % 2 == 0 else accent2
            draw.rounded_rectangle([left, top, right, bottom], radius=20, fill=fill_color)

            s_title = section_titles[idx]
            s_w, s_h = get_text_size(draw, s_title, section_font)
            s_x = left + int(col_width * 0.06)
            s_y = top + int(row_height * 0.12)
            draw.text((s_x, s_y), s_title, fill=text_color, font=section_font)

            # iç çizgiler
            line_top = s_y + s_h + int(row_height * 0.08)
            line_bottom = bottom - int(row_height * 0.12)
            num_lines = 6
            if num_lines > 1:
                spacing = (line_bottom - line_top) // (num_lines - 1)
                line_margin = int(col_width * 0.08)
                for j in range(num_lines):
                    y = line_top + j * spacing
                    draw.line([left + line_margin, y, right - line_margin, y], fill=(200, 200, 200), width=2)

    draw_decorations(draw, width, height, style.get("decorations"), accent, accent2)
    return img


def draw_weekly_page(style: Dict, size_name: str) -> Image.Image:
    bg = hex_to_rgb(style.get("background_color", "#FFFFFF"))
    accent = hex_to_rgb(style.get("accent_color", "#FFB7B2"))
    accent2 = hex_to_rgb(style.get("accent_color_2", "#FFE6A7"))
    text_color = hex_to_rgb(style.get("text_color", "#333333"))

    img, draw, width, height, margin_x, margin_y = get_canvas(size_name, bg)
    days: List[str] = style.get("weekly_sections", DEFAULT_STYLE["weekly_sections"])

    header_h = int(height * 0.10)
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, margin_y + header_h],
        radius=30,
        fill=accent2,
    )

    title_font = load_font(int(header_h * 0.4))
    title = "Week at a Glance"
    t_w, t_h = get_text_size(draw, title, title_font)
    t_x = (width - t_w) // 2
    t_y = margin_y + (header_h - t_h) // 2
    draw.text((t_x, t_y), title, fill=text_color, font=title_font)

    # Sol tarafta gün kutuları + sağda çizgiler (senin ilk örneğe benzer)
    body_top = margin_y + header_h + int(height * 0.03)
    body_bottom = height - margin_y
    body_height = body_bottom - body_top

    row_gap = int(height * 0.01)
    row_height = (body_height - (len(days) - 1) * row_gap) // len(days)

    day_font = load_font(int(row_height * 0.40))

    stripe_w = int(width * 0.12)
    line_margin = int(width * 0.04)

    for i, day in enumerate(days):
        top = body_top + i * (row_height + row_gap)
        bottom = top + row_height

        # renkli gün kutusu
        if i % 2 == 0:
            fill_color = accent
        else:
            fill_color = accent2

        draw.rounded_rectangle(
            [margin_x, top, margin_x + stripe_w, bottom],
            radius=16,
            fill=fill_color,
        )

        d_w, d_h = get_text_size(draw, day, day_font)
        d_x = margin_x + (stripe_w - d_w) // 2
        d_y = top + (row_height - d_h) // 2
        draw.text((d_x, d_y), day, fill=(255, 255, 255), font=day_font)

        # sağ taraf - çizgili alan
        line_top = top + int(row_height * 0.15)
        line_bottom = bottom - int(row_height * 0.15)
        num_lines = 3
        if num_lines > 1:
            spacing = (line_bottom - line_top) // (num_lines - 1)
            for j in range(num_lines):
                y = line_top + j * spacing
                draw.line(
                    [margin_x + stripe_w + line_margin, y, width - margin_x, y],
                    fill=(190, 190, 190),
                    width=2,
                )

    draw_decorations(draw, width, height, style.get("decorations"), accent, accent2)
    return img


def draw_monthly_page(style: Dict, size_name: str) -> Image.Image:
    bg = hex_to_rgb(style.get("background_color", "#FFFFFF"))
    accent = hex_to_rgb(style.get("accent_color", "#FFB7B2"))
    accent2 = hex_to_rgb(style.get("accent_color_2", "#FFE6A7"))
    text_color = hex_to_rgb(style.get("text_color", "#333333"))

    img, draw, width, height, margin_x, margin_y = get_canvas(size_name, bg)
    sections: List[str] = style.get("monthly_sections", DEFAULT_STYLE["monthly_sections"])

    header_h = int(height * 0.10)
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, margin_y + header_h],
        radius=30,
        fill=accent,
    )

    title_font = load_font(int(header_h * 0.4))
    title = "Monthly Overview"
    t_w, t_h = get_text_size(draw, title, title_font)
    t_x = (width - t_w) // 2
    t_y = margin_y + (header_h - t_h) // 2
    draw.text((t_x, t_y), title, fill=(255, 255, 255), font=title_font)

    body_top = margin_y + header_h + int(height * 0.03)
    body_bottom = height - margin_y
    body_height = body_bottom - body_top

    # Sol taraf: mini takvim grid (5x7)
    grid_w = int((width - 2 * margin_x) * 0.58)
    cell_gap = 2
    rows, cols = 5, 7
    cell_w = (grid_w - (cols + 1) * cell_gap) // cols
    cell_h = (body_height - (rows + 1) * cell_gap) // rows

    grid_left = margin_x
    grid_top = body_top

    for r in range(rows):
        for c in range(cols):
            left = grid_left + cell_gap + c * (cell_w + cell_gap)
            top = grid_top + cell_gap + r * (cell_h + cell_gap)
            right = left + cell_w
            bottom = top + cell_h
            color = (bg[0] + 8, bg[1] + 8, bg[2] + 8)
            color = tuple(min(255, x) for x in color)
            draw.rectangle([left, top, right, bottom], outline=(210, 210, 210), fill=color, width=2)

    # Sağ taraf: 3-4 blok (Goals, Important Dates, vs)
    right_left = margin_x + grid_w + int(width * 0.03)
    right_width = width - margin_x - right_left

    num_blocks = min(4, len(sections))
    block_gap = int(height * 0.015)
    block_height = (body_height - (num_blocks - 1) * block_gap) // num_blocks

    sec_font = load_font(int(block_height * 0.22))

    for i in range(num_blocks):
        top = body_top + i * (block_height + block_gap)
        bottom = top + block_height
        fill_color = accent2 if i % 2 == 0 else bg
        draw.rounded_rectangle(
            [right_left, top, right_left + right_width, bottom],
            radius=18,
            fill=fill_color,
        )

        s_title = sections[i]
        s_w, s_h = get_text_size(draw, s_title, sec_font)
        s_x = right_left + int(right_width * 0.07)
        s_y = top + int(block_height * 0.12)
        draw.text((s_x, s_y), s_title, fill=text_color, font=sec_font)

        line_top = s_y + s_h + int(block_height * 0.08)
        line_bottom = bottom - int(block_height * 0.12)
        num_lines = 5
        if num_lines > 1:
            spacing = (line_bottom - line_top) // (num_lines - 1)
            line_margin = int(right_width * 0.07)
            for j in range(num_lines):
                y = line_top + j * spacing
                draw.line([right_left + line_margin, y, right_left + right_width - line_margin, y],
                          fill=(200, 200, 200), width=2)

    draw_decorations(draw, width, height, style.get("decorations"), accent, accent2)
    return img


def draw_yearly_page(style: Dict, size_name: str) -> Image.Image:
    bg = hex_to_rgb(style.get("background_color", "#FFFFFF"))
    accent = hex_to_rgb(style.get("accent_color", "#FFB7B2"))
    accent2 = hex_to_rgb(style.get("accent_color_2", "#FFE6A7"))
    text_color = hex_to_rgb(style.get("text_color", "#333333"))

    img, draw, width, height, margin_x, margin_y = get_canvas(size_name, bg)
    sections: List[str] = style.get("yearly_sections", DEFAULT_STYLE["yearly_sections"])

    header_h = int(height * 0.10)
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, margin_y + header_h],
        radius=30,
        fill=accent2,
    )

    title_font = load_font(int(header_h * 0.4))
    title = "Yearly Planner"
    t_w, t_h = get_text_size(draw, title, title_font)
    t_x = (width - t_w) // 2
    t_y = margin_y + (header_h - t_h) // 2
    draw.text((t_x, t_y), title, fill=text_color, font=title_font)

    body_top = margin_y + header_h + int(height * 0.03)
    body_bottom = height - margin_y
    body_height = body_bottom - body_top

    # 2x2 grid (Q1-Q4 vb.)
    rows, cols = 2, 2
    gap = int(height * 0.02)
    cell_w = ((width - 2 * margin_x) - gap) // 2
    cell_h = (body_height - gap) // 2

    sec_font = load_font(int(cell_h * 0.18))

    idx = 0
    for r in range(rows):
        for c in range(cols):
            left = margin_x + c * (cell_w + gap)
            top = body_top + r * (cell_h + gap)
            right = left + cell_w
            bottom = top + cell_h

            fill_color = accent if idx % 2 == 0 else accent2
            draw.rounded_rectangle([left, top, right, bottom], radius=24, fill=fill_color)

            s_title = sections[idx] if idx < len(sections) else f"Q{idx+1}"
            s_w, s_h = get_text_size(draw, s_title, sec_font)
            s_x = left + int(cell_w * 0.07)
            s_y = top + int(cell_h * 0.10)
            draw.text((s_x, s_y), s_title, fill=text_color, font=sec_font)

            # iç çizgiler
            line_top = s_y + s_h + int(cell_h * 0.08)
            line_bottom = bottom - int(cell_h * 0.12)
            num_lines = 7
            if num_lines > 1:
                spacing = (line_bottom - line_top) // (num_lines - 1)
                line_margin = int(cell_w * 0.07)
                for j in range(num_lines):
                    y = line_top + j * spacing
                    draw.line([left + line_margin, y, right - line_margin, y], fill=(230, 230, 230), width=2)

            idx += 1

    draw_decorations(draw, width, height, style.get("decorations"), accent, accent2)
    return img


def draw_notes_page(style: Dict, size_name: str) -> Image.Image:
    bg = hex_to_rgb(style.get("background_color", "#FFFFFF"))
    accent = hex_to_rgb(style.get("accent_color", "#FFB7B2"))
    accent2 = hex_to_rgb(style.get("accent_color_2", "#FFE6A7"))
    text_color = hex_to_rgb(style.get("text_color", "#333333"))

    img, draw, width, height, margin_x, margin_y = get_canvas(size_name, bg)

    header_h = int(height * 0.10)
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, margin_y + header_h],
        radius=30,
        fill=accent,
    )

    title_font = load_font(int(header_h * 0.4))
    title = style.get("notes_title", "Notes")
    t_w, t_h = get_text_size(draw, title, title_font)
    t_x = margin_x + int(width * 0.03)
    t_y = margin_y + (header_h - t_h) // 2
    draw.text((t_x, t_y), title, fill=(255, 255, 255), font=title_font)

    body_top = margin_y + header_h + int(height * 0.04)
    body_bottom = height - margin_y
    body_height = body_bottom - body_top

    # Noktalı / çizgili not alanı
    line_count = 24
    line_spacing = body_height // line_count
    for i in range(line_count):
        y = body_top + i * line_spacing
        draw.line([margin_x, y, width - margin_x, y], fill=(210, 210, 210), width=1)

    # Hafif doodle
    draw_decorations(draw, width, height, style.get("decorations"), accent, accent2)
    return img


# --- BÜTÜN BUNDLE'I OLUŞTURAN FONKSİYON -----------------------------------


def draw_planner_collection(style: Dict, size_name: str, output_dir: str) -> Dict[str, str]:
    """
    Tek bir stil için:
      - Cover
      - Daily
      - Weekly
      - Monthly
      - Yearly
      - Notes

    olmak üzere 6 sayfa çizip,
    hepsini çok sayfalı bir PDF olarak kaydeder.
    Ayrıca cover sayfasını PNG önizleme olarak kaydeder.

    Geriye:
      {"pdf": "generated/xxx.pdf", "preview": "generated/yyy.png"}
    döndürür.
    """
    os.makedirs(output_dir, exist_ok=True)

    pages: List[Image.Image] = []
    pages.append(draw_cover_page(style, size_name))
    pages.append(draw_daily_page(style, size_name))
    pages.append(draw_weekly_page(style, size_name))
    pages.append(draw_monthly_page(style, size_name))
    pages.append(draw_yearly_page(style, size_name))
    pages.append(draw_notes_page(style, size_name))

    bundle_id = uuid.uuid4().hex

    # PNG preview (cover)
    preview_filename = f"planner_{size_name}_{bundle_id}_preview.png"
    preview_full = os.path.join(output_dir, preview_filename)
    pages[0].save(preview_full, format="PNG")

    # PDF (çok sayfalı)
    pdf_filename = f"planner_{size_name}_{bundle_id}.pdf"
    pdf_full = os.path.join(output_dir, pdf_filename)
    pages[0].save(pdf_full, format="PDF", save_all=True, append_images=pages[1:], resolution=300)

    return {
        "preview": f"generated/{preview_filename}",
        "pdf": f"generated/{pdf_filename}",
    }
