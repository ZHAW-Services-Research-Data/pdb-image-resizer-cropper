
import streamlit as st
from PIL import Image, ImageOps
import io
import base64

st.set_page_config(page_title="Bildbearbeitung mit Rahmen & Zoom", layout="centered")
st.title("Bildbearbeitung mit festem Rahmen und Zoom")

# Upload
uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    # Bild einmalig öffnen, EXIF-Orientierung korrigieren und in RGBA konvertieren
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)  # korrigiert Kamera-Orientierung
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    width, height = img.size

    # Fester Rahmen
    frame_width, frame_height = 2000, 750
    margin = 75  # Rand um den Rahmen (nur visuell im CSS)

    # Zoom-Untergrenze so setzen, dass das Bild den Rahmen füllt (mindestens in einer Dimension)
    min_zoom_needed = max(frame_width / width, frame_height / height)
    # Option: Wenn du kleinere Zooms erlauben willst, nimm: min_zoom = 0.5
    min_zoom = min_zoom_needed
    max_zoom = 4.0
    default_zoom = max(min_zoom, 1.0)

    zoom = st.slider("Zoom-Faktor", min_zoom, max_zoom, default_zoom, 0.05)

    # Bild skalieren mit gutem Filter
    new_size = (int(width * zoom), int(height * zoom))
    img_resized = img.resize(new_size, Image.LANCZOS)

    # Verschiebungsspannen berechnen
    max_x = max(0, new_size[0] - frame_width)
    max_y = max(0, new_size[1] - frame_height)

    # Slider nur anzeigen, wenn nötig
    if new_size[0] > frame_width:
        x_pos = st.slider("X-Position", 0, max_x, 0, 1)
    else:
        x_pos = 0

    if new_size[1] > frame_height:
        y_pos = st.slider("Y-Position", 0, max_y, 0, 1)
    else:
        y_pos = 0

    # CSS-Offsets für die Vorschau im festen Rahmen:
    # Wenn das Bild kleiner als der Rahmen ist, zentrieren wir es (positive Offsets),
    # andernfalls verschieben wir es negativ, um den Cropping-Ausschnitt zu simulieren.
    if new_size[0] <= frame_width:
        x_css = (frame_width - new_size[0]) // 2  # positiv
    else:
        x_css = -x_pos  # negativ

    if new_size[1] <= frame_height:
        y_css = (frame_height - new_size[1]) // 2  # positiv
    else:
        y_css = -y_pos  # negativ

    # PNG + Base64 für HTML-Vorschau
    buf = io.BytesIO()
    # PNG ist ideal für CSS-Vorschau (einheitlich, unterstützt Transparenz)
    img_resized.save(buf, format="PNG")
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # CSS + HTML für den festen Rahmen und die Live-Vorschau
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
            background-color: white; /* Hintergrund innerhalb des Rahmens */
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
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Bild für Download erzeugen:
    # Falls das Bild kleiner als der Rahmen ist, erstellen wir eine Canvas in Rahmen-Größe und fügen das Bild zentriert ein.
    if new_size[0] <= frame_width or new_size[1] <= frame_height:
        canvas = Image.new("RGBA", (frame_width, frame_height), (255, 255, 255, 255))
        paste_x = max(0, (frame_width - new_size[0]) // 2)
        paste_y = max(0, (frame_height - new_size[1]) // 2)
        # Bei RGBA nutzen wir den Alpha-Kanal als Maske
        mask = img_resized if img_resized.mode == "RGBA" else None
        canvas.paste(img_resized, (paste_x, paste_y), mask=mask)
        cropped_img = canvas
    else:
        # Standard-Crop, wenn das Bild groß genug ist
        box = (x_pos, y_pos, x_pos + frame_width, y_pos + frame_height)
        cropped_img = img_resized.crop(box)

    st.write("### Vorschau des zugeschnittenen Ausschnitts")
    st.image(cropped_img, caption="Ausgewählter Ausschnitt", use_column_width=False)

    # Download-Button
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

