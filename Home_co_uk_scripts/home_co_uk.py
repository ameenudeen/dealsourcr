import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load previously scraped data
existing_file = "postcodes_data_20250524_221647.json"
if os.path.exists(existing_file):
    with open(existing_file, "r", encoding="utf-8") as f:
        results = json.load(f)
        scraped_locations = {entry["location"] for entry in results}
else:
    results = []
    scraped_locations = set()

lock = Lock()

postcodes_to_scrape = ['B3', 'BS16', 'CO2', 'LIVERPOOL','PE30', 'PL29', 'SG15', 'SG2', 'TF12', 'WR4', 'WV9', 'YO12']

postcodes = [p for p in postcodes_to_scrape if p not in scraped_locations]

print(f"🔁 Resuming scrape for {len(postcodes)} new postcodes using 2 threads...")

def clean_days(value):
    match = re.search(r"(\d+)", value)
    return int(match.group(1)) if match else None

def parse_table_rows(table, label_field):
    rows = table.find_all("tr")[1:]
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        label = cells[0].get_text(strip=True)
        props = int(cells[1].get_text(strip=True))
        mean = clean_days(cells[2].get_text(strip=True))
        median = clean_days(cells[3].get_text(strip=True))
        data.append({
            label_field: label,
            "properties": props,
            "mean_days": mean,
            "median_days": median
        })
    return data

def scrape_postcode(postcode, retries=3):
    payload = {
        'api_key': os.environ['SCRAPER_API_KEY'],
        'url': f'https://www.home.co.uk/selling/{postcode.lower()}/time_to_sell/?location={postcode}',
        'render': 'true'
    }

    for attempt in range(retries):
        try:
            response = requests.get("https://api.scraperapi.com/", params=payload, timeout=30)
            response.raise_for_status()
            html = response.text

            soup = BeautifulSoup(html, "html.parser")
            content = soup.find("div", class_="homeco_pr_content") or soup
            tables = content.find_all("table", class_="table") if content else []

            overall = {}
            if len(tables) > 0:
                cells = tables[0].find_all("tr")[1].find_all("td")
                overall = {
                    "total_properties": int(cells[1].get_text(strip=True)),
                    "mean_days": clean_days(cells[2].get_text(strip=True)),
                    "median_days": clean_days(cells[3].get_text(strip=True))
                }

            by_price_band = []
            if len(tables) > 1:
                raw_rows = parse_table_rows(tables[1], "label")
                for row in raw_rows:
                    label = row["label"]
                    prices = list(map(lambda x: int(x.replace(',', '')), re.findall(r"\d{1,3}(?:,\d{3})*", label)))
                    if "under" in label.lower():
                        min_price, max_price = 0, prices[0] if prices else None
                    elif "over" in label.lower():
                        min_price, max_price = prices[0] if prices else None, None
                    else:
                        min_price = prices[0] if len(prices) > 0 else None
                        max_price = prices[1] if len(prices) > 1 else None

                    by_price_band.append({
                        "price_range": {
                            "min": min_price,
                            "max": max_price,
                            "display": label
                        },
                        "properties": row["properties"],
                        "mean_days": row["mean_days"],
                        "median_days": row["median_days"]
                    })

            by_bedrooms = []
            if len(tables) > 2:
                raw_rows = parse_table_rows(tables[2], "label")
                for row in raw_rows:
                    label = row["label"].lower()
                    if "studio" in label:
                        row["bedrooms"] = 0
                    elif "one" in label or "1" in label:
                        row["bedrooms"] = 1
                    elif "two" in label or "2" in label:
                        row["bedrooms"] = 2
                    elif "three" in label or "3" in label:
                        row["bedrooms"] = 3
                    elif "four" in label or "4" in label:
                        row["bedrooms"] = 4
                    elif "five" in label or "5" in label:
                        row["bedrooms"] = 5
                    elif "six" in label or "6" in label:
                        row["bedrooms"] = 6
                    else:
                        continue
                    del row["label"]
                    by_bedrooms.append(row)

            by_property_type = parse_table_rows(tables[3], "type") if len(tables) > 3 else []

            result = {
                "location": postcode.upper(),
                "currency": "GBP",
                "overall": overall,
                "by_price_band": by_price_band,
                "by_bedrooms": by_bedrooms,
                "by_property_type": by_property_type
            }

            with lock:
                results.append(result)

            return

        except Exception as e:
            print(f"⚠️ Retry {attempt+1}/{retries} failed for {postcode}: {e}")

    print(f"❌ Failed all attempts for {postcode}")

total = len(postcodes)
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(scrape_postcode, postcode): postcode for postcode in postcodes}
    for i, future in enumerate(as_completed(futures), 1):
        future.result()
        print(f"[{i}/{total}] Completed")

with open(existing_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"✅ All postcode data updated in {existing_file}")
