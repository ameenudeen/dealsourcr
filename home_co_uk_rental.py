import requests
from bs4 import BeautifulSoup
import json
import re

# Global currency symbol
CURRENCY_SYMBOL = "£"

# Clean currency and numeric strings
def clean(text):
    return (
        text.replace("\u00a3", "")
            .replace(CURRENCY_SYMBOL, "")
            .replace("pcm", "")
            .replace(",", "")
            .strip()
    )

# Convert raw range strings into structured format
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

# Fetch the page
url = "https://www.home.co.uk/for_rent/br6/current_rents?location=br6"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# ----------- Summary Data -----------
summary_table = soup.find_all("table", class_="table--plain")[0]
summary_rows = summary_table.find_all("tr")

summary = {
    "total_properties": int(summary_rows[0].find_all("td")[1].text.strip()),
    "new_in_14_days": int(summary_rows[1].find_all("td")[1].text.strip()),
    "average_rent_pcm": int(clean(summary_rows[2].find_all("td")[1].text)),
    "median_rent_pcm": int(clean(summary_rows[3].find_all("td")[1].text)),
}

# ----------- Rents by Price Range -----------
price_table = soup.find_all("table", class_="table--plain")[1]
raw_price_data = []
for row in price_table.find_all("tr")[1:]:
    cells = row.find_all("td")
    if len(cells) == 2:
        raw_price_data.append({
            "range": cells[0].text.strip(),
            "number_of_properties": int(cells[1].text.strip())
        })

structured_price_data = convert_price_ranges(raw_price_data)

# ----------- Rents by Bedrooms -----------
bedroom_table = soup.find_all("table", class_="table--plain")[2]
bedroom_data = []
for row in bedroom_table.find_all("tr")[1:]:
    cells = row.find_all("td")
    bedroom_data.append({
        "bedroom_category": cells[0].text.strip(),
        "number_of_properties": int(cells[1].text.strip()),
        "average_rent_pcm": int(clean(cells[2].text)),
        "median_rent_pcm": int(clean(cells[3].text))
    })

# ----------- Rents by Property Type -----------
type_table = soup.find_all("table", class_="table--plain")[3]
type_data = []
for row in type_table.find_all("tr")[1:]:
    cells = row.find_all("td")
    type_data.append({
        "property_type": cells[0].text.strip(),
        "number_of_properties": int(cells[1].text.strip()),
        "average_rent_pcm": int(clean(cells[2].text)),
        "median_rent_pcm": int(clean(cells[3].text))
    })

# ----------- Combine and Save -----------
data = {
    "summary": summary,
    "rents_by_price_range": structured_price_data,
    "rents_by_bedroom": bedroom_data,
    "rents_by_property_type": type_data
}

with open("br6_rental_overview.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Structured data saved to br6_rental_overview.json")
