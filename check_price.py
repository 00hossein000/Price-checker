import os, re, json, requests
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

URL = "https://servatmandi.com"
TOPIC = os.environ["NTFY_TOPIC"]
THRESHOLD = 0.5  # درصد تغییر برای هشدار
STATE_FILE = "prices.json"
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def notify(text, title="Prices", high=False):
    headers = {"Title": title}
    if high:
        headers["Priority"] = "high"
        headers["Tags"] = "warning"
    requests.post(f"https://ntfy.sh/{TOPIC}", data=text.encode("utf-8"), headers=headers)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(10000)
        body = page.inner_text("body")
    except Exception as e:
        notify("خطا در باز کردن سایت: " + type(e).__name__)
        raise
    finally:
        browser.close()

body = body.translate(DIGITS).replace("\t", " | ")
lines = [re.sub(r"\s+", " ", l).strip() for l in body.split("\n")]
lines = [l for l in lines if l]
print("\n".join(lines))

def find_row(must, avoid=()):
    for i, line in enumerate(lines):
        if all(k in line for k in must) and not any(a in line for a in avoid):
            row = line
            if not re.search(r"\d[\d,٬.]{3,}", row):
                row += " | " + " | ".join(lines[i + 1:i + 3])
            return row
    return None

def parse_value(row, key):
    after = re.split(key, row, maxsplit=1)[-1]
    after = re.sub(r"[\d.,٬]+\s*[%٪]|[%٪]\s*[\d.,٬]+", " ", after)
    for token in re.findall(r"\d[\d,٬]*(?:\.\d+)?", after):
        if len(re.sub(r"\D", "", token)) >= 3:
            return float(token.replace(",", "").replace("٬", ""))
    return None

def fmt(v):
    return f"{v:,.2f}".rstrip("0").rstrip(".")

items = [
    ("gold18", "طلای 18 عیار", "عیار", find_row(["18", "عیار"])),
    ("usd", "دلار آمریکا",
     "دلار",
     find_row(["دلار", "آمریکا"]) or find_row(["دلار", "امریکا"]) or find_row(["دلار"], avoid=["تتر"])),
    ("usdt", "تتر", "تتر", find_row(["تتر"])),
    ("ounce", "انس طلا", "انس", find_row(["انس", "طلا"]) or find_row(["انس"])),
]

try:
    with open(STATE_FILE) as f:
        prev = json.load(f)
except Exception:
    prev = {}

new = dict(prev)
out, alerts = [], []
for key, name, kw, row in items:
    if not row:
        out.append(f"{name}: پیدا نشد")
        continue
    out.append(row)
    val = parse_value(row, kw)
    if val is None:
        continue
    old = prev.get(key)
    if old:
        pct = (val - old) / old * 100
        if abs(pct) > THRESHOLD:
            alerts.append(f"{name}: از {fmt(old)} به {fmt(val)} ({pct:+.2f}%)")
    new[key] = val

with open(STATE_FILE, "w") as f:
    json.dump(new, f, indent=2, sort_keys=True)

now = datetime.now(ZoneInfo("Asia/Tehran")).strftime("%H:%M")
notify("\n".join(out) + f"\nساعت بررسی: {now}")
if alerts:
    notify("\n".join(alerts), title="Price Alert", high=True)
