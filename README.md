# house-hunting

Streamlit-based personal rental finder (SFO / Peninsula).  
Search by ZIP codes, budget, in-unit laundry and parking. Uses Zillow as primary data source; fallback data provided for demo.

## Files
- `app.py` - Main Streamlit app
- `utils/zillow_fetcher.py` - Zillow fetch + parse logic
- `utils/filters.py` - Filtering helpers
- `utils/ui_components.py` - Listing card renderer
- `fallback_listings.json` - Demo data used when Zillow fetch fails

## Local run
1. Create and activate a Python 3.10+ venv.
2. Install dependencies:
