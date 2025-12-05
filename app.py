# app.py
import streamlit as st
import json
import os
from utils.zillow_fetcher import fetch_listings_by_zip
from utils.filters import filter_by_zip, filter_by_budget, filter_by_laundry, filter_by_parking
from utils.ui_components import listing_card

# Paths
FALLBACK_PATH = "fallback_listings.json"

st.set_page_config(page_title="House Hunting", layout="wide")

st.sidebar.title("House Hunting - Filters")

# Budget
min_budget, max_budget = st.sidebar.slider("Monthly budget", 2600, 3600, (2600, 3600), step=50)

# Zip codes: user can input comma separated or multi select.
default_zips = ["94005","94014","94015","94112","94080"]
selected_zips = st.sidebar.multiselect("Zip codes (multi-select)", default_zips, default=default_zips)

# Laundry & Parking
require_laundry = st.sidebar.checkbox("Require in-unit laundry", value=True)
require_parking = st.sidebar.checkbox("Require parking info", value=True)

st.sidebar.markdown("---")
st.sidebar.write("Data source: Zillow (primary). If Zillow blocking occurs the app will use fallback data for demo.")

fetch_button = st.sidebar.button("Fetch listings")

# initial state
if 'raw_listings_count' not in st.session_state:
    st.session_state['raw_listings_count'] = 0

def load_fallback():
    if os.path.exists(FALLBACK_PATH):
        with open(FALLBACK_PATH, "r") as f:
            return json.load(f)
    return []

listings = []
error_msg = None

if fetch_button:
    # iterate zips and fetch
    all_raw = []
    for z in selected_zips:
        try:
            raw = fetch_listings_by_zip(z)
            all_raw.extend(raw)
        except Exception as e:
            # log and break to use fallback
            st.error(f"Zillow fetch failed for zip {z}: {e}")
            st.warning("Using fallback data")
            all_raw = load_fallback()
            break

    st.session_state['raw_listings_count'] = len(all_raw)

    # Apply filters
    filtered = filter_by_zip(all_raw, selected_zips)
    filtered = filter_by_budget(filtered, min_budget, max_budget)
    filtered = filter_by_laundry(filtered, require_laundry)
    filtered = filter_by_parking(filtered, require_parking)

    listings = filtered

    st.success(f"Fetched {st.session_state['raw_listings_count']} raw listings; {len(listings)} matched after filtering.")

else:
    st.info("Click 'Fetch listings' in the sidebar to start. You can also adjust filters before fetching.")
    # show fallback preview so UI isn't empty
    listings = load_fallback()
    if listings:
        st.warning("Showing fallback demo data. Click 'Fetch listings' to query Zillow.")

# Controls: sort
sort_option = st.selectbox("Sort by", ["Recommended", "Price: low to high", "Price: high to low", "Newest first"])

if sort_option == "Price: low to high":
    listings = sorted(listings, key=lambda x: x.get("rent") or 1e9)
elif sort_option == "Price: high to low":
    listings = sorted(listings, key=lambda x: -(x.get("rent") or 0))
# Note: "Newest first" requires time_on_market parsing; left as-is for MVP

# Result count and export
st.write(f"Showing {len(listings)} listings")
if listings:
    if st.button("Export results to CSV"):
        import pandas as pd
        df = pd.DataFrame(listings)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="house_hunting_results.csv", mime="text/csv")

# Render listing cards
for l in listings:
    listing_card(l)
