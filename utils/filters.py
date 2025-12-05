# utils/filters.py
from typing import List, Dict

def filter_by_zip(listings: List[Dict], selected_zips: List[str]) -> List[Dict]:
    if not selected_zips:
        return listings
    return [l for l in listings if str(l.get("zip", "")).strip() in selected_zips]

def filter_by_budget(listings: List[Dict], min_price: int, max_price: int) -> List[Dict]:
    return [l for l in listings if (l.get("rent") is not None and min_price <= l.get("rent") <= max_price)]

def filter_by_laundry(listings: List[Dict], require_laundry: bool) -> List[Dict]:
    if not require_laundry:
        return listings
    return [l for l in listings if l.get("laundry_in_unit")]

def filter_by_parking(listings: List[Dict], require_parking: bool) -> List[Dict]:
    if not require_parking:
        return listings
    return [l for l in listings if l.get("parking") and l.get("parking") != "N/A"]
