
import streamlit as st
from PIL import Image, ImageOps
import io
import base64
import streamlit.components.v1 as components

# Seiteneinstellungen
st.set_page_config(page_title="Bildbearbeitung mit Rahmen & Zoom", layout="centered")
st.title("Bildbearbeitung mit festem Rahmen und Zoom")

# Datei-Upload
uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    # Bild laden und orientieren
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    width, height = img.size

    # Rahmen-Parameter
    frame_width, frame_height = 2000, 750
    margin = 75

    # Zoom-Berechnung
    min_zoom_needed = max(frame_width / width, frame_height / height)
    min_zoom = min_zoom_needed
    max_zoom = 4.0
    default_zoom = max(min_zoom, 1.0)

    zoom = st.slider("Zoom-Faktor", min_zoom, max_zoom, default_zoom, 0.05)

    # Bild skalieren
    new_size = (int(width * zoom), int(height * zoom))
    img_resized = img.resize(new_size, Image.LANCZOS)

    # Positionssteuerung
    max_x = max(0, new_size[0] - frame_width)
    max_y = max(0, new_size[1] - frame_height)

    x_pos = st.slider("X-Position", 0, max_x, 0, 1) if new_size[0] > frame_width else 0
    y_pos = st.slider("Y-Position", 0, max_y, 0, 1) if new_size[1] > frame_height else 0

    # CSS-Offsets
    x_css = (frame_width - new_size[0]) // 2 if new_size[0] <= frame_width else -x_pos
    y_css = (frame_height - new_size[1]) // 2 if new_size[1] <= frame_height else -y_pos

    # Bild in Base64 umwandeln
    buf = io.BytesIO()
    img_resized.save(buf, format="PNG")
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # HTML für Anzeige
    html_code = f"""
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
            <img src="data:image/png;base64,{}
        </div>
    </div>
    """

    # HTML-Komponente einbinden
    components.html(html_code, height=frame_height + margin*2 + 50)

    # Vorschau und Download
    if new_size[0] <= frame_width or new_size[1] <= frame_height:
        canvas = Image.new("RGBA", (frame_width, frame_height), (255, 255, 255, 255))
        paste_x = max(0, (frame_width - new_size[0]) // 2)
        paste_y = max(0, (frame_height - new_size[1]) // 2)
        mask = img_resized if img_resized.mode == "RGBA" else None
        canvas.paste(img_resized, (paste_x, paste_y), mask=mask)
        cropped_img = canvas
    else:
        box = (x_pos, y_pos, x_pos + frame_width, y_pos + frame_height)
        cropped_img = img_resized.crop(box)

    st.write("### Vorschau des zugeschnittenen Ausschnitts")
    st.image(cropped_img, caption="Ausgewählter Ausschnitt", use_column_width=False)

    out_bytes = io.BytesIO()
    cropped_img.save(out_bytes, format="PNG")
    out_bytes.seek(0)

    st.download_button(
        label="Ausschnitt herunterladen",
        data=out_bytes,
        file_name="ausschnitt.png",
        mime="image/png"
    )
else:
    st.info("Bitte ein Bild hochladen (JPG, JPEG oder PNG).")
