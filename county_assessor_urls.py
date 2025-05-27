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
    
    # Always include county and state
    search_terms.append(f"{county} county {state}")
    
    # Add property-specific terms
    search_terms.extend([
        "property tax",
        "assessor",
        "property search"
    ])
    
    # Add address if provided
    if address:
        # Clean up address
        address = address.replace(',', '')
        search_terms.append(f'"{address}"')
    
    # Combine terms and encode for URL
    search_query = ' '.join(search_terms)
    encoded_query = urllib.parse.quote(search_query)
    
    return f"https://www.google.com/search?q={encoded_query}"

def get_state_url(state: str) -> str:
    """Generate a Google search URL for state-level property tax info."""
    state = state.upper()
    search_query = urllib.parse.quote(f"{state} state property tax assessor database")
    return f"https://www.google.com/search?q={search_query}"
