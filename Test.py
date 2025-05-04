import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_rightmove_search_urls(search_terms):
    """
    Returns a dictionary mapping search terms to their corresponding Rightmove search URLs.
    Handles both direct matches and ambiguous location suggestions.
    """
    results = {}
    base_url = "https://www.rightmove.co.uk/property-for-sale/find.html"

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

        for term in search_terms:
            # Step 1: Perform initial search
            response = session.get(base_url, params={"searchLocation": term}, allow_redirects=True)
            response.raise_for_status()

            # Step 2: Check if we got direct results
            if "locationIdentifier" in response.url:
                results[term] = [response.url]
            else:
                # Step 3: Parse location suggestions
                soup = BeautifulSoup(response.text, "html.parser")
                results[term] = []

                # Find all suggestion links containing locationIdentifier
                suggestion_links = soup.select('a[href*="locationIdentifier="]')
                for link in suggestion_links:
                    href = link.get("href")
                    if href and "/property-for-sale/find.html" in href:
                        absolute_url = urljoin(base_url, href)
                        results[term].append(absolute_url)

    return results


if __name__ == "__main__":
    searches = ["Manchester", "B", "SW1A"]  # Test terms (specific and ambiguous)
    urls = get_rightmove_search_urls(searches)

    # Print results
    for term, links in urls.items():
        print(f"Search: {term}")
        print(f"Found {len(links)} URL(s):")
        for url in links:
            print(f"• {url}")
        print("\n")