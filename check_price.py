import os, re, requests
from playwright.sync_api import sync_playwright

URL = "https://servatmandi.com"
TOPIC = os.environ["NTFY_TOPIC"]
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    body = page.inner_text("body")
    browser.close()

body = body.translate(DIGITS).replace("\t", " | ")
lines = [re.sub(r"\s+", " ", l).strip() for l in body.split("\n")]
lines = [l for l in lines if l]
print("\n".join(lines))  # برای دیدن متن صفحه توی لاگ

msg = "ردیف طلای 18 عیار پیدا نشد"
for i, line in enumerate(lines):
    if "18" in line and "عیار" in line:
        msg = line
        if not re.search(r"\d[\d,٬]{4,}", line):
            msg += " | " + " | ".join(lines[i + 1:i + 3])
        break

requests.post(f"https://ntfy.sh/{TOPIC}", data=msg.encode("utf-8"),
              headers={"Title": "Gold 18K"})
