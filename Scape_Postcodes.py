import requests
from bs4 import BeautifulSoup
import json
import time

# Mapping postcode areas to countries (partial list for non-England areas)
postcode_area_to_country = {
    "BT": "Northern Ireland",
    "AB": "Scotland", "DD": "Scotland", "DG": "Scotland", "EH": "Scotland",
    "FK": "Scotland", "G": "Scotland", "HS": "Scotland", "IV": "Scotland",
    "KA": "Scotland", "KW": "Scotland", "KY": "Scotland", "ML": "Scotland",
    "PA": "Scotland", "PH": "Scotland", "TD": "Scotland", "ZE": "Scotland",
    "CF": "Wales", "CH": "Wales", "LL": "Wales", "LD": "Wales",
    "NP": "Wales", "SA": "Wales", "SY": "Wales"
}

def get_country(postcode):
    area = ''.join([c for c in postcode if not c.isdigit()])
    return postcode_area_to_country.get(area, "England")

def extract_postcode_data(url):
    print(f"🔎 Extracting from: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable"})

    data = []
    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "postcode" in headers[0] and "post town" in headers[1]:
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    postcode = cells[0].get_text(strip=True).upper()
                    post_town = cells[1].get_text(strip=True).upper()
                    data.append({
                        "postcode": postcode,
                        "postTown": post_town,
                        "country": get_country(postcode)
                    })
            break
    return data

def get_rightmove_id(postcode, retries=3, delay=1.0):
    api_url = f"https://los.rightmove.co.uk/typeahead?query={postcode}&limit=10&exclude=STREET"
    for attempt in range(retries):
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                results = response.json().get("matches", [])
                for item in results:
                    if item.get("displayName", "").upper() == postcode.upper():
                        return item.get("id")
        except Exception as e:
            print(f"[{postcode}] Error: {e}")
        time.sleep(delay * (attempt + 1))
    print(f"❌ Failed to fetch ID for: {postcode}")
    failed_postcodes.append(postcode)
    return None

postcode_areas = [
    "AB", "AL", "B", "BA", "BB", "BD", "BH", "BL", "BN", "BR", "BS", "BT", "CA", "CB", "CF",
    "CH", "CM", "CO", "CR", "CT", "CV", "CW", "DA", "DD", "DE", "DG", "DH", "DL", "DN", "DT",
    "DY", "E", "EC", "EH", "EN", "EX", "FK", "FY", "G", "GL", "GU", "HA", "HD", "HG", "HP",
    "HR", "HS", "HU", "HX", "IG", "IP", "IV", "KA", "KT", "KW", "KY", "L", "LA", "LD", "LE",
    "LL", "LN", "LS", "LU", "M", "ME", "MK", "ML", "N", "NE", "NG", "NN", "NP", "NR", "NW",
    "OL", "OX", "PA", "PE", "PH", "PL", "PO", "PR", "RG", "RH", "RM", "S", "SA", "SE", "SG",
    "SK", "SL", "SM", "SN", "SO", "SP", "SR", "SS", "ST", "SW", "SY", "TA", "TD", "TF", "TN",
    "TQ", "TR", "TS", "TW", "UB", "W", "WA", "WC", "WD", "WF", "WN", "WR", "WS", "WV", "YO", "ZE"
]
urls = [f"https://en.wikipedia.org/wiki/{area}_postcode_area" for area in postcode_areas]

final_data = []
failed_postcodes = []

for url in urls:
    try:
        area_data = extract_postcode_data(url)
        for entry in area_data:
            postcode = entry["postcode"]
            country = entry["country"]
            if country not in ["England", "Wales"]:
                continue
            time.sleep(0.5)
            entry["id"] = get_rightmove_id(postcode)
            print(f"→ {postcode} ({country}): {entry['id']}")
        final_data.extend([entry for entry in area_data if entry["country"] in ["England", "Wales"]])
    except Exception as e:
        print(f"⚠️ Error processing {url}: {e}")

# Save filtered data
with open("uk_postcode_england_wales.json", "w") as f:
    json.dump(final_data, f, indent=2)

# Save failed lookups
if failed_postcodes:
    with open("failed_postcodes.txt", "w") as f:
        for code in failed_postcodes:
            f.write(code + "\n")
    print(f"⚠️ {len(failed_postcodes)} postcodes failed and were saved to failed_postcodes.txt")

print("✅ England & Wales data saved to uk_postcode_england_wales.json")
