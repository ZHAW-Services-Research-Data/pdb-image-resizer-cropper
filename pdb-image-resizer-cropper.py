
import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import io

# ----------------------------
# Einstellungen & Titel
# ----------------------------
st.set_page_config(page_title="Bildbearbeitung mit Rahmen & Zoom", layout="centered")
st.title("Bildbearbeitung mit festem Rahmen, Zoom & Prozent-Verschiebung")

# ----------------------------
# Zielgröße auswählen
# ----------------------------
size_label = st.radio(
    "Zielgröße auswählen",
    options=[
        "Haupt-/Stimmungsbild (2340 x 950 px)",
        "Weiteres Bild für Bildkarussell (1600 x 900 px)",
    ],
    index=0,
    horizontal=False,
)

# Mapping von Auswahl zu Innenmaß (frame)
if "2340 x 950" in size_label:
    frame_w, frame_h = 2340, 950
else:
    frame_w, frame_h = 1600, 900

# Außenrand & Rahmen (nur Vorschau)
outer_margin = 75                    # "weißer Rand" außen herum (bleibt im Download erhalten)
border_thickness = 10                # grüne Rahmenlinie (nur Vorschau)
border_color = (0, 128, 0)           # Grün

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
    # Steuer-Elemente
    # ----------------------------
    zoom = st.slider("Zoom (%)", 5.0, 200.0, 100.0, 0.5) / 100.0
    x_percent = st.slider("X-Verschiebung (%)", -50, 50, 0, 1)
    y_percent = st.slider("Y-Verschiebung (%)", -50, 50, 0, 1)

    # ----------------------------
    # Bild skalieren nach Zoom
    # ----------------------------
    new_w, new_h = int(orig_w * zoom), int(orig_h * zoom)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # ----------------------------
    # Hilfsfunktion: Prozent → Offset
    # Mappt −50..+50% auf 0..available
    # ----------------------------
    def percent_to_offset(percent: int, available: int) -> int:
        return int(((percent + 50) / 100.0) * max(available, 0))

    # ----------------------------
    # Berechnung horizontal
    # ----------------------------
    if new_w >= frame_w:
        # Bild breiter als Rahmen: aus dem Bild croppen
        available_src_x = new_w - frame_w
        crop_x = percent_to_offset(x_percent, available_src_x)
        paste_x = 0
        crop_w = frame_w
    else:
        # Bild schmaler als Rahmen: im Canvas verschieben
        available_canvas_x = frame_w - new_w
        paste_x = percent_to_offset(x_percent, available_canvas_x)
        crop_x = 0
        crop_w = new_w

    # ----------------------------
    # Berechnung vertikal
    # ----------------------------
    if new_h >= frame_h:
        # Bild höher als Rahmen: aus dem Bild croppen
        available_src_y = new_h - frame_h
        crop_y = percent_to_offset(y_percent, available_src_y)
        paste_y = 0
        crop_h = frame_h
    else:
        # Bild flacher als Rahmen: im Canvas verschieben
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
    # Canvas (Innenfläche) vorbereiten & Region einfügen
    # ----------------------------
    canvas = Image.new("RGB", (frame_w, frame_h), (255, 255, 255))
    mask = region.split()[-1] if region.mode == "RGBA" else None
    canvas.paste(region, (paste_x, paste_y), mask=mask)

    # ----------------------------
    # Endbild ohne grünen Rahmen (für Download)
    # ----------------------------
    final_w = frame_w + 2 * outer_margin
    final_h = frame_h + 2 * outer_margin
    final_img = Image.new("RGB", (final_w, final_h), (255, 255, 255))
    final_img.paste(canvas, (outer_margin, outer_margin))

    # ----------------------------
    # Vorschau-Bild: Kopie + grüner Rahmen nur zur Anzeige
    # ----------------------------
    preview_img = final_img.copy()
    draw = ImageDraw.Draw(preview_img)
    rect = [outer_margin, outer_margin, outer_margin + frame_w - 1, outer_margin + frame_h - 1]
    draw.rectangle(rect, outline=border_color, width=border_thickness)

    # ----------------------------
    # Anzeige
    # ----------------------------
    st.write(
        f"### Vorschau — Zielmaß: {frame_w} × {frame_h} px "
        f"(mit weißem Außenrand: {final_w} × {final_h} px)"
    )
    st.image(preview_img, caption="Bild im Rahmen (nur Vorschau)", use_column_width=False)

    # ----------------------------
    # Download (ohne grünen Rahmen)
    # ----------------------------
    out_bytes = io.BytesIO()
    final_img.save(out_bytes, format="PNG")
    out_bytes.seek(0)
    default_name = f"ausschnitt_{frame_w}x{frame_h}.png"
    st.download_button("Ausschnitt herunterladen", data=out_bytes, file_name=default_name, mime="image/png")

else:
