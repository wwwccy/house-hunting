# utils/zillow_fetcher.py
import requests
import re
import json
import time
from bs4 import BeautifulSoup
from typing import List, Dict

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"

SEARCH_URL_TEMPLATE = "https://www.zillow.com/homes/for_rent/{zip}_rb/"

def _get_page(url: str, timeout=10) -> str:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text

def _extract_json_from_html(html: str) -> Dict:
    """
    Zillow often embeds page data in a <script> or as JSON inside HTML comments.
    This function tries several heuristics to find and parse that JSON.
    """
    # 1) Try to find "!--" wrapped JSON (common pattern)
    m = re.search(r'<!--\s*(\{"queryState".*?)\s*-->', html, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # 2) Search for 'searchPageState' or 'zillow' patterns
    m2 = re.search(r'!--\s*(.*"searchResults":\s*\{.*)\s*-->', html, re.S)
    if m2:
        try:
            return json.loads(m2.group(1))
        except Exception:
            pass

    # 3) Try to parse any <script> tags that include "searchResults"
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script"):
        text = script.string
        if not text:
            continue
        if "searchResults" in text or "cat1" in text and "searchList" in text:
            # find first {...}
            m3 = re.search(r'(\{.*"searchResults".*\})', text, re.S)
            if m3:
                try:
                    return json.loads(m3.group(1))
                except Exception:
                    continue
    # If nothing found, raise
    raise ValueError("Could not extract Zillow JSON from HTML")

def fetch_listings_by_zip(zip_code: str, max_pages: int = 1, delay: float = 1.0) -> List[Dict]:
    """
    Fetch listing raw data for a given zip code.
    Returns a list of raw listing dicts (may be empty).
    """
    listings = []
    url = SEARCH_URL_TEMPLATE.format(zip=zip_code)
    try:
        html = _get_page(url)
        page_json = _extract_json_from_html(html)
        # Navigate probable paths to find the list of properties
        # Zillow JSON structure varies; attempt multiple common paths
        props = []
        # Path 1
        try:
            props = page_json.get("cat1", {}).get("searchResults", {}).get("listResults", [])
        except Exception:
            props = []
        # Path 2 (alternate)
        if not props:
            try:
                props = page_json.get("searchResults", {}).get("listResults", [])
            except Exception:
                props = []
        for p in props:
            # Map common fields; be permissive
            listings.append({
                "address": p.get("address") or p.get("unformattedAddress") or p.get("streetAddress"),
                "rent": _safe_int(p.get("price")),
                "sqft": _safe_int(p.get("area")),
                "bedrooms": _safe_int(p.get("beds")),
                "bathrooms": _safe_float(p.get("baths")),
                "unit_type": _derive_unit_type(p),
                "time_on_market": p.get("hdpData", {}).get("homeInfo", {}).get("daysOnZillow") and f"Listed {p['hdpData']['homeInfo']['daysOnZillow']} days ago" or p.get("detailUrl", "N/A"),
                "parking": _extract_parking(p),
                "laundry_in_unit": _extract_laundry(p),
                "photos": p.get("imgSrc") and [p.get("imgSrc")] or p.get("images") or [],
                "url": "https://www.zillow.com" + p.get("detailUrl") if p.get("detailUrl", "").startswith("/") else p.get("detailUrl"),
                "zip": zip_code,
                "zpid": p.get("zpid")
            })
    except Exception as e:
        # Propagate an indicator to caller by raising or returning empty; here return empty to let caller use fallback
        raise RuntimeError(f"Zillow fetch failed: {e}")

    return listings

def _safe_int(v):
    try:
        if v is None:
            return None
        return int(str(v).replace("$","").replace(",","").replace("+","").split()[0])
    except Exception:
        return None

def _safe_float(v):
    try:
        if v is None:
            return None
        return float(str(v))
    except Exception:
        return None

def _derive_unit_type(p):
    # Try to deduce 2B2B / 2B1B from beds/baths
    beds = _safe_int(p.get("beds") or p.get("bedrooms") or p.get("bed"))
    baths = _safe_float(p.get("baths") or p.get("bathrooms") or p.get("bath"))
    if beds == 2 and baths and float(baths) >= 2.0:
        return "2B2B"
    if beds == 2 and baths and float(baths) >= 1.0:
        return "2B1B"
    return f"{beds}B{int(baths) if baths else 'N/A'}"

def _extract_parking(p):
    # multiple locations: description, buildingInfo, homeInfo
    desc = (p.get("description") or "") + " " + json.dumps(p)
    if "parking" in desc.lower():
        # return snippet with parking
        m = re.search(r'parking[:\s\-]*([^\n.,;]+)', desc, re.I)
        if m:
            return m.group(1).strip()
        return "Parking info in description"
    # Zillow sometimes has parking info in homeInfo
    try:
        hi = p.get("hdpData", {}).get("homeInfo", {})
        if "parking" in hi:
            return hi.get("parking")
    except Exception:
        pass
    return "N/A"

def _extract_laundry(p):
    # Look for laundry in keywords / description / homeInfo
    desc = (p.get("description") or "") + " " + json.dumps(p)
    if re.search(r'in[-\s]*unit laundry|in-unit laundry|laundry in unit|washer dryer', desc, re.I):
        return True
    # homeInfo
    try:
        hi = p.get("hdpData", {}).get("homeInfo", {})
        if hi.get("laundry", ""):
            return "in unit" in hi.get("laundry", "").lower()
    except Exception:
        pass
    return False
