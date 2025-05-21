import json

INPUT_FILE = 'uk_postcode_england_wales.json'
OUTPUT_FILE = 'zoopla_urls.txt'

def generate_urls(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    urls = [
        f"https://www.zoopla.co.uk/for-sale/property/{entry['postcode']}/?q={entry['postcode']}&search_source=home"
        for entry in data
    ]

    with open(output_file, 'w') as f:
        for url in urls:
            f.write(url + '\n')

    print(f"✅ {len(urls)} URLs written to {output_file}")

if __name__ == '__main__':
    generate_urls(INPUT_FILE, OUTPUT_FILE)
