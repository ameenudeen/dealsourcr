import requests
from bs4 import BeautifulSoup
import time
import csv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def fetch_listings(base_url, max_pages=10):
    listings = []
    page = 1

    while page <= max_pages:
        url = f"{base_url}?page={page}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"Failed to fetch page {page}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        # Update these selectors based on actual page inspection
        listing_cards = soup.find_all('div', class_='property-item')  # Hypothetical class

        if not listing_cards:
            break  # No more listings

        for card in listing_cards:
            title = card.find('h2', class_='title').text.strip()
            price = card.find('div', class_='price').text.strip()
            location = card.find('span', class_='location').text.strip()
            link = card.find('a')['href'].strip()

            listings.append({
                "title": title,
                "price": price,
                "location": location,
                "link": link
            })

        print(f"Page {page} fetched. Total listings: {len(listings)}")
        page += 1
        time.sleep(2)  # Avoid overwhelming the server

    return listings


if __name__ == "__main__":
    # Example URL (adjust parameters as needed)
    BASE_URL = "https://www.openrent.co.uk/properties-to-rent/london"

    listings = fetch_listings(BASE_URL, max_pages=5)

    # Save to CSV
    with open('openrent_listings.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["title", "price", "location", "link"])
        writer.writeheader()
        writer.writerows(listings)

    print(f"Saved {len(listings)} listings to CSV.")