import os
import io

from flask import Flask, render_template, request, redirect, url_for
from flask import send_file  # user dialog box for saving the file in their computer

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    NameObject, ArrayObject, DictionaryObject,
    NumberObject, DecodedStreamObject, TextStringObject
)

# reportlab is used to render Bangla text into a mini PDF
# then we extract that as an appearance stream for the form field
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# data.py to import curriculum data from user L-1, T-1 selection
from data import lookup


# ─────────────────────────────────────────────────────────────────────────────
# BANGLA FONT SETUP
# We try a few common font paths on Ubuntu/Debian systems.
# FreeSerif supports Bengali Unicode glyphs.
# If you have Noto Sans Bengali installed, it will be preferred.
# Install with: sudo apt install fonts-freefont-ttf
#           or: sudo apt install fonts-noto-core
# ─────────────────────────────────────────────────────────────────────────────
BANGLA_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",  # best quality
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",             # fallback
]

BANGLA_FONT_PATH = next(
    (f for f in BANGLA_FONT_CANDIDATES if os.path.exists(f)), None
)

if BANGLA_FONT_PATH is None:
    raise RuntimeError(
        "No Bangla font found! Install one:\n"
        "  sudo apt install fonts-freefont-ttf\n"
        "  or: sudo apt install fonts-noto-core"
    )

# Register the font with reportlab once at startup (not inside a function)
pdfmetrics.registerFont(TTFont("BanglaFont", BANGLA_FONT_PATH))
print(f"[INFO] Bangla font loaded: {BANGLA_FONT_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# patch_bangla_ap()
#
# WHY THIS FUNCTION EXISTS:
#   PDF form fields have two layers:
#     1. /V  → the stored value (text string) — Edge reads this
#     2. /AP → the Appearance Stream (pre-drawn pixels) — Chrome reads this
#
#   pypdf's update_page_form_field_values() only sets /V.
#   Chrome ignores /V and only renders /AP.
#   The default /AP uses Helvetica which has NO Bangla glyphs → blank in Chrome.
#
# WHAT THIS FUNCTION DOES:
#   For the 'student_name_b' field, it:
#     1. Finds every widget annotation for that field (can appear on multiple pages)
#     2. Uses reportlab to render the Bangla text into a tiny PDF
#     3. Extracts that rendered content as a Form XObject (PDF's internal format)
#     4. Sets it as the /AP /N (Normal appearance) on the widget
#   Now Chrome reads this pre-drawn appearance and shows the Bangla text correctly.
# ─────────────────────────────────────────────────────────────────────────────
def patch_bangla_ap(writer, reader, bangla_text, font_size=10):

    field_name = "student_name_b"  # the PDF field we are targeting

    print(f"[Bangla] Patching field '{field_name}' with text: {bangla_text}")

    for page_idx, page in enumerate(reader.pages):

        annots = page.get("/Annots")
        if not annots:
            continue  # this page has no form fields, skip

        for annot_ref in annots:
            annot = annot_ref.get_object()

            # skip non-widget annotations (links, comments, etc.)
            if annot.get("/Subtype") != "/Widget":
                continue

            # get the field name — it may be on the parent object
            parent = annot.get("/Parent")
            fname = (parent.get_object().get("/T") if parent else annot.get("/T"))

            if str(fname) != field_name:
                continue  # not our target field

            # get this widget's position on the page
            rect = [float(r) for r in annot["/Rect"]]
            x0, y0, x1, y1 = rect
            w = x1 - x0   # field width
            h = y1 - y0   # field height

            print(f"  [Bangla] Found widget on page {page_idx + 1}, rect={rect}")

            # ── STEP A: render Bangla text into a mini PDF using reportlab ──
            # We create a tiny PDF the exact size of the form field
            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=(w, h))
            c.setFont("BanglaFont", font_size)
            # vertically centre the text inside the field
            draw_y = (h - font_size) / 2 + 1
            c.drawString(2, draw_y, bangla_text)  # 2pt left padding
            c.save()
            buf.seek(0)

            # ── STEP B: extract the content stream from the mini PDF ──
            mini = PdfReader(buf)
            mini_page = mini.pages[0]
            # get the raw drawing commands (PDF content stream)
            stream_data = mini_page["/Contents"].get_object().get_data()
            # get font resources (includes the embedded Bangla font)
            resources = mini_page["/Resources"].get_object()

            # ── STEP C: wrap it as a PDF Form XObject ──
            # A Form XObject is how PDF stores reusable graphics/appearance streams
            xobj = DecodedStreamObject()
            xobj.set_data(stream_data)
            xobj.update({
                NameObject("/Type"):      NameObject("/XObject"),
                NameObject("/Subtype"):   NameObject("/Form"),
                NameObject("/BBox"):      ArrayObject([
                    NumberObject(0), NumberObject(0),
                    NumberObject(w), NumberObject(h)
                ]),
                NameObject("/Resources"): resources,  # includes our Bangla font
            })
            # add the XObject to the PDF and get a reference to it
            ap_ref = writer._add_object(xobj)

            # ── STEP D: find the same widget in writer and patch its /AP ──
            # (writer has its own copies of the annotations)
            w_page = writer.pages[page_idx]
            for w_ref in (w_page.get("/Annots") or []):
                w_annot = w_ref.get_object()

                if w_annot.get("/Subtype") != "/Widget":
                    continue

                wp = w_annot.get("/Parent")
                wf = (wp.get_object().get("/T") if wp else w_annot.get("/T"))

                if str(wf) != field_name:
                    continue

                # match by position to find the exact same widget
                if [float(r) for r in w_annot["/Rect"]] != rect:
                    continue

                # set /AP /N — this is what Chrome reads to draw the field
                w_annot[NameObject("/AP")] = DictionaryObject({
                    NameObject("/N"): ap_ref
                })
                # also update /V — this is what Edge/Acrobat reads
                w_annot[NameObject("/V")] = TextStringObject(bangla_text)

                print(f"  [Bangla] AP stream patched on page {page_idx + 1} ✓")


# ─────────────────────────────────────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        # dictionary whose keys match the PDF field names in Entry_Form3.pdf
        data_field = {
            'id': None,
            'student_name_b': None,   # ← Bangla name field (needs special handling)
            'father': None,
            'mother': None,
            'level': None,
            'term': None,
            'student_name': None,
            'village': None,
            'post': None,
            'zilla': None,
            'thana': None,
            'birth': None,
            'religion': None,
            'school': None,
            'college': None,
            'year_ssc': None,
            'roll_hsc': None,
            'gpa': None,
            'ssc_roll': None,
            'butex_exam': None,
            'phone': None,
            'present_address': None,
            'nationality': None,
            'ssc_board': None,
            'year_hsc': None,
            'hsc_board': None
        }

        # get department, level, term from the HTML form
        department = request.form.get('dept')
        level      = request.form.get('level')
        term       = request.form.get('term')

        # build the lookup key matching the format in data.py
        key = f"{department}: {level.replace('L-', 'Level ')} - {term.replace('T-', 'Term ')}"

        # get course codes and course names for the selected level/term
        # code  → dict like {'s1': 'TE-101', 's2': 'TE-102', ...}
        # course → dict like {'s1': 'Yarn Engineering', ...}
        code, course = lookup(key)

        # get all submitted form values as a flat dict
        html_data = request.form.to_dict()

        # build match dict: only keep keys that exist in data_field
        match = {}
        for key1 in data_field:
            if key1 in html_data:
                match[key1] = html_data[key1]

        print(f"[INFO] Filling fields: {list(match.keys())}")

        # ── load the PDF ──
        file_open  = PdfReader("Entry_Form3.pdf")
        file_write = PdfWriter()
        file_write.append(file_open)  # copy all pages into writer

        # ── fill all regular fields (works for Latin text in all browsers) ──
        for page in file_write.pages:
            try:
                file_write.update_page_form_field_values(page, match, auto_regenerate=False)
            except Exception:
                pass  # some pages may not have all fields — safe to skip

            try:
                file_write.update_page_form_field_values(page, code, auto_regenerate=False)
            except Exception:
                pass

            try:
                file_write.update_page_form_field_values(page, course, auto_regenerate=False)
            except Exception:
                pass

        # ── patch Bangla field appearance for Chrome compatibility ──
        # Chrome ignores the stored /V value and only renders the /AP stream.
        # We build a proper /AP stream with an embedded Bangla font here.
        bangla_name = match.get('student_name_b', '')
        if bangla_name:
            patch_bangla_ap(file_write, file_open, bangla_name, font_size=10)
        else:
            print("[Bangla] No Bangla name provided, skipping AP patch.")

        # tell Edge/Acrobat to regenerate appearances for other fields
        # (Chrome ignores this; it uses /AP directly)
        file_write.set_need_appearances_writer(True)

        # save the filled PDF to disk
        with open("output.pdf", "wb") as file:
            file_write.write(file)

        print("[INFO] output.pdf saved, sending to browser.")

        # send the file to the user as a download
        return send_file(
            "output.pdf",
            as_attachment=True,
            download_name=f"{request.form.get('student_name')}_student_form.pdf"
        )

    else:
        # GET request — just show the form
        return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
