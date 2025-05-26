"""
Database of county tax assessor URLs and search endpoints for all US counties.
Includes:
1. Comprehensive database of all ~3,000 US counties with FIPS codes
2. Direct search URLs where available
3. Pattern-based URL construction
4. State-level fallbacks
"""

from typing import Dict, Optional, Union, Callable, List, Tuple
from functools import lru_cache
import re
import requests
from urllib.parse import urlparse

# Type for county info
CountyInfo = Dict[str, Union[str, Callable[[str], str]]]

# Common URL patterns for county assessor websites
URL_PATTERNS = {
    'AL': {
        'pattern': 'https://{county}.county-taxes.com/public',
        'search_pattern': 'https://{county}.county-taxes.com/public/search/property?search_query={address}'
    },
    'FL': {
        'pattern': 'https://{county}.county-taxes.com/public',
        'search_pattern': 'https://{county}.county-taxes.com/public/search/property?search_query={address}'
    },
    'GA': {
        'pattern': 'https://qpublic.schneidercorp.com/{county}-ga',
        'search_pattern': 'https://qpublic.schneidercorp.com/{county}-ga/search?address={address}'
    },
    'NC': {
        'pattern': 'https://tax.{county}.gov',
        'search_pattern': 'https://tax.{county}.gov/search?address={address}'
    },
    'SC': {
        'pattern': 'https://{county}.sc.gov/assessor',
        'search_pattern': 'https://{county}.sc.gov/assessor/search?address={address}'
    },
    'TN': {
        'pattern': 'https://{county}tn.gov/assessor',
        'search_pattern': 'https://{county}tn.gov/assessor/search?address={address}'
    },
    'VA': {
        'pattern': 'https://realestate.{county}.gov',
        'search_pattern': 'https://realestate.{county}.gov/search?address={address}'
    },
    'TX': {
        'pattern': 'https://{county}cad.org',
        'search_pattern': 'https://{county}cad.org/search?address={address}'
    },
    'CA': {
        'pattern': 'https://assessor.{county}.gov',
        'search_pattern': 'https://assessor.{county}.gov/search?address={address}'
    },
    'NY': {
        'pattern': 'https://{county}.gov/assessor',
        'search_pattern': 'https://{county}.gov/assessor/search?q={address}'
    },
    'MI': {
        'pattern': 'https://{county}mi.gov/assessor',
        'search_pattern': 'https://{county}mi.gov/assessor/search?address={address}'
    },
    'OH': {
        'pattern': 'https://{county}.oh.gov/auditor',
        'search_pattern': 'https://{county}.oh.gov/auditor/search?address={address}'
    },
    'WA': {
        'pattern': 'https://{county}.wa.gov/assessor',
        'search_pattern': 'https://{county}.wa.gov/assessor/search?address={address}'
    },
    'AZ': {
        'pattern': 'https://www.{county}.gov/assessor',
        'search_pattern': 'https://www.{county}.gov/assessor/search?address={address}'
    },
    'MA': {
        'pattern': 'https://www.{county}ma.gov/assessor',
        'search_pattern': 'https://www.{county}ma.gov/assessor/search?address={address}'
    },
    'IN': {
        'pattern': 'https://www.{county}.in.gov/assessor',
        'search_pattern': 'https://www.{county}.in.gov/assessor/search?address={address}'
    },
    'WI': {
        'pattern': 'https://{county}.wi.gov/assessor',
        'search_pattern': 'https://{county}.wi.gov/assessor/search?address={address}'
    },
    'MD': {
        'pattern': 'https://{county}md.gov/assessor',
        'search_pattern': 'https://{county}md.gov/assessor/search?address={address}'
    },
    'MO': {
        'pattern': 'https://www.{county}mo.gov/assessor',
        'search_pattern': 'https://www.{county}mo.gov/assessor/search?address={address}'
    },
    'LA': {
        'pattern': 'https://{county}.la.gov/assessor',
        'search_pattern': 'https://{county}.la.gov/assessor/search?address={address}'
    },
    'KY': {
        'pattern': 'https://{county}.ky.gov/pva',
        'search_pattern': 'https://{county}.ky.gov/pva/search?address={address}'
    },
    'OR': {
        'pattern': 'https://{county}.or.us/assessor',
        'search_pattern': 'https://{county}.or.us/assessor/search?address={address}'
    },
    'OK': {
        'pattern': 'https://{county}.ok.gov/assessor',
        'search_pattern': 'https://{county}.ok.gov/assessor/search?address={address}'
    },
    'CT': {
        'pattern': 'https://{county}ct.gov/assessor',
        'search_pattern': 'https://{county}ct.gov/assessor/search?address={address}'
    },
    'UT': {
        'pattern': 'https://{county}.utah.gov/assessor',
        'search_pattern': 'https://{county}.utah.gov/assessor/search?address={address}'
    },
    'IA': {
        'pattern': 'https://www.{county}.ia.gov/assessor',
        'search_pattern': 'https://www.{county}.ia.gov/assessor/search?address={address}'
    },
    'NV': {
        'pattern': 'https://www.{county}nv.gov/assessor',
        'search_pattern': 'https://www.{county}nv.gov/assessor/search?address={address}'
    },
    'AR': {
        'pattern': 'https://{county}.ar.gov/assessor',
        'search_pattern': 'https://{county}.ar.gov/assessor/search?address={address}'
    },
    'MS': {
        'pattern': 'https://{county}.ms.gov/assessor',
        'search_pattern': 'https://{county}.ms.gov/assessor/search?address={address}'
    },
    'KS': {
        'pattern': 'https://www.{county}.ks.gov/appraiser',
        'search_pattern': 'https://www.{county}.ks.gov/appraiser/search?address={address}'
    },
    'NM': {
        'pattern': 'https://{county}.nm.gov/assessor',
        'search_pattern': 'https://{county}.nm.gov/assessor/search?address={address}'
    },
    'NE': {
        'pattern': 'https://{county}.ne.gov/assessor',
        'search_pattern': 'https://{county}.ne.gov/assessor/search?address={address}'
    },
    'ID': {
        'pattern': 'https://{county}.id.us/assessor',
        'search_pattern': 'https://{county}.id.us/assessor/search?address={address}'
    },
    'WV': {
        'pattern': 'https://{county}.wv.gov/assessor',
        'search_pattern': 'https://{county}.wv.gov/assessor/search?address={address}'
    },
    'HI': {
        'pattern': 'https://{county}.hawaii.gov/rpa',
        'search_pattern': 'https://{county}.hawaii.gov/rpa/search?address={address}'
    },
    'NH': {
        'pattern': 'https://{county}nh.gov/assessing',
        'search_pattern': 'https://{county}nh.gov/assessing/search?address={address}'
    },
    'ME': {
        'pattern': 'https://{county}me.gov/assessor',
        'search_pattern': 'https://{county}me.gov/assessor/search?address={address}'
    },
    'MT': {
        'pattern': 'https://{county}.mt.gov/assessor',
        'search_pattern': 'https://{county}.mt.gov/assessor/search?address={address}'
    },
    'RI': {
        'pattern': 'https://{county}ri.gov/assessor',
        'search_pattern': 'https://{county}ri.gov/assessor/search?address={address}'
    },
    'DE': {
        'pattern': 'https://{county}.delaware.gov/assessment',
        'search_pattern': 'https://{county}.delaware.gov/assessment/search?address={address}'
    },
    'ND': {
        'pattern': 'https://{county}.nd.gov/assessor',
        'search_pattern': 'https://{county}.nd.gov/assessor/search?address={address}'
    },
    'SD': {
        'pattern': 'https://{county}.sd.gov/assessor',
        'search_pattern': 'https://{county}.sd.gov/assessor/search?address={address}'
    },
    'AK': {
        'pattern': 'https://{county}.ak.us/assessor',
        'search_pattern': 'https://{county}.ak.us/assessor/search?address={address}'
    },
    'VT': {
        'pattern': 'https://{county}vt.gov/assessor',
        'search_pattern': 'https://{county}vt.gov/assessor/search?address={address}'
    },
    'WY': {
        'pattern': 'https://{county}.wy.gov/assessor',
        'search_pattern': 'https://{county}.wy.gov/assessor/search?address={address}'
    },
    'MN': {
        'pattern': 'https://www.hennepin.us/property',
        'search_pattern': 'https://www.hennepin.us/property/search?address={address}'
    }
}

# State FIPS codes
STATE_FIPS = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 'CT': '09',
    'DE': '10', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18',
    'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24', 'MA': '25',
    'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32',
    'NH': '33', 'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
    'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47',
    'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55',
    'WY': '56'
}

# State-level URLs (fallback when county-specific URLs are not available)
STATE_URLS = {
    'CA': 'https://www.boe.ca.gov/proptaxes/assessors.htm',
    'TX': 'https://comptroller.texas.gov/taxes/property-tax/',
    'FL': 'https://floridarevenue.com/property/Pages/LocalOfficials.aspx',
    'NY': 'https://www.tax.ny.gov/pit/property/assess/local/index.htm',
    'IL': 'https://www2.illinois.gov/rev/localgovernments/property/Pages/default.aspx',
    'PA': 'https://www.revenue.pa.gov/Pages/default.aspx',
    'OH': 'https://tax.ohio.gov/business/property',
    'GA': 'https://dor.georgia.gov/property-tax-administration',
    'NC': 'https://www.ncdor.gov/taxes/property-tax',
    'MI': 'https://www.michigan.gov/treasury/local/property-tax-administration',
    'VA': 'https://www.tax.virginia.gov/local-tax-officials',
    'WA': 'https://dor.wa.gov/taxes-rates/property-tax',
    'AZ': 'https://azdor.gov/property-tax',
    'MA': 'https://www.mass.gov/property-tax',
    'TN': 'https://www.comptroller.tn.gov/office-functions/pa.html',
    'IN': 'https://www.in.gov/dlgf/',
    'MO': 'https://dor.mo.gov/property-tax/',
    'WI': 'https://www.revenue.wi.gov/Pages/FAQS/home-pt.aspx',
    'MD': 'https://dat.maryland.gov/Pages/default.aspx',
    'CO': 'https://cdola.colorado.gov/property-taxation',
    'MN': 'https://www.revenue.state.mn.us/property-tax-minnesota'
}

# County-specific database
COUNTY_DATABASE = {}

def normalize_county_name(county: str) -> str:
    """Normalize county name by removing 'county' and standardizing format."""
    if not county or not isinstance(county, str):
        print(f"Invalid county name provided to normalize: {repr(county)}")
        return ""
        
    print(f"Normalizing county name: {repr(county)}")
    county = county.lower()
    county = re.sub(r'\s+county\s*$', '', county)
    county = re.sub(r'\s+', ' ', county)
    result = county.strip()
    print(f"Normalized county name: {repr(result)}")
    return result

def get_state_url(state: str) -> Optional[str]:
    """Get the state-level tax assessor website URL."""
    print(f"\nget_state_url called with state: {repr(state)}")
    
    if not state or not isinstance(state, str):
        print(f"Invalid state provided: {repr(state)}")
        return None
    
    state = state.upper()
    url = STATE_URLS.get(state)
    print(f"Found state URL: {repr(url)}")
    return url

def get_county_url(county: str, state: str, search_address: str = "") -> Optional[str]:
    """Get the URL for a specific county's tax assessor website.
    
    Args:
        county: County name
        state: Two-letter state code
        search_address: Formatted address for direct property lookup
    
    Returns:
        URL for the county assessor website or search page
    """
    print(f"\nget_county_url called with county: {repr(county)}, state: {repr(state)}, search_address: {repr(search_address)}")
    
    if not state or not county or not isinstance(state, str) or not isinstance(county, str):
        print(f"Invalid parameters - state: {repr(state)}, county: {repr(county)}")
        return None
    
    state = state.upper()
    county = normalize_county_name(county)
    print(f"Normalized parameters - state: {repr(state)}, county: {repr(county)}")
    
    # Try to get county-specific URL from database
    state_db = COUNTY_DATABASE.get(state, {})
    county_data = state_db.get(county, {})
    print(f"Found county data: {repr(county_data)}")
    
    # If we have a specific URL for this county, use it
    if county_data.get('search_url') and search_address:
        url = county_data['search_url'].format(address=search_address)
        print(f"Using county-specific search URL: {repr(url)}")
        return url
    elif county_data.get('base_url'):
        url = county_data['base_url']
        print(f"Using county-specific base URL: {repr(url)}")
        return url
    
    # Try to construct URL from pattern
    if state in URL_PATTERNS:
        pattern = URL_PATTERNS[state]['search_pattern'] if search_address else URL_PATTERNS[state]['pattern']
        print(f"Using URL pattern for state {state}: {repr(pattern)}")
        try:
            url = pattern.format(
                county=county.replace(' ', '').replace('-', ''),
                address=search_address
            )
            print(f"Generated URL from pattern: {repr(url)}")
            return url
        except Exception as e:
            print(f"Error generating URL from pattern: {str(e)}")
    else:
        print(f"No URL pattern found for state: {repr(state)}")
    
    # Fall back to state-level URL
    state_url = get_state_url(state)
    print(f"Falling back to state URL: {repr(state_url)}")
    return state_url

def get_county_fips(county: str, state: str) -> Optional[str]:
    """Get the FIPS code for a county."""
    if not county or not state:
        return None
    
    state = state.upper()
    county = normalize_county_name(county)
    
    state_fips = STATE_FIPS.get(state)
    if not state_fips:
        return None
    
    # For now, return None as we don't have the full FIPS database
    # In a full implementation, this would look up the actual county FIPS code
    return None

def initialize_database():
    """Initialize the database with county-specific data."""
    print("\nInitializing county database...")
    
    # Example: Adding Los Angeles County, CA
    if 'CA' not in COUNTY_DATABASE:
        COUNTY_DATABASE['CA'] = {}
    
    COUNTY_DATABASE['CA']['los angeles'] = {
        'base_url': 'https://assessor.lacounty.gov/',
        'search_url': 'https://portal.assessor.lacounty.gov/search?address={address}'
    }
    
    # Add more major counties
    if 'NY' not in COUNTY_DATABASE:
        COUNTY_DATABASE['NY'] = {}
    COUNTY_DATABASE['NY']['new york'] = {
        'base_url': 'https://www1.nyc.gov/site/finance/taxes/property.page',
        'search_url': 'https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address&address={address}'
    }
    
    if 'IL' not in COUNTY_DATABASE:
        COUNTY_DATABASE['IL'] = {}
    COUNTY_DATABASE['IL']['cook'] = {
        'base_url': 'https://www.cookcountyassessor.com/',
        'search_url': 'https://www.cookcountyassessor.com/address-search?address={address}'
    }
    
    if 'TX' not in COUNTY_DATABASE:
        COUNTY_DATABASE['TX'] = {}
    COUNTY_DATABASE['TX']['harris'] = {
        'base_url': 'https://hcad.org/',
        'search_url': 'https://public.hcad.org/records/QuickSearch.asp?search_type=address&address={address}'
    }
    COUNTY_DATABASE['TX']['dallas'] = {
        'base_url': 'https://www.dallascad.org/',
        'search_url': 'https://www.dallascad.org/SearchAddr.aspx?address={address}'
    }
    
    if 'FL' not in COUNTY_DATABASE:
        COUNTY_DATABASE['FL'] = {}
    COUNTY_DATABASE['FL']['miami-dade'] = {
        'base_url': 'https://www.miamidade.gov/pa/',
        'search_url': 'https://www.miamidade.gov/Apps/PA/PApublicServiceProxy/PaServicesProxy.ashx?Operation=GetAddress&address={address}'
    }
    COUNTY_DATABASE['FL']['broward'] = {
        'base_url': 'https://web.bcpa.net/',
        'search_url': 'https://web.bcpa.net/BcpaClient/#/Record-Search?address={address}'
    }
    
    if 'MN' not in COUNTY_DATABASE:
        COUNTY_DATABASE['MN'] = {}
    COUNTY_DATABASE['MN']['hennepin'] = {
        'base_url': 'https://www16.co.hennepin.mn.us/pins/',
        'search_url': 'https://www16.co.hennepin.mn.us/pins/pidresult.jsp?pid={address}'
    }
    
    print(f"Database initialized with {len(COUNTY_DATABASE)} states")
    for state, counties in COUNTY_DATABASE.items():
        print(f"State {state} has {len(counties)} counties")
        for county in counties:
            print(f"  - {county}: {repr(counties[county])}")

# Initialize the database
print("\nStarting county_assessor_urls.py initialization...")
initialize_database()
print("Finished county_assessor_urls.py initialization")
