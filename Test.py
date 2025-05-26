import requests

payload = {
    'api_key': '85b8fd8da923bb4b2ca41280890d54cc',
    'url': 'https://www.home.co.uk/selling/br6/time_to_sell/?location=br6',
    'render': 'true'
}

try:
    print("⏳ Fetching Home.co.uk via ScraperAPI...")
    response = requests.get("https://api.scraperapi.com/", params=payload, timeout=30)
    response.raise_for_status()
    html = response.text

    with open("br6_debug_rest.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ HTML saved to br6_debug_rest.html")
except Exception as e:
    print("❌ ScraperAPI request failed:", e)
