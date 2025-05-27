import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
import time

# Global config
CURRENCY_SYMBOL = "£"
SCRAPERAPI_KEY = os.environ['SCRAPER_API_KEY']
SCRAPERAPI_URL = "http://api.scraperapi.com/"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries

def clean(text):
    return (
        text.replace("\u00a3", "")
            .replace(CURRENCY_SYMBOL, "")
            .replace("pcm", "")
            .replace(",", "")
            .strip()
    )

def convert_price_ranges(raw_ranges):
    structured = []
    for entry in raw_ranges:
        label = entry["range"].replace("pcm", "").strip()
        count = entry["number_of_properties"]

        prices = re.findall(r"\d[\d,]*", label)
        prices = [int(p.replace(",", "")) for p in prices]

        if "under" in label.lower():
            structured.append({
                "range_label": f"Under {CURRENCY_SYMBOL}{prices[0]}",
                "min": 0,
                "max": prices[0],
                "count": count
            })
        elif "over" in label.lower():
            structured.append({
                "range_label": f"Over {CURRENCY_SYMBOL}{prices[0]}",
                "min": prices[0],
                "max": None,
                "count": count
            })
        elif len(prices) == 2:
            structured.append({
                "range_label": f"{CURRENCY_SYMBOL}{prices[0]}–{CURRENCY_SYMBOL}{prices[1]}",
                "min": prices[0],
                "max": prices[1],
                "count": count
            })
        else:
            structured.append({
                "range_label": label,
                "min": None,
                "max": None,
                "count": count
            })
    return structured

def scrape_postcode(postcode):
    target_url = f"https://www.home.co.uk/for_rent/{postcode.lower()}/current_rents?location={postcode}"
    params = {
        "api_key": SCRAPERAPI_KEY,
        "url": target_url,
        "render": "false"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(SCRAPERAPI_URL, params=params, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')

            tables = soup.find_all("table", class_="table--plain")
            if len(tables) < 4:
                raise ValueError("Expected tables not found in HTML")

            summary_rows = tables[0].find_all("tr")
            summary = {
                "total_properties": int(summary_rows[0].find_all("td")[1].text.strip()),
                "new_in_14_days": int(summary_rows[1].find_all("td")[1].text.strip()),
                "average_rent_pcm": int(clean(summary_rows[2].find_all("td")[1].text)),
                "median_rent_pcm": int(clean(summary_rows[3].find_all("td")[1].text)),
            }

            raw_price_data = []
            for row in tables[1].find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) == 2:
                    raw_price_data.append({
                        "range": cells[0].text.strip(),
                        "number_of_properties": int(cells[1].text.strip())
                    })
            structured_price_data = convert_price_ranges(raw_price_data)

            bedroom_data = []
            for row in tables[2].find_all("tr")[1:]:
                cells = row.find_all("td")
                bedroom_data.append({
                    "bedroom_category": cells[0].text.strip(),
                    "number_of_properties": int(cells[1].text.strip()),
                    "average_rent_pcm": int(clean(cells[2].text)),
                    "median_rent_pcm": int(clean(cells[3].text))
                })

            type_data = []
            for row in tables[3].find_all("tr")[1:]:
                cells = row.find_all("td")
                type_data.append({
                    "property_type": cells[0].text.strip(),
                    "number_of_properties": int(cells[1].text.strip()),
                    "average_rent_pcm": int(clean(cells[2].text)),
                    "median_rent_pcm": int(clean(cells[3].text))
                })

            return {
                "postcode": postcode,
                "summary": summary,
                "rents_by_price_range": structured_price_data,
                "rents_by_bedroom": bedroom_data,
                "rents_by_property_type": type_data
            }

        except Exception as e:
            print(f"⚠️ Attempt {attempt}/{MAX_RETRIES} failed for {postcode}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return None

# ----------- MAIN -----------
postcodes = ["BR1", "BR2"]  # Replace with up to 2000 postcodes if needed
all_results = []
failed_postcodes = []

total = len(postcodes)
success_count = 0
fail_count = 0

for idx, postcode in enumerate(postcodes, start=1):
    print(f"\n🔄 Processing {idx} of {total}: {postcode}")
    result = scrape_postcode(postcode)
    if result:
        all_results.append(result)
        success_count += 1
        print(f"✅ Success: {postcode} ({success_count} successful)")
    else:
        failed_postcodes.append(postcode)
        fail_count += 1
        print(f"❌ Failed after {MAX_RETRIES} attempts: {postcode} ({fail_count} failed)")

# Save results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"home_co_uk_rental_{timestamp}.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)
print(f"\n📁 Data saved to: {output_filename}")

# Save failed postcodes
if failed_postcodes:
    fail_filename = f"home_co_uk_rental_failed_{timestamp}.txt"
    with open(fail_filename, "w") as f:
        for p in failed_postcodes:
            f.write(p + "\n")
    print(f"📝 Failed postcodes logged to: {fail_filename}")

# Final summary
print(f"\n🎯 Scraping complete — {success_count} succeeded, {fail_count} failed, out of {total} postcodes.")
