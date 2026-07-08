#!/usr/bin/env python3
"""
Build the printable marker sheet from boxes.json.

Usage:  python3 build_ar.py         ->  writes markers.pdf

boxes.json is the single source of truth (the AR page reads it at runtime).
This script only produces the PRINT sheet, and only needs re-running when you
add a NEW card value (existing cards change live by editing boxes.json).

boxes.json is a list of objects:
  { "value": 1, "label": "Box 1", "width_in": 8, "depth_in": 8, "height_in": 12, "color": "#C7A87A" }

Marker type: 4x4_BCH_13_9_3 (512 codes). Print at 100% so each marker = 200 mm.
"""
import json, os, urllib.request
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from PIL import Image

MARKER_MM = 200.0
REPO_DIR  = "4x4_bch_13_9_3"
CACHE     = "marker_cache"

def get_marker_png(value):
    os.makedirs(CACHE, exist_ok=True)
    dst = f"{CACHE}/{value}.png"
    if not os.path.exists(dst):
        url = (f"https://raw.githubusercontent.com/nicolocarpignoli/"
               f"artoolkit-barcode-markers-collection/master/{REPO_DIR}/{value}.png")
        urllib.request.urlretrieve(url, dst)
    return dst

def read_boxes(path="boxes.json"):
    boxes = json.load(open(path))
    seen = set()
    for b in boxes:
        v = int(b["value"])
        if v in seen: raise SystemExit(f"Duplicate barcode value {v} in boxes.json")
        if not (0 <= v <= 511): raise SystemExit(f"Value {v} out of range 0-511")
        seen.add(v)
    return boxes

def build_pdf(boxes, path="markers.pdf"):
    W, H = letter
    c = canvas.Canvas(path, pagesize=letter)
    for b in boxes:
        src = get_marker_png(b["value"])
        im = Image.open(src).convert("RGB").resize((2000,2000), Image.NEAREST)
        tmp = f"{CACHE}/{b['value']}_print.png"; im.save(tmp, dpi=(300,300))
        size = MARKER_MM*mm; x=(W-size)/2; y=(H-size)/2 + 15*mm
        c.drawImage(tmp, x, y, size, size)
        c.setLineWidth(0.5)
        for cx,cy in [(x,y),(x+size,y),(x,y+size),(x+size,y+size)]:
            c.line(cx-6*mm,cy,cx+6*mm,cy); c.line(cx,cy-6*mm,cx,cy+6*mm)
        dims = f"{b['width_in']} x {b['depth_in']} x {b['height_in']} in (W x D x H)"
        c.setFont("Helvetica-Bold",14)
        c.drawCentredString(W/2, y-14*mm, f"MB DESIGN — AR MARKER  ·  value {b['value']}  =  {b['label']}  ·  {dims}")
        c.setFont("Helvetica",10)
        c.drawCentredString(W/2, y-22*mm, f"Print at 100% / Actual Size. Marker must measure {MARKER_MM:.0f} mm edge-to-edge. Keep white space around it.")
        c.drawCentredString(W/2, y-28*mm, "Tape flat to the shelf where this box should stand.")
        c.showPage()
    c.save()
    print(f"wrote {path}  ({len(boxes)} pages)")

if __name__ == "__main__":
    build_pdf(read_boxes())
