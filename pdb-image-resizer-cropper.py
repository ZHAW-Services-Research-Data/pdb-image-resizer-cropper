
import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import io

# ----------------------------
# Einstellungen & Titel
# ----------------------------
st.set_page_config(page_title="Billdbearbeitung mit Rahmen & Zoom", layout="centered")
st.title("Bildbearbeitung mit festem Rahmen, Zoom & Prozent-Verschiebung")

# ----------------------------
# Datei-Upload
# ----------------------------
uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Bild laden und an EXIF-Orientierung anpassen
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    orig_w, orig_h = img.size

    # ----------------------------
    # Rahmen-Parameter
    # ----------------------------
    frame_w, frame_h = 2000, 750        # feste Rahmen-Größe (Innenmaß)
    outer_margin = 75                    # "weißer Rand" außen herum
    border_thickness = 10                # grüne Rahmenlinie
    border_color = (0, 128, 0)           # Grün

    # ----------------------------
    # Steuer-Elemente
    # ----------------------------
    # Zoom: 5% bis 200%, Standard 100% (1.0)
    zoom = st.slider("Zoom (%)", 5.0, 200.0, 100.0, 0.5) / 100.0

    # Verschiebung in Prozent: −50% (ganz links/oben) bis +50% (ganz rechts/unten), 0% = zentriert
    x_percent = st.slider("X-Verschiebung (%)", -50, 50, 0, 1)
    y_percent = st.slider("Y-Verschiebung (%)", -50, 50, 0, 1)

    # ----------------------------
    # Bild skalieren nach Zoom
    # ----------------------------
    new_w, new_h = int(orig_w * zoom), int(orig_h * zoom)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # ----------------------------
    # Hilfsfunktion: Prozent → Offset
    # Mappt −50..+50% auf 0..available (0 = linkes/oberes Ende, +50 = rechtes/unteres Ende)
    # ----------------------------
    def percent_to_offset(percent: int, available: int) -> int:
        # available kann Quelle (zu großer Bildteil) oder Ziel (freier Canvas-Rand) sein
        # −50% => 0; 0% => available/2; +50% => available
        return int(((percent + 50) / 100.0) * max(available, 0))

    # ----------------------------
    # Berechnung horizontal
    # ----------------------------
    if new_w >= frame_w:
        # Bild breiter als Rahmen: wir croppen links/rechts aus dem Bild
        available_src_x = new_w - frame_w        # wie weit wir im Bild nach rechts schieben können
        crop_x = percent_to_offset(x_percent, available_src_x)
        paste_x = 0                               # ins Frame immer an (0, *) einsetzen
        crop_w = frame_w
    else:
        # Bild schmaler als Rahmen: wir setzen es innerhalb des Rahmens (Canvas) um
        available_canvas_x = frame_w - new_w     # wie weit wir im Canvas nach rechts schieben können
        paste_x = percent_to_offset(x_percent, available_canvas_x)
        crop_x = 0                                # Quelle vollständig
        crop_w = new_w

    # ----------------------------
    # Berechnung vertikal
    # ----------------------------
    if new_h >= frame_h:
        # Bild höher als Rahmen: wir croppen oben/unten aus dem Bild
        available_src_y = new_h - frame_h
        crop_y = percent_to_offset(y_percent, available_src_y)
        paste_y = 0
        crop_h = frame_h
    else:
        # Bild flacher als Rahmen: wir setzen es innerhalb des Rahmens
        available_canvas_y = frame_h - new_h
        paste_y = percent_to_offset(y_percent, available_canvas_y)
        crop_y = 0
        crop_h = new_h

    # ----------------------------
    # Zuschnitt aus dem skalierten Bild
    # ----------------------------
    crop_box = (crop_x, crop_y, crop_x + crop_w, crop_y + crop_h)
    region = img_resized.crop(crop_box)

    # ----------------------------
    # Canvas (Rahmen-Innenfläche) vorbereiten & Region einfügen
    # ----------------------------
    canvas = Image.new("RGB", (frame_w, frame_h), (255, 255, 255))

    # Transparenz korrekt handhaben, falls PNG mit Alpha
    mask = region.split()[-1] if region.mode == "RGBA" else None
    canvas.paste(region, (paste_x, paste_y), mask=mask)

    # ----------------------------
    # Außenrand + grüner Rahmen zeichnen
    # ----------------------------
    final_w = frame_w + 2 * outer_margin
    final_h = frame_h + 2 * outer_margin
    final_img = Image.new("RGB", (final_w, final_h), (255, 255, 255))
    final_img.paste(canvas, (outer_margin, outer_margin))

    draw = ImageDraw.Draw(final_img)
    # Rahmenrechteck exakt auf die Innenkante legen
    rect = [outer_margin, outer_margin, outer_margin + frame_w - 1, outer_margin + frame_h - 1]
    draw.rectangle(rect, outline=border_color, width=border_thickness)

    # ----------------------------
    # Anzeige
    # ----------------------------
    st.write("### Vorschau")
    st.image(final_img, caption="Bild im Rahmen", use_column_width=False)

    # ----------------------------
    # Download
    # ----------------------------
    out_bytes = io.BytesIO()
    final_img.save(out_bytes, format="PNG")
    out_bytes.seek(0)
    st.download_button("Ausschnitt herunterladen", data=out_bytes, file_name="ausschnitt.png", mime="image/png")

else:
    st.info("Bitte ein Bild hochladen (JPG, JPEG oder PNG).")
