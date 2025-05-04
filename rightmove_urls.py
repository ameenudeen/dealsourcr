import json

# Load data
with open("uk_postcode_england_wales.json", "r") as f:
    data = json.load(f)

# Output file
output_file = "rightmove_urls.txt"

# Write only URLs
with open(output_file, "w") as f:
    for entry in data:
        postcode = entry.get("postcode")
        id_ = entry.get("id")
        if postcode and id_:
            url = f"https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation={postcode}&useLocationIdentifier=true&locationIdentifier=OUTCODE%5E{id_}&radius=0.0&_includeSSTC=on"
            f.write(url + "\n")

print(f"✅ Rightmove URLs written to {output_file}")
