
import streamlit as st
from PIL import Image, ImageOps
import io
import base64

# Seiteneinstellungen
st.set_page_config(page_title="Bildbearbeitung mit Rahmen & Zoom", layout="centered")
st.title("Bildbearbeitung mit festem Rahmen und Zoom")

# Upload
uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    # Bild öffnen, EXIF-Orientierung korrigieren und konvertieren
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    width, height = img.size

    # Fester Rahmen
    frame_width, frame_height = 2000, 750
    margin = 75

    # Zoom-Grenzen
    min_zoom_needed = max(frame_width / width, frame_height / height)
    min_zoom = min_zoom_needed
    max_zoom = 4.0
    default_zoom = max(min_zoom, 1.0)

    zoom = st.slider("Zoom-Faktor", min_zoom, max_zoom, default_zoom, 0.05)

    # Skalieren
    new_size = (int(width * zoom), int(height * zoom))
    img_resized = img.resize(new_size, Image.LANCZOS)

    # Verschiebungs-Spannen
    max_x = max(0, new_size[0] - frame_width)
    max_y = max(0, new_size[1] - frame_height)

    x_pos = st.slider("X-Position", 0, max_x, 0, 1) if new_size[0] > frame_width else 0
    y_pos = st.slider("Y-Position", 0, max_y, 0, 1) if new_size[1] > frame_height else 0

    # CSS-Offsets für die Vorschau
    if new_size[0] <= frame_width:
        x_css = (frame_width - new_size[0]) // 2
    else:
        x_css = -x_pos

    if new_size[1] <= frame_height:
        y_css = (frame_height - new_size[1]) // 2
    else:
        y_css = -y_pos

    # PNG + Base64 für HTML-Vorschau
    buf = io.BytesIO()
    img_resized.save(buf, format="PNG")
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # HTML + CSS für den Rahmen und das Bild
    st.markdown(
        f"""
        <style>
        .frame-container {{
            width: {frame_width + margin*2}px;
            height: {frame_height + margin*2}px;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #f0f0f0;
            position: relative;
            margin: 16px auto;
        }}
        .frame {{
            width: {frame_width}px;
            height: {frame_height}px;
            border: 5px solid green;
            overflow: hidden;
            position: relative;
            background-color: white;
        }}
        .frame img {{
            position: absolute;
            top: {y_css}px;
            left: {x_css}px;
            width: {new_size[0]}px;
            height: {new_size[1]}px;
            user-select: none;
            -webkit-user-drag: none;
        }}
        </style>
        <div class="frame-container">
            <div class="frame">
                data:image/png;base64,{img_base64}
