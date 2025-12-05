# utils/ui_components.py
import streamlit as st

def listing_card(listing: dict):
    st.markdown("---")
    header = f"**{listing.get('address', 'N/A')} — ${listing.get('rent', 'N/A')}**"
    st.markdown(header)
    cols = st.columns([1,2])
    with cols[0]:
        photos = listing.get("photos", [])
        if photos:
            # show first photo as thumbnail; clicking will not open full gallery automatically,
            # but we render all photos below to meet "show all photos" requirement
            st.image(photos[0], use_column_width=True)
        else:
            st.write("Image unavailable")
    with cols[1]:
        st.write(f"**Type:** {listing.get('unit_type', 'N/A')}")
        st.write(f"**Sqft:** {listing.get('sqft', 'N/A')}")
        st.write(f"**Beds/Baths:** {listing.get('bedrooms', 'N/A')} / {listing.get('bathrooms', 'N/A')}")
        st.write(f"**Time on market:** {listing.get('time_on_market', 'N/A')}")
        st.write(f"**Parking:** {listing.get('parking', 'N/A')}")
        st.write(f"**In-unit laundry:** {listing.get('laundry_in_unit', 'N/A')}")
        st.write(f"**Zip:** {listing.get('zip', 'N/A')}")
        url = listing.get("url")
        if url:
            st.markdown(f"[View original listing]({url})")
    # show all photos below card
    photos = listing.get("photos", [])
    if photos:
        st.write("Photos:")
        for p in photos:
            try:
                st.image(p, use_column_width=True)
            except Exception:
                st.write("Image unavailable")
