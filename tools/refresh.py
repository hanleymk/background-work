#!/usr/bin/env python3
"""Refresh the site from the Google Sheet. Run with /usr/bin/python3 (has Google libs).
Reads text via Sheets API, exports xlsx for embedded images, maps images to rows/columns,
resizes new ones, rewrites docs/data.json, and commits+pushes only if something changed."""
import sys, os, re, io, json, zipfile, hashlib, shutil, subprocess, tempfile, collections
import xml.etree.ElementTree as ET
sys.path.insert(0, "/root/.hermes/skills/productivity/google-workspace/scripts")
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SHEET = "1H3u_c0_rE7Vxt1WqkbqcQuB-eNFzDuPJRuxSoZt0L5o"
VENV_PY = "/root/.hermes/installs/76f6e7e5145b5f39/environments/68d463f16f2e4f8ab6bf31e9ca0e3c40/venv/bin/python3"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS, IMG = f"{ROOT}/docs", f"{ROOT}/docs/img"
DATA = f"{DOCS}/data.json"
DATE_FIX = {"05/14/22": "05/14/25"}  # known typos; unknown ones are left as-is and reported
NS = {"xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
def run(*a, **k): return subprocess.run(a, cwd=ROOT, check=True, text=True, capture_output=True, **k)
def lines(s): return [re.sub(r"^[-\u2013\u2022]\s*", "", l).strip() for l in (s or "").splitlines() if l.strip()]

creds = Credentials.from_authorized_user_file("/root/.hermes/google_token.json")
creds.refresh(Request())
vals = build("sheets", "v4", credentials=creds, cache_discovery=False).spreadsheets().values() \
    .get(spreadsheetId=SHEET, range="A1:F500").execute().get("values", [])
r = requests.get(f"https://docs.google.com/spreadsheets/d/{SHEET}/export?format=xlsx",
                 headers={"Authorization": "Bearer " + creds.token}, timeout=600)
r.raise_for_status()
z = zipfile.ZipFile(io.BytesIO(r.content))

rels = {x.get("Id"): x.get("Target") for x in ET.fromstring(z.read("xl/drawings/_rels/drawing1.xml.rels"))}
pos = collections.defaultdict(list)
for anc in ET.fromstring(z.read("xl/drawings/drawing1.xml")):
    fr, b = anc.find("xdr:from", NS), anc.find(".//a:blip", NS)
    if fr is None or b is None: continue
    row, col = int(fr.find("xdr:row", NS).text), int(fr.find("xdr:col", NS).text)
    target = "xl/" + rels[b.get("{%s}embed" % NS["r"])].replace("../", "")
    pos[row].append((col, hashlib.sha1(z.read(target)).hexdigest()[:12], target))

os.makedirs(IMG, exist_ok=True)
new = {h: t for items in pos.values() for _, h, t in items if not os.path.exists(f"{IMG}/{h}_t.jpg")}
if new:
    tmp = tempfile.mkdtemp()
    for h, t in new.items(): open(f"{tmp}/{h}.jpg", "wb").write(z.read(t))
    run(VENV_PY, f"{ROOT}/tools/resize.py", tmp, IMG); shutil.rmtree(tmp)

out, upcoming, warn = [], False, []
for i, row in enumerate(vals):
    if i == 0 or not row or not row[0].strip(): continue
    if row[0].strip().lower() == "not yet released": break  # ignore everything below the marker
    title, ep, date, ts, notes = ([x.strip() for x in row + [""] * 5][:5])
    date = DATE_FIX.get(date, date)
    if date and not re.fullmatch(r"\d{4}|\d{1,2}/\d{1,2}/\d{2,4}", date): warn.append(f"row {i+1} {title}: odd date '{date}'")
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", date)
    if m and not upcoming:
        y = int(m[3]) + (2000 if int(m[3]) < 100 else 0)
        if y < 2010 and ep: warn.append(f"row {i+1} {title} {ep}: suspicious year {y}, date hidden"); date = ""
    out.append(dict(id=i, title=title, episode=ep, date=date, times=lines(ts), notes=lines(notes),
                    shots=[h for _, h, _ in sorted(pos.get(i, []))], upcoming=upcoming))

old = json.load(open(DATA)) if os.path.exists(DATA) else []
if len(out) < 0.5 * len(old) or (old and not any(e["shots"] for e in out)):
    sys.exit(f"ABORT: sheet looks truncated ({len(out)} entries vs {len(old)} before); site untouched")
used = {s for e in out for s in e["shots"]}
for f in os.listdir(IMG):
    if f.rsplit("_", 1)[0] not in used: os.remove(f"{IMG}/{f}")
json.dump(out, open(DATA, "w"), indent=1, ensure_ascii=False)

if run("git", "status", "--porcelain").stdout.strip():
    run("git", "add", "-A")
    run("git", "commit", "-m", f"Refresh from sheet: {len(out)} entries, {len(used)} images")
    run("git", "push", "origin", "main")
    print(f"UPDATED: {len(out)} entries, {len(used)} images")
else:
    print("No changes")
for w in warn: print("WARN", w)
