from math import radians, cos, sin, sqrt, atan2

import requests


def haversine(coord1, coord2):
    """Calculate distance (in km) between two latitude/longitude coordinates."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def nearest_station(lat, lon, radius=10000):
    """Find stations within `radius` meters using OpenStreetMap."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node[railway=station](around:{radius},{lat},{lon});
      node[railway=subway_entrance](around:{radius},{lat},{lon});
      way[railway=station](around:{radius},{lat},{lon});
      relation[railway=station](around:{radius},{lat},{lon});
    );
    out center;
    """
    response = requests.post(overpass_url, data={'data': query})
    if response.status_code == 200:
        stations = []
        for element in response.json().get('elements', []):
            if 'tags' in element and 'name' in element['tags']:
                # Extract coordinates
                if element['type'] == 'node':
                    station_lat = element['lat']
                    station_lon = element['lon']
                else:
                    station_lat = element['center']['lat']
                    station_lon = element['center']['lon']
                # Calculate distance
                distance = haversine((lat, lon), (station_lat, station_lon))
                stations.append({
                    'name': element['tags']['name'],
                    'distance_km': round(distance, 2),
                    'coordinates': (station_lat, station_lon)
                })
        # Sort by distance
        return sorted(stations, key=lambda x: x['distance_km'])
    else:
        raise ConnectionError("Overpass API request failed.")

print(nearest_station(51.36743, 0.05634, 3000))