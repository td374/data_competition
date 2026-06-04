# -*- coding: utf-8 -*-
\"\"\"
Baidu Maps API Batch Geocoding Script
Converts company names + cities to precise lat/lon coordinates.

Usage:
  1. Get Baidu Maps API key (free): https://lbsyun.baidu.com/apiconsole/key
  2. Set BAIDU_MAP_AK environment variable or replace below
  3. Run: python batch_geocode.py

Output: Updated company_coordinates.csv with verified coordinates
\"\"\"
import os, sys, csv, time, requests

# === CONFIGURATION ===
BAIDU_AK = os.environ.get("BAIDU_MAP_AK", "YOUR_BAIDU_MAP_AK_HERE")
BASE_URL = "https://api.map.baidu.com/geocoding/v3"
INPUT_CSV = os.path.join(os.path.dirname(__file__), "company_coordinates.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "company_coordinates_verified.csv")

# Rate limit: Baidu free tier allows ~30 QPS, be conservative
RATE_LIMIT = 0.5  # seconds between requests

def geocode_baidu(address, city=None, ak=BAIDU_AK):
    \"\"\"Geocode an address using Baidu Maps API.\"\"\"
    if ak == "YOUR_BAIDU_MAP_AK_HERE":
        print("ERROR: Please set BAIDU_MAP_AK environment variable or replace in script")
        return None
    
    params = {
        "address": address,
        "output": "json",
        "ak": ak,
    }
    if city:
        params["city"] = city
    
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == 0:
            location = data["result"]["location"]
            return {
                "lat": location["lat"],
                "lon": location["lng"],
                "confidence": data["result"].get("confidence", 0),
                "level": data["result"].get("level", ""),
            }
        else:
            print(f"  API Error: status={data.get('status')}, msg={data.get('message')}")
            return None
    except Exception as e:
        print(f"  Request Error: {e}")
        return None

def batch_geocode(input_csv=None, output_csv=None, ak=BAIDU_AK):
    \"\"\"Batch geocode all companies with missing or approximate coordinates.\"\"\"
    if input_csv is None:
        input_csv = INPUT_CSV
    if output_csv is None:
        output_csv = OUTPUT_CSV
    
    if ak == "YOUR_BAIDU_MAP_AK_HERE":
        print("="*60)
        print("  BAIDU MAPS API KEY REQUIRED")
        print("="*60)
        print("  1. Register at https://lbsyun.baidu.com/apiconsole/key")
        print("  2. Create a 'Server' type application")
        print("  3. Set environment variable: set BAIDU_MAP_AK=your_key")
        print("     Or edit this script and replace YOUR_BAIDU_MAP_AK_HERE")
        print("="*60)
        return
    
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    fieldnames = list(rows[0].keys())
    if "coord_source" not in fieldnames:
        fieldnames.append("coord_source")
    if "coord_confidence" not in fieldnames:
        fieldnames.append("coord_confidence")
    
    total = len(rows)
    updated = 0
    
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, row in enumerate(rows):
            code = row.get("code", "")
            name = row.get("name", "")
            city = row.get("production_city", "")
            current_src = row.get("coord_source", "")
            
            # Skip if already verified with high confidence
            if current_src == "BaiduMaps-verified":
                writer.writerow(row)
                continue
            
            # Build search query: company name + city
            query = f"{city} {name}" if city else name
            query = query.strip()
            
            print(f"[{i+1}/{total}] {code} {name[:20]}...", end=" ")
            
            result = geocode_baidu(query, city=city, ak=ak)
            
            if result and result["confidence"] >= 50:
                row["lat"] = result["lat"]
                row["lon"] = result["lon"]
                row["coord_source"] = "BaiduMaps-verified"
                row["coord_confidence"] = result["confidence"]
                print(f"OK (conf={result['confidence']}, level={result['level']})")
                updated += 1
            elif result:
                row["lat"] = result["lat"]
                row["lon"] = result["lon"]
                row["coord_source"] = "BaiduMaps-low-conf"
                row["coord_confidence"] = result["confidence"]
                print(f"LOW confidence={result['confidence']}, please verify manually")
                updated += 1
            else:
                print("FAILED - keeping existing coords")
            
            writer.writerow(row)
            time.sleep(RATE_LIMIT)
    
    print(f"\nDone: {updated}/{total} updated. Saved to {output_csv}")
    print(f"Copy to company_coordinates.csv to use with GEE script:")
    print(f"  copy {output_csv} {input_csv}")

if __name__ == "__main__":
    batch_geocode()
