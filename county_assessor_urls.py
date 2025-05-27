"""
Simple and reliable property tax lookup via Google Search.
This approach is:
1. Always up-to-date
2. Works for all counties
3. Zero maintenance
4. Free and reliable
"""

from typing import Optional
import urllib.parse

def get_county_url(county: str, state: str, address: str = "") -> str:
    """Generate a Google search URL for county property tax records.
    
    Args:
        county: County name
        state: Two-letter state code
        address: Property address (optional)
    
    Returns:
        Google search URL with relevant search terms
    """
    # Remove 'county' from the name if present
    county = county.lower().replace(' county', '').strip()
    state = state.upper()
    
    # Build search terms based on available info
    search_terms = []
    
    # If we have an address, make it the primary search term
    if address:
        # Clean up address
        address = address.replace(',', '')
        search_terms.append(f'"{address}"')
    
    # Add county and state with property tax terms
    search_terms.extend([
        f"{county} county",
        state,
        "property tax",
        "assessor",
        "property search",
        "parcel lookup"
    ])
    
    # Combine terms and encode for URL
    search_query = ' '.join(search_terms)
    encoded_query = urllib.parse.quote(search_query)
    
    # Add search refinements to prioritize government sites
    return f"https://www.google.com/search?q={encoded_query}+site:.gov+OR+site:.us"

def get_state_url(state: str) -> str:
    """Generate a Google search URL for state-level property tax info."""
    state = state.upper()
    search_query = urllib.parse.quote(f"{state} state property tax assessor database site:.gov")
    return f"https://www.google.com/search?q={search_query}"
