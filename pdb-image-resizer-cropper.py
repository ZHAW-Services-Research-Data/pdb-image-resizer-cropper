
import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import io

st.set_page_config(page_title="Bildbearbeitung mit Rahmen & Zoom", layout="centered")
st.title("Bildbearbeitung mit festem Rahmen und Zoom")

uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    width, height = img.size

    # Rahmen-Parameter
    frame_width, frame_height = 2000, 750
    margin = 75
    border_color = (0, 128, 0)  # Grün
    border_thickness = 10

    # Zoom-Berechnung
    min_zoom_needed = max(frame_width / width, frame_height / height)
    zoom = st.slider("Zoom-Faktor", min_zoom_needed, 4.0, max(min_zoom_needed, 1.0), 0.05)

    # Bild skalieren
    new_size = (int(width * zoom), int(height * zoom))
    img_resized = img.resize(new_size, Image.LANCZOS)

    # Positionssteuerung
    max_x = max(0, new_size[0] - frame_width)
    max_y = max(0, new_size[1] - frame_height)

    x_pos = st.slider("X-Position", 0, max_x, 0, 1) if new_size[0] > frame_width else 0
    y_pos = st.slider("Y-Position", 0, max_y, 0, 1) if new_size[1] > frame_height else 0

    # Ausschnitt berechnen
    if new_size[0] <= frame_width or new_size[1] <= frame_height:
        canvas = Image.new("RGB", (frame_width, frame_height), (255, 255, 255))
        paste_x = max(0, (frame_width - new_size[0]) // 2)
        paste_y = max(0, (frame_height - new_size[1]) // 2)
        canvas.paste(img_resized, (paste_x, paste_y))
        cropped_img = canvas
    else:
        box = (x_pos, y_pos, x_pos + frame_width, y_pos + frame_height)
        cropped_img = img_resized.crop(box)

    # Rahmen hinzufügen
    final_img = Image.new("RGB", (frame_width + 2 * margin, frame_height + 2 * margin), (255, 255, 255))
    final_img.paste(cropped_img, (margin, margin))
    draw = ImageDraw.Draw(final_img)
    draw.rectangle([margin, margin, margin + frame_width, margin + frame_height], outline=border_color, width=border_thickness)

    # Anzeige
    st.image(final_img, caption="Bild mit Rahmen", use_column_width=False)

    # Download
    out_bytes = io.BytesIO()
    final_img.save(out_bytes, format="PNG")
    out_bytes.seek(0)

    st.download_button(
        label="Ausschnitt herunterladen",
        data=out_bytes,
        file_name="ausschnitt.png",
        mime="image/png"
    )
else:
    st.info("Bitte ein Bild hochladen (JPG, JPEG oder PNG).")
