"""
Optimized property tax search using targeted Google queries.
"""

import urllib.parse
from typing import Optional

def format_address(address: str) -> str:
    """Format address for optimal searching."""
    # Remove common address suffixes and prefixes
    suffixes = ['apt', 'unit', '#', 'suite', 'ste']
    parts = address.lower().split()
    
    # Keep only the main address parts
    cleaned_parts = []
    skip_next = False
    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
            
        # Skip if it's a suffix or the next part should be skipped
        if any(part.startswith(suffix) for suffix in suffixes):
            skip_next = True
            continue
            
        cleaned_parts.append(part)
    
    return ' '.join(cleaned_parts)

def get_county_url(county: str, state: str, address: str = "") -> str:
    """Generate an optimized Google search URL for property tax information.
    
    Args:
        county: County name
        state: Two-letter state code
        address: Property address
    
    Returns:
        Google search URL optimized for finding property tax records
    """
    # Clean up inputs
    county = county.lower().strip().replace(" county", "")
    state = state.upper().strip()
    
    # Build search terms in order of importance
    search_terms = []
    
    if address:
        # Format address for search
        formatted_address = format_address(address)
        search_terms.append(f'"{formatted_address}"')  # Exact match for address
    
    # Add county and state (in quotes to keep them together)
    search_terms.append(f'"{county} county {state}"')
    
    # Add search refinements in order of importance
    search_terms.extend([
        "property tax",
        "assessor",
        "property search",
        "parcel",
        # Restrict to government sites and educational institutions
        "(site:.gov OR site:.us)",
        # Exclude common irrelevant results
        "-zillow.com",
        "-realtor.com",
        "-trulia.com"
    ])
    
    # Join all terms
    search_query = ' '.join(search_terms)
    return f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"

def get_state_url(state: str) -> str:
    """Generate an optimized Google search URL for state-level tax information."""
    state = state.upper().strip()
    
    # Build targeted state-level search
    search_terms = [
        f'"{state} state"',
        "property tax",
        "department of revenue",
        "assessor",
        "(site:.gov OR site:.us)",
        "-zillow.com",
        "-realtor.com"
    ]
    
    search_query = ' '.join(search_terms)
    return f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
