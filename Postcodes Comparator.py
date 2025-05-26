import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load fetched postcode data
with open("postcodes_data_20250524_221647.json") as f:
    fetched_data = json.load(f)

fetched_postcodes = set(entry["location"].upper() for entry in fetched_data)

# Load all postcodes from reference file
with open("uk_postcode_england_wales.json") as f:
    all_postcodes = json.load(f)

reference_postcodes = set(entry["postcode"].upper() for entry in all_postcodes)

# Find postcodes in reference that are missing in the fetched data
missing_postcodes = sorted(reference_postcodes - fetched_postcodes)

print(f"Total fetched postcodes: {len(fetched_postcodes)}")
print(f"Total reference postcodes: {len(reference_postcodes)}")
print(f"Missing postcodes: {len(missing_postcodes)}")
print("List of missing postcodes:")
print(missing_postcodes)
