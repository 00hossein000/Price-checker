import os, requests
from bs4 import BeautifulSoup

URL = "آدرس-سایت-اینجا"
TOPIC = os.environ["NTFY_TOPIC"]

html = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
soup = BeautifulSoup(html, "html.parser")
price = soup.select_one("سلکتور-قیمت-اینجا").get_text(strip=True)

requests.post(f"https://ntfy.sh/{TOPIC}",
              data=f"قیمت امروز: {price}".encode("utf-8"),
              headers={"Title": "Price Alert"})
