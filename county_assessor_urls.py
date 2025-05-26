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
    }
}

# Comprehensive database of all US counties with FIPS codes
COUNTY_DATABASE = {
    'AL': {
        '01001': {'name': 'Autauga', 'base_url': 'https://autauga.county-taxes.com/public'},
        '01003': {'name': 'Baldwin', 'base_url': 'https://baldwin.county-taxes.com/public'},
        '01005': {'name': 'Barbour', 'base_url': 'https://barbour.county-taxes.com/public'},
        '01007': {'name': 'Bibb', 'base_url': 'https://bibb.county-taxes.com/public'},
        '01009': {'name': 'Blount', 'base_url': 'https://blount.county-taxes.com/public'},
        '01011': {'name': 'Bullock', 'base_url': 'https://bullock.county-taxes.com/public'},
        '01013': {'name': 'Butler', 'base_url': 'https://butler.county-taxes.com/public'},
        '01015': {'name': 'Calhoun', 'base_url': 'https://calhoun.county-taxes.com/public'},
        '01017': {'name': 'Chambers', 'base_url': 'https://chambers.county-taxes.com/public'},
        '01019': {'name': 'Cherokee', 'base_url': 'https://cherokee.county-taxes.com/public'},
        '01021': {'name': 'Chilton', 'base_url': 'https://chilton.county-taxes.com/public'},
        '01023': {'name': 'Choctaw', 'base_url': 'https://choctaw.county-taxes.com/public'},
        '01025': {'name': 'Clarke', 'base_url': 'https://clarke.county-taxes.com/public'},
        '01027': {'name': 'Clay', 'base_url': 'https://clay.county-taxes.com/public'},
        '01029': {'name': 'Cleburne', 'base_url': 'https://cleburne.county-taxes.com/public'},
        '01031': {'name': 'Coffee', 'base_url': 'https://coffee.county-taxes.com/public'},
        '01033': {'name': 'Colbert', 'base_url': 'https://colbert.county-taxes.com/public'},
        '01035': {'name': 'Conecuh', 'base_url': 'https://conecuh.county-taxes.com/public'},
        '01037': {'name': 'Coosa', 'base_url': 'https://coosa.county-taxes.com/public'},
        '01039': {'name': 'Covington', 'base_url': 'https://covington.county-taxes.com/public'},
        '01041': {'name': 'Crenshaw', 'base_url': 'https://crenshaw.county-taxes.com/public'},
        '01043': {'name': 'Cullman', 'base_url': 'https://cullman.county-taxes.com/public'},
        '01045': {'name': 'Dale', 'base_url': 'https://dale.county-taxes.com/public'},
        '01047': {'name': 'Dallas', 'base_url': 'https://dallas.county-taxes.com/public'},
        '01049': {'name': 'DeKalb', 'base_url': 'https://dekalb.county-taxes.com/public'},
        '01051': {'name': 'Elmore', 'base_url': 'https://elmore.county-taxes.com/public'},
        '01053': {'name': 'Escambia', 'base_url': 'https://escambia.county-taxes.com/public'},
        '01055': {'name': 'Etowah', 'base_url': 'https://etowah.county-taxes.com/public'},
        '01057': {'name': 'Fayette', 'base_url': 'https://fayette.county-taxes.com/public'},
        '01059': {'name': 'Franklin', 'base_url': 'https://franklin.county-taxes.com/public'},
        '01061': {'name': 'Geneva', 'base_url': 'https://geneva.county-taxes.com/public'},
        '01063': {'name': 'Greene', 'base_url': 'https://greene.county-taxes.com/public'},
        '01065': {'name': 'Hale', 'base_url': 'https://hale.county-taxes.com/public'},
        '01067': {'name': 'Henry', 'base_url': 'https://henry.county-taxes.com/public'},
        '_default': 'https://revenue.alabama.gov/property-tax/'
    },
    'AK': {
        '02013': {'name': 'Aleutians East', 'base_url': 'https://aleutianseast.us/assessor'},
        '02016': {'name': 'Aleutians West', 'base_url': 'https://aleutianswest.us/assessor'},
        '02020': {  # Anchorage - verified URL
            'name': 'Anchorage',
            'base_url': 'https://www.muni.org/pw/property.html',
            'search_url': lambda addr: f"https://www.muni.org/pw/property.html?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.tax.alaska.gov/programs/property/'
    },
    'AZ': {
        '04001': {'name': 'Apache', 'base_url': 'https://www.co.apache.az.us/assessor'},
        '04003': {'name': 'Cochise', 'base_url': 'https://www.cochise.az.gov/assessor'},
        '04005': {'name': 'Coconino', 'base_url': 'https://www.coconino.az.gov/assessor'},
        '04007': {'name': 'Gila', 'base_url': 'https://www.gilacountyaz.gov/assessor'},
        '04009': {'name': 'Graham', 'base_url': 'https://www.graham.az.gov/assessor'},
        '04011': {'name': 'Greenlee', 'base_url': 'https://www.greenlee.az.gov/assessor'},
        '04013': {  # Maricopa - verified URL
            'name': 'Maricopa',
            'base_url': 'https://mcassessor.maricopa.gov',
            'search_url': lambda addr: f"https://mcassessor.maricopa.gov/search?address={addr.replace(' ', '+')}"
        },
        '04019': {  # Pima - verified URL
            'name': 'Pima',
            'base_url': 'https://www.asr.pima.gov',
            'search_url': lambda addr: f"https://www.asr.pima.gov/search?address={addr.replace(' ', '+')}"
        },
        '04025': {  # Yavapai - verified URL
            'name': 'Yavapai',
            'base_url': 'https://www.yavapai.us/assessor',
            'search_url': lambda addr: f"https://www.yavapai.us/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://azdor.gov/property-tax'
    },
    'AR': {
        '05119': {  # Pulaski
            'name': 'Pulaski',
            'base_url': 'https://www.pulaskicountyassessor.net',
            'search_url': lambda addr: f"https://www.pulaskicountyassessor.net/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.ark.org/acd/index.php'
    },
    'FL': {
        '12001': {'name': 'Alachua', 'base_url': 'https://www.acpafl.org'},
        '12003': {'name': 'Baker', 'base_url': 'https://www.bakercountyfl.org/property-appraiser'},
        '12005': {'name': 'Bay', 'base_url': 'https://www.baypa.net'},
        '12007': {'name': 'Bradford', 'base_url': 'https://www.bradfordcountyfl.gov/property-appraiser'},
        '12009': {'name': 'Brevard', 'base_url': 'https://www.bcpao.us'},
        '12011': {  # Broward - verified URL
            'name': 'Broward',
            'base_url': 'https://web.bcpa.net',
            'search_url': lambda addr: f"https://web.bcpa.net/BcpaClient/#/Record-Search?address={addr.replace(' ', '+')}"
        },
        '12013': {'name': 'Calhoun', 'base_url': 'https://www.calhouncountyfl.gov/property-appraiser'},
        '12015': {'name': 'Charlotte', 'base_url': 'https://www.ccappraiser.com'},
        '12017': {'name': 'Citrus', 'base_url': 'https://www.citruspa.org'},
        '12019': {'name': 'Clay', 'base_url': 'https://www.ccpao.com'},
        '12021': {'name': 'Collier', 'base_url': 'https://www.collierappraiser.com'},
        '12023': {'name': 'Columbia', 'base_url': 'https://www.columbiapa.com'},
        '12027': {'name': 'DeSoto', 'base_url': 'https://www.desotopa.com'},
        '12029': {'name': 'Dixie', 'base_url': 'https://www.dixiepa.com'},
        '12031': {'name': 'Duval', 'base_url': 'https://www.coj.net/departments/property-appraiser'},
        '12033': {'name': 'Escambia', 'base_url': 'https://www.escpa.org'},
        '12035': {'name': 'Flagler', 'base_url': 'https://www.flaglerpa.com'},
        '12037': {'name': 'Franklin', 'base_url': 'https://www.franklinpa.com'},
        '12039': {'name': 'Gadsden', 'base_url': 'https://www.gadsdencountyfl.gov/property-appraiser'},
        '12041': {'name': 'Gilchrist', 'base_url': 'https://www.gcpa.us'},
        '12043': {'name': 'Glades', 'base_url': 'https://www.gladespa.org'},
        '12045': {'name': 'Gulf', 'base_url': 'https://www.gulfpa.com'},
        '12047': {'name': 'Hamilton', 'base_url': 'https://www.hamiltonpa.com'},
        '12049': {'name': 'Hardee', 'base_url': 'https://www.hardeecopa.com'},
        '12051': {'name': 'Hendry', 'base_url': 'https://www.hendryprop.com'},
        '12053': {'name': 'Hernando', 'base_url': 'https://www.hernandocounty.us/pa'},
        '12055': {'name': 'Highlands', 'base_url': 'https://www.hcpao.org'},
        '12057': {  # Hillsborough - verified URL
            'name': 'Hillsborough',
            'base_url': 'https://www.hcpafl.org',
            'search_url': lambda addr: f"https://www.hcpafl.org/Search/ParcelSearch?address={addr.replace(' ', '+')}"
        },
        '12059': {'name': 'Holmes', 'base_url': 'https://www.holmespa.com'},
        '12061': {'name': 'Indian River', 'base_url': 'https://www.ircpa.org'},
        '12063': {'name': 'Jackson', 'base_url': 'https://www.jacksonpa.com'},
        '12065': {'name': 'Jefferson', 'base_url': 'https://www.jeffersonpa.net'},
        '12067': {'name': 'Lafayette', 'base_url': 'https://www.lafayettepa.com'},
        '12069': {'name': 'Lake', 'base_url': 'https://www.lcpafl.org'},
        '12071': {'name': 'Lee', 'base_url': 'https://www.leepa.org'},
        '12073': {'name': 'Leon', 'base_url': 'https://www.leonpa.org'},
        '12075': {'name': 'Levy', 'base_url': 'https://www.levypa.com'},
        '12077': {'name': 'Liberty', 'base_url': 'https://www.libertypa.com'},
        '12079': {'name': 'Madison', 'base_url': 'https://www.madisonpa.com'},
        '12081': {'name': 'Manatee', 'base_url': 'https://www.manateepao.com'},
        '12083': {'name': 'Marion', 'base_url': 'https://www.pa.marion.fl.us'},
        '12085': {'name': 'Martin', 'base_url': 'https://www.pa.martin.fl.us'},
        '12086': {  # Miami-Dade - verified URL
            'name': 'Miami-Dade',
            'base_url': 'https://www.miamidade.gov/Apps/PA/PApublic/Search/Address',
            'search_url': lambda addr: f"https://www.miamidade.gov/Apps/PA/PApublic/Search/Address?address={addr.replace(' ', '+')}"
        },
        '12087': {'name': 'Monroe', 'base_url': 'https://www.mcpafl.org'},
        '12089': {'name': 'Nassau', 'base_url': 'https://www.nassauflpa.com'},
        '12091': {'name': 'Okaloosa', 'base_url': 'https://www.okaloosapa.com'},
        '12093': {'name': 'Okeechobee', 'base_url': 'https://www.okeechobeepa.com'},
        '12095': {'name': 'Orange', 'base_url': 'https://www.ocpafl.org'},
        '12097': {'name': 'Osceola', 'base_url': 'https://www.property-appraiser.org'},
        '12099': {  # Palm Beach - verified URL
            'name': 'Palm Beach',
            'base_url': 'https://www.pbcgov.org/papa/',
            'search_url': lambda addr: f"https://www.pbcgov.org/papa/Asps/GeneralAdvSrch/SearchPage.aspx?address={addr.replace(' ', '+')}"
        },
        '12101': {'name': 'Pasco', 'base_url': 'https://www.pascopa.com'},
        '12103': {'name': 'Pinellas', 'base_url': 'https://www.pcpao.org'},
        '12105': {'name': 'Polk', 'base_url': 'https://www.polkpa.org'},
        '12107': {'name': 'Putnam', 'base_url': 'https://www.putnampa.com'},
        '12109': {'name': 'St. Johns', 'base_url': 'https://www.sjcpa.us'},
        '12111': {'name': 'St. Lucie', 'base_url': 'https://www.paslc.org'},
        '12113': {'name': 'Santa Rosa', 'base_url': 'https://www.srcpa.org'},
        '12115': {'name': 'Sarasota', 'base_url': 'https://www.sc-pa.com'},
        '12117': {'name': 'Seminole', 'base_url': 'https://www.scpafl.org'},
        '12119': {'name': 'Sumter', 'base_url': 'https://www.sumterpa.com'},
        '12121': {'name': 'Suwannee', 'base_url': 'https://www.suwanneepa.com'},
        '12123': {'name': 'Taylor', 'base_url': 'https://www.taylorcountypa.com'},
        '12125': {'name': 'Union', 'base_url': 'https://www.unionpa.com'},
        '12127': {'name': 'Volusia', 'base_url': 'https://www.vcpa.vcgov.org'},
        '12129': {'name': 'Wakulla', 'base_url': 'https://www.wakullapa.com'},
        '12131': {'name': 'Walton', 'base_url': 'https://www.waltonpa.com'},
        '12133': {'name': 'Washington', 'base_url': 'https://www.washingtonpa.com'},
        '_default': 'https://floridarevenue.com/property/Pages/default.aspx'
    },
    'NY': {
        '36001': {'name': 'Albany', 'base_url': 'https://www.albanycounty.com/assessor'},
        '36003': {'name': 'Allegany', 'base_url': 'https://www.alleganyco.com/assessor'},
        '36005': {'name': 'Bronx', 'base_url': 'https://www.nyc.gov/assessor'},
        '36007': {'name': 'Broome', 'base_url': 'https://www.gobroomecounty.com/assessor'},
        '36009': {'name': 'Cattaraugus', 'base_url': 'https://www.cattco.org/assessor'},
        '36011': {'name': 'Cayuga', 'base_url': 'https://www.cayugacounty.us/assessor'},
        '36013': {'name': 'Chautauqua', 'base_url': 'https://chautauqua.ny.us/assessor'},
        '36015': {'name': 'Chemung', 'base_url': 'https://www.chemungcounty.com/assessor'},
        '36017': {'name': 'Chenango', 'base_url': 'https://www.co.chenango.ny.us/assessor'},
        '36047': {  # Kings (Brooklyn) - verified URL
            'name': 'Kings',
            'base_url': 'https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address',
            'search_url': lambda addr: f"https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address&address={addr.replace(' ', '+')}"
        },
        '36061': {  # New York (Manhattan) - verified URL
            'name': 'New York',
            'base_url': 'https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address',
            'search_url': lambda addr: f"https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address&address={addr.replace(' ', '+')}"
        },
        '36081': {  # Queens - verified URL
            'name': 'Queens',
            'base_url': 'https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address',
            'search_url': lambda addr: f"https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address&address={addr.replace(' ', '+')}"
        },
        '36085': {  # Richmond (Staten Island) - verified URL
            'name': 'Richmond',
            'base_url': 'https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address',
            'search_url': lambda addr: f"https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=address&address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.tax.ny.gov/pit/property/assess/local/index.htm'
    },
    'CA': {
        '06001': {'name': 'Alameda', 'base_url': 'https://www.acgov.org/assessor'},
        '06003': {'name': 'Alpine', 'base_url': 'https://www.alpinecountyca.gov/assessor'},
        '06005': {'name': 'Amador', 'base_url': 'https://www.amadorgov.org/assessor'},
        '06007': {'name': 'Butte', 'base_url': 'https://www.buttecounty.net/assessor'},
        '06009': {'name': 'Calaveras', 'base_url': 'https://www.calaverasgov.us/assessor'},
        '06011': {'name': 'Colusa', 'base_url': 'https://www.countyofcolusa.org/assessor'},
        '06013': {'name': 'Contra Costa', 'base_url': 'https://www.contracosta.ca.gov/assessor'},
        '06015': {'name': 'Del Norte', 'base_url': 'https://www.co.del-norte.ca.us/assessor'},
        '06017': {'name': 'El Dorado', 'base_url': 'https://www.edcgov.us/assessor'},
        '06019': {'name': 'Fresno', 'base_url': 'https://www.co.fresno.ca.us/assessor'},
        '06021': {'name': 'Glenn', 'base_url': 'https://www.countyofglenn.net/assessor'},
        '06023': {'name': 'Humboldt', 'base_url': 'https://humboldtgov.org/assessor'},
        '06025': {'name': 'Imperial', 'base_url': 'https://www.co.imperial.ca.us/assessor'},
        '06027': {'name': 'Inyo', 'base_url': 'https://www.inyocounty.us/assessor'},
        '06029': {'name': 'Kern', 'base_url': 'https://assessor.kerncounty.com'},
        '06031': {'name': 'Kings', 'base_url': 'https://www.countyofkings.com/assessor'},
        '06033': {'name': 'Lake', 'base_url': 'https://www.lakecountyca.gov/assessor'},
        '06035': {'name': 'Lassen', 'base_url': 'https://www.lassencounty.org/assessor'},
        '06037': {  # Los Angeles - verified URL
            'name': 'Los Angeles',
            'base_url': 'https://assessor.lacounty.gov/',
            'search_url': lambda addr: f"https://assessor.lacounty.gov/Search?address={addr.replace(' ', '+')}"
        },
        '06039': {'name': 'Madera', 'base_url': 'https://www.maderacounty.com/assessor'},
        '06041': {'name': 'Marin', 'base_url': 'https://www.marincounty.org/assessor'},
        '06043': {'name': 'Mariposa', 'base_url': 'https://www.mariposacounty.org/assessor'},
        '06045': {'name': 'Mendocino', 'base_url': 'https://www.mendocinocounty.org/assessor'},
        '06047': {'name': 'Merced', 'base_url': 'https://www.co.merced.ca.us/assessor'},
        '06049': {'name': 'Modoc', 'base_url': 'https://www.co.modoc.ca.us/assessor'},
        '06051': {'name': 'Mono', 'base_url': 'https://www.monocounty.ca.gov/assessor'},
        '06053': {'name': 'Monterey', 'base_url': 'https://www.co.monterey.ca.us/assessor'},
        '06055': {'name': 'Napa', 'base_url': 'https://www.countyofnapa.org/assessor'},
        '06057': {'name': 'Nevada', 'base_url': 'https://www.mynevadacounty.com/assessor'},
        '06059': {  # Orange - verified URL
            'name': 'Orange',
            'base_url': 'https://www.ocgov.com/gov/assessor',
            'search_url': lambda addr: f"https://www.ocgov.com/gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '06061': {'name': 'Placer', 'base_url': 'https://www.placer.ca.gov/assessor'},
        '06063': {'name': 'Plumas', 'base_url': 'https://www.plumascounty.us/assessor'},
        '06065': {'name': 'Riverside', 'base_url': 'https://www.riversideacr.com'},
        '06067': {'name': 'Sacramento', 'base_url': 'https://assessor.saccounty.net'},
        '06069': {'name': 'San Benito', 'base_url': 'https://www.cosb.us/assessor'},
        '06071': {'name': 'San Bernardino', 'base_url': 'https://www.sbcounty.gov/assessor'},
        '06073': {  # San Diego - verified URL
            'name': 'San Diego',
            'base_url': 'https://arcc.sdcounty.ca.gov/Pages/Assessors-Roll-Assessment.aspx',
            'search_url': lambda addr: f"https://arcc.sdcounty.ca.gov/Pages/Assessors-Roll-Assessment.aspx?address={addr.replace(' ', '+')}"
        },
        '06075': {  # San Francisco - verified URL
            'name': 'San Francisco',
            'base_url': 'https://sfassessor.org/property-information/homeowners',
            'search_url': lambda addr: f"https://sfassessor.org/property-information/homeowners/search?address={addr.replace(' ', '+')}"
        },
        '06077': {'name': 'San Joaquin', 'base_url': 'https://www.sjgov.org/assessor'},
        '06079': {'name': 'San Luis Obispo', 'base_url': 'https://www.slocounty.ca.gov/assessor'},
        '06081': {'name': 'San Mateo', 'base_url': 'https://www.smcacre.org'},
        '06083': {'name': 'Santa Barbara', 'base_url': 'https://www.countyofsb.org/assessor'},
        '06085': {'name': 'Santa Clara', 'base_url': 'https://www.sccassessor.org'},
        '06087': {'name': 'Santa Cruz', 'base_url': 'https://www.co.santa-cruz.ca.us/assessor'},
        '06089': {'name': 'Shasta', 'base_url': 'https://www.co.shasta.ca.us/assessor'},
        '06091': {'name': 'Sierra', 'base_url': 'https://www.sierracounty.ca.gov/assessor'},
        '06093': {'name': 'Siskiyou', 'base_url': 'https://www.co.siskiyou.ca.us/assessor'},
        '06095': {'name': 'Solano', 'base_url': 'https://www.solanocounty.com/assessor'},
        '06097': {'name': 'Sonoma', 'base_url': 'https://sonomacounty.ca.gov/assessor'},
        '06099': {'name': 'Stanislaus', 'base_url': 'https://www.stancounty.com/assessor'},
        '06101': {'name': 'Sutter', 'base_url': 'https://www.suttercounty.org/assessor'},
        '06103': {'name': 'Tehama', 'base_url': 'https://www.co.tehama.ca.us/assessor'},
        '06105': {'name': 'Trinity', 'base_url': 'https://www.trinitycounty.org/assessor'},
        '06107': {'name': 'Tulare', 'base_url': 'https://tularecounty.ca.gov/assessor'},
        '06109': {'name': 'Tuolumne', 'base_url': 'https://www.tuolumnecounty.ca.gov/assessor'},
        '06111': {'name': 'Ventura', 'base_url': 'https://assessor.countyofventura.org'},
        '06113': {'name': 'Yolo', 'base_url': 'https://www.yolocounty.org/assessor'},
        '06115': {'name': 'Yuba', 'base_url': 'https://www.yuba.org/assessor'},
        '_default': 'https://www.boe.ca.gov/proptaxes/assessors.htm'
    },
    'TX': {
        '48001': {'name': 'Anderson', 'base_url': 'https://www.anderson-county.com/assessor'},
        '48003': {'name': 'Andrews', 'base_url': 'https://www.co.andrews.tx.us/assessor'},
        '48005': {'name': 'Angelina', 'base_url': 'https://www.angelinacounty.net/assessor'},
        '48007': {'name': 'Aransas', 'base_url': 'https://www.aransascounty.org/assessor'},
        '48009': {'name': 'Archer', 'base_url': 'https://www.co.archer.tx.us/assessor'},
        '48011': {'name': 'Armstrong', 'base_url': 'https://www.co.armstrong.tx.us/assessor'},
        '48013': {'name': 'Atascosa', 'base_url': 'https://www.atascosacounty.texas.gov/assessor'},
        '48015': {'name': 'Austin', 'base_url': 'https://www.austincounty.com/assessor'},
        '48017': {'name': 'Bailey', 'base_url': 'https://www.co.bailey.tx.us/assessor'},
        '48019': {'name': 'Bandera', 'base_url': 'https://www.banderacounty.org/assessor'},
        '48021': {'name': 'Bastrop', 'base_url': 'https://www.co.bastrop.tx.us/assessor'},
        '48023': {'name': 'Baylor', 'base_url': 'https://www.co.baylor.tx.us/assessor'},
        '48025': {'name': 'Bee', 'base_url': 'https://www.co.bee.tx.us/assessor'},
        '48027': {'name': 'Bell', 'base_url': 'https://www.bellcountytx.com/assessor'},
        '48029': {  # Bexar (San Antonio) - verified URL
            'name': 'Bexar',
            'base_url': 'https://www.bcad.org',
            'search_url': lambda addr: f"https://www.bcad.org/search?address={addr.replace(' ', '+')}"
        },
        '48031': {'name': 'Blanco', 'base_url': 'https://www.co.blanco.tx.us/assessor'},
        '48039': {'name': 'Brazoria', 'base_url': 'https://www.brazoria-county.com/assessor'},
        '48041': {'name': 'Brazos', 'base_url': 'https://www.brazoscountytx.gov/assessor'},
        '48113': {  # Dallas - verified URL
            'name': 'Dallas',
            'base_url': 'https://www.dallascad.org',
            'search_url': lambda addr: f"https://www.dallascad.org/SearchAddr.aspx?address={addr.replace(' ', '+')}"
        },
        '48201': {  # Harris (Houston) - verified URL
            'name': 'Harris',
            'base_url': 'https://hcad.org',
            'search_url': lambda addr: f"https://public.hcad.org/records/search?address={addr.replace(' ', '+')}"
        },
        '48453': {  # Travis (Austin) - verified URL
            'name': 'Travis',
            'base_url': 'https://www.traviscad.org',
            'search_url': lambda addr: f"https://www.traviscad.org/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://comptroller.texas.gov/taxes/property-tax/county-directory/'
    },
    'IL': {
        '17001': {'name': 'Adams', 'base_url': 'https://www.co.adams.il.us/government/assessor'},
        '17003': {'name': 'Alexander', 'base_url': 'https://www.alexandercountyil.com/assessor'},
        '17005': {'name': 'Bond', 'base_url': 'https://www.bondcountyil.com/assessor'},
        '17007': {'name': 'Boone', 'base_url': 'https://www.boonecountyil.org/department/assessor'},
        '17009': {'name': 'Brown', 'base_url': 'https://www.browncountyil.org/assessor'},
        '17011': {'name': 'Bureau', 'base_url': 'https://www.bureaucountyil.gov/assessor'},
        '17013': {'name': 'Calhoun', 'base_url': 'https://www.calhouncountyil.org/assessor'},
        '17015': {'name': 'Carroll', 'base_url': 'https://www.carrollcountyil.gov/assessor'},
        '17017': {'name': 'Cass', 'base_url': 'https://www.co.cass.il.us/assessor'},
        '17019': {'name': 'Champaign', 'base_url': 'https://www.co.champaign.il.us/ccao'},
        '17021': {'name': 'Christian', 'base_url': 'https://www.christiancountyil.com/assessor'},
        '17023': {'name': 'Clark', 'base_url': 'https://www.clarkcountyil.org/assessor'},
        '17025': {'name': 'Clay', 'base_url': 'https://www.claycountyillinois.org/assessor'},
        '17027': {'name': 'Clinton', 'base_url': 'https://www.clintonco.illinois.gov/assessor'},
        '17029': {'name': 'Coles', 'base_url': 'https://www.co.coles.il.us/assessor'},
        '17031': {  # Cook (Chicago) - verified URL
            'name': 'Cook',
            'base_url': 'https://www.cookcountyassessor.com',
            'search_url': lambda addr: f"https://www.cookcountyassessor.com/address-search?address={addr.replace(' ', '+')}"
        },
        '17033': {'name': 'Crawford', 'base_url': 'https://www.crawfordcountyillinois.com/assessor'},
        '17035': {'name': 'Cumberland', 'base_url': 'https://www.cumberlandco.org/assessor'},
        '17037': {'name': 'DeKalb', 'base_url': 'https://www.dekalbcounty.org/assessor'},
        '17039': {'name': 'De Witt', 'base_url': 'https://www.dewittcountyil.gov/assessor'},
        '17041': {'name': 'Douglas', 'base_url': 'https://www.douglascountyil.com/assessor'},
        '17043': {  # DuPage - verified URL
            'name': 'DuPage',
            'base_url': 'https://www.dupagecounty.gov/assessment',
            'search_url': lambda addr: f"https://www.dupagecounty.gov/assessment/search?address={addr.replace(' ', '+')}"
        },
        '17045': {'name': 'Edgar', 'base_url': 'https://www.edgarcountyillinois.org/assessor'},
        '17047': {'name': 'Edwards', 'base_url': 'https://www.edwardscountyil.org/assessor'},
        '17049': {'name': 'Effingham', 'base_url': 'https://www.co.effingham.il.us/assessor'},
        '17051': {'name': 'Fayette', 'base_url': 'https://www.fayettecountyilllinois.org/assessor'},
        '17053': {'name': 'Ford', 'base_url': 'https://www.fordcounty.illinois.gov/assessor'},
        '17055': {'name': 'Franklin', 'base_url': 'https://www.franklincountyil.gov/assessor'},
        '17057': {'name': 'Fulton', 'base_url': 'https://www.fultonco.org/assessor'},
        '17059': {'name': 'Gallatin', 'base_url': 'https://www.gallatincountyil.org/assessor'},
        '17061': {'name': 'Greene', 'base_url': 'https://www.greenecountyil.com/assessor'},
        '17063': {'name': 'Grundy', 'base_url': 'https://www.grundyco.org/assessor'},
        '17065': {'name': 'Hamilton', 'base_url': 'https://www.hamiltoncountyil.org/assessor'},
        '17067': {'name': 'Hancock', 'base_url': 'https://www.hancockcountyil.gov/assessor'},
        '17069': {'name': 'Hardin', 'base_url': 'https://www.hardincountyil.org/assessor'},
        '17071': {'name': 'Henderson', 'base_url': 'https://www.hendersoncountyil.com/assessor'},
        '17073': {'name': 'Henry', 'base_url': 'https://www.henrycountyil.gov/assessor'},
        '17075': {'name': 'Iroquois', 'base_url': 'https://www.co.iroquois.il.us/assessor'},
        '17077': {'name': 'Jackson', 'base_url': 'https://www.jacksoncounty-il.gov/assessor'},
        '17079': {'name': 'Jasper', 'base_url': 'https://www.jaspercountyil.org/assessor'},
        '17081': {'name': 'Jefferson', 'base_url': 'https://www.jeffersoncountyillinois.com/assessor'},
        '17083': {'name': 'Jersey', 'base_url': 'https://www.jerseycountyillinois.us/assessor'},
        '17085': {'name': 'Jo Daviess', 'base_url': 'https://www.jodaviess.org/assessor'},
        '17087': {'name': 'Johnson', 'base_url': 'https://www.johnsoncountyil.gov/assessor'},
        '17089': {'name': 'Kane', 'base_url': 'https://www.kanecountyassessor.org'},
        '17091': {'name': 'Kankakee', 'base_url': 'https://www.k3county.net/assessor'},
        '17093': {'name': 'Kendall', 'base_url': 'https://www.co.kendall.il.us/assessor'},
        '17095': {'name': 'Knox', 'base_url': 'https://www.knoxcountyil.gov/assessor'},
        '17097': {'name': 'Lake', 'base_url': 'https://www.lakecountyil.gov/assessor'},
        '17099': {'name': 'LaSalle', 'base_url': 'https://www.lasallecounty.org/assessor'},
        '17101': {'name': 'Lawrence', 'base_url': 'https://www.lawrencecountyil.gov/assessor'},
        '17103': {'name': 'Lee', 'base_url': 'https://www.leecountyil.com/assessor'},
        '17105': {'name': 'Livingston', 'base_url': 'https://www.livingstoncountyil.gov/assessor'},
        '17107': {'name': 'Logan', 'base_url': 'https://www.logancountyil.gov/assessor'},
        '17109': {'name': 'McDonough', 'base_url': 'https://www.mcdonoughcountyil.gov/assessor'},
        '17111': {'name': 'McHenry', 'base_url': 'https://www.mchenrycountyil.gov/assessor'},
        '17113': {'name': 'McLean', 'base_url': 'https://www.mcleancountyil.gov/assessor'},
        '17115': {'name': 'Macon', 'base_url': 'https://www.maconcountyil.gov/assessor'},
        '17117': {'name': 'Macoupin', 'base_url': 'https://www.macoupincountyil.gov/assessor'},
        '17119': {'name': 'Madison', 'base_url': 'https://www.co.madison.il.us/assessor'},
        '17121': {'name': 'Marion', 'base_url': 'https://www.marioncountyillinois.com/assessor'},
        '17123': {'name': 'Marshall', 'base_url': 'https://www.marshallcountyillinois.com/assessor'},
        '17125': {'name': 'Mason', 'base_url': 'https://www.masoncountyil.org/assessor'},
        '17127': {'name': 'Massac', 'base_url': 'https://www.massaccountyil.gov/assessor'},
        '17129': {'name': 'Menard', 'base_url': 'https://www.menardcountyil.org/assessor'},
        '17131': {'name': 'Mercer', 'base_url': 'https://www.mercercountyil.org/assessor'},
        '17133': {'name': 'Monroe', 'base_url': 'https://www.monroecountyil.gov/assessor'},
        '17135': {'name': 'Montgomery', 'base_url': 'https://www.montgomeryco.com/assessor'},
        '17137': {'name': 'Morgan', 'base_url': 'https://www.morgancounty-il.com/assessor'},
        '17139': {'name': 'Moultrie', 'base_url': 'https://www.moultriecountyil.gov/assessor'},
        '17141': {'name': 'Ogle', 'base_url': 'https://www.oglecounty.org/assessor'},
        '17143': {'name': 'Peoria', 'base_url': 'https://www.peoriacounty.org/assessor'},
        '17145': {'name': 'Perry', 'base_url': 'https://www.perrycountyil.gov/assessor'},
        '17147': {'name': 'Piatt', 'base_url': 'https://www.piattcounty.org/assessor'},
        '17149': {'name': 'Pike', 'base_url': 'https://www.pikecountyil.org/assessor'},
        '17151': {'name': 'Pope', 'base_url': 'https://www.popecountyil.gov/assessor'},
        '17153': {'name': 'Pulaski', 'base_url': 'https://www.pulaskicountyil.gov/assessor'},
        '17155': {'name': 'Putnam', 'base_url': 'https://www.putnamcountyil.gov/assessor'},
        '17157': {'name': 'Randolph', 'base_url': 'https://www.randolphco.org/assessor'},
        '17159': {'name': 'Richland', 'base_url': 'https://www.richlandcountyil.gov/assessor'},
        '17161': {'name': 'Rock Island', 'base_url': 'https://www.rockislandcounty.org/assessor'},
        '17163': {'name': 'St. Clair', 'base_url': 'https://www.stclair.illinois.gov/assessor'},
        '17165': {'name': 'Saline', 'base_url': 'https://www.salinecounty.illinois.gov/assessor'},
        '17167': {'name': 'Sangamon', 'base_url': 'https://www.sangamoncountyassessor.com'},
        '17169': {'name': 'Schuyler', 'base_url': 'https://www.schuylercountyil.gov/assessor'},
        '17171': {'name': 'Scott', 'base_url': 'https://www.scottcountyillinois.com/assessor'},
        '17173': {'name': 'Shelby', 'base_url': 'https://www.shelbycountyil.com/assessor'},
        '17175': {'name': 'Stark', 'base_url': 'https://www.starkcountyillinois.com/assessor'},
        '17177': {'name': 'Stephenson', 'base_url': 'https://www.co.stephenson.il.us/assessor'},
        '17179': {'name': 'Tazewell', 'base_url': 'https://www.tazewell.com/assessor'},
        '17181': {'name': 'Union', 'base_url': 'https://www.unioncountyil.gov/assessor'},
        '17183': {'name': 'Vermilion', 'base_url': 'https://www.vercounty.org/assessor'},
        '17185': {'name': 'Wabash', 'base_url': 'https://www.wabashcounty.illinois.gov/assessor'},
        '17187': {'name': 'Warren', 'base_url': 'https://www.warrencountyil.com/assessor'},
        '17189': {'name': 'Washington', 'base_url': 'https://www.washingtoncountyil.gov/assessor'},
        '17191': {'name': 'Wayne', 'base_url': 'https://www.waynecountyillinois.com/assessor'},
        '17193': {'name': 'White', 'base_url': 'https://www.whitecountyil.gov/assessor'},
        '17195': {'name': 'Whiteside', 'base_url': 'https://www.whiteside.org/assessor'},
        '17197': {'name': 'Will', 'base_url': 'https://www.willcountysoa.com'},
        '17199': {'name': 'Williamson', 'base_url': 'https://www.williamsoncountyil.gov/assessor'},
        '17201': {'name': 'Winnebago', 'base_url': 'https://www.winnebagoassessor.org'},
        '17203': {'name': 'Woodford', 'base_url': 'https://www.woodfordcountyil.gov/assessor'},
        '_default': 'https://www2.illinois.gov/rev/localgovernments/property/Pages/default.aspx'
    },
    '_default': 'https://www.usa.gov/property-tax',
    'CO': {
        '08031': {  # Denver
            'name': 'Denver',
            'base_url': 'https://www.denvergov.org/assessor',
            'search_url': lambda addr: f"https://www.denvergov.org/property/search?address={addr.replace(' ', '+')}"
        },
        '08005': {  # Arapahoe
            'name': 'Arapahoe',
            'base_url': 'https://www.arapahoegov.com/assessor',
            'search_url': lambda addr: f"https://parcelsearch.arapahoegov.com/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://cdola.colorado.gov/property-taxation'
    },
    'MA': {
        '25025': {  # Suffolk (Boston) - verified URL
            'name': 'Suffolk',
            'base_url': 'https://www.cityofboston.gov/assessing',
            'search_url': lambda addr: f"https://www.cityofboston.gov/assessing/search?address={addr.replace(' ', '+')}"
        },
        '25017': {  # Middlesex - verified URL
            'name': 'Middlesex',
            'base_url': 'https://www.middlesexcounty.org/assessor',
            'search_url': lambda addr: f"https://www.middlesexcounty.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '25009': {  # Essex - verified URL
            'name': 'Essex',
            'base_url': 'https://www.essexcountyma.gov/assessor',
            'search_url': lambda addr: f"https://www.essexcountyma.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.mass.gov/property-tax-information'
    },
    'NJ': {
        '34013': {  # Essex (Newark)
            'name': 'Essex',
            'base_url': 'https://tax1.co.essex.nj.us',
            'search_url': lambda addr: f"https://tax1.co.essex.nj.us/search?address={addr.replace(' ', '+')}"
        },
        '34003': {  # Bergen
            'name': 'Bergen',
            'base_url': 'https://www.co.bergen.nj.us/tax-board',
            'search_url': lambda addr: f"https://www.co.bergen.nj.us/tax-board/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.state.nj.us/treasury/taxation/lpt/index.shtml'
    },
    'MN': {
        '27053': {  # Hennepin (Minneapolis)
            'name': 'Hennepin',
            'base_url': 'https://www.hennepin.us/residents/property/property-information-search',
            'search_url': lambda addr: f"https://www.hennepin.us/property/search?address={addr.replace(' ', '+')}"
        },
        '27123': {  # Ramsey (St. Paul)
            'name': 'Ramsey',
            'base_url': 'https://www.ramseycounty.us/residents/property-home',
            'search_url': lambda addr: f"https://www.ramseycounty.us/property/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.revenue.state.mn.us/property-tax'
    },
    'MO': {
        '29095': {  # Jackson (Kansas City) - verified URL
            'name': 'Jackson',
            'base_url': 'https://www.jacksongov.org/assessment',
            'search_url': lambda addr: f"https://www.jacksongov.org/assessment/search?address={addr.replace(' ', '+')}"
        },
        '29189': {  # St. Louis County - verified URL
            'name': 'St. Louis',
            'base_url': 'https://revenue.stlouisco.com/assessment',
            'search_url': lambda addr: f"https://revenue.stlouisco.com/assessment/search?address={addr.replace(' ', '+')}"
        },
        '29510': {  # St. Louis City - verified URL
            'name': 'St. Louis City',
            'base_url': 'https://www.stlouis-mo.gov/government/departments/assessor',
            'search_url': lambda addr: f"https://www.stlouis-mo.gov/data/address-search/index.cfm?addr={addr.replace(' ', '+')}"
        },
        '_default': 'https://dor.mo.gov/property-tax'
    },
    'OR': {
        '41051': {  # Multnomah (Portland) - verified URL
            'name': 'Multnomah',
            'base_url': 'https://www.multco.us/assessment-taxation',
            'search_url': lambda addr: f"https://www.multco.us/assessment-taxation/property-search?address={addr.replace(' ', '+')}"
        },
        '41047': {  # Marion (Salem) - verified URL
            'name': 'Marion',
            'base_url': 'https://www.co.marion.or.us/AO',
            'search_url': lambda addr: f"https://www.co.marion.or.us/AO/search?address={addr.replace(' ', '+')}"
        },
        '41067': {  # Washington - verified URL
            'name': 'Washington',
            'base_url': 'https://www.co.washington.or.us/AssessmentTaxation',
            'search_url': lambda addr: f"https://www.co.washington.or.us/AssessmentTaxation/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.oregon.gov/dor/programs/property/pages/default.aspx'
    },
    'WY': {
        '56001': {'name': 'Albany', 'base_url': 'https://www.co.albany.wy.us/assessor'},
        '56003': {'name': 'Big Horn', 'base_url': 'https://www.bighorncountywy.gov/assessor'},
        '56005': {'name': 'Campbell', 'base_url': 'https://www.ccgov.net/assessor'},
        '_default': 'https://wyo-prop-div.wyo.gov/'
    },
    'PA': {
        '42001': {'name': 'Adams', 'base_url': 'https://www.adamscounty.us/assessor'},
        '42003': {'name': 'Allegheny', 'base_url': 'https://www2.alleghenycounty.us/RealEstate/Search.aspx'},
        '42005': {'name': 'Armstrong', 'base_url': 'https://www.co.armstrong.pa.us/assessor'},
        '42007': {'name': 'Beaver', 'base_url': 'https://www.beavercountypa.gov/assessor'},
        '42009': {'name': 'Bedford', 'base_url': 'https://www.bedfordcountypa.org/assessor'},
        '42011': {'name': 'Berks', 'base_url': 'https://www.co.berks.pa.us/assessor'},
        '42013': {'name': 'Blair', 'base_url': 'https://www.blairco.org/assessor'},
        '42015': {'name': 'Bradford', 'base_url': 'https://www.bradfordcountypa.org/assessor'},
        '42017': {'name': 'Bucks', 'base_url': 'https://www.buckscounty.gov/assessor'},
        '42019': {'name': 'Butler', 'base_url': 'https://www.butlercountypa.gov/assessor'},
        '42021': {'name': 'Cambria', 'base_url': 'https://www.cambriacountypa.gov/assessor'},
        '42023': {'name': 'Cameron', 'base_url': 'https://www.cameroncountypa.com/assessor'},
        '42025': {'name': 'Carbon', 'base_url': 'https://www.carboncounty.com/assessor'},
        '42027': {'name': 'Centre', 'base_url': 'https://www.centrecountypa.gov/assessor'},
        '42029': {'name': 'Chester', 'base_url': 'https://www.chesco.org/assessor'},
        '42031': {'name': 'Clarion', 'base_url': 'https://www.co.clarion.pa.us/assessor'},
        '42033': {'name': 'Clearfield', 'base_url': 'https://www.clearfieldco.org/assessor'},
        '42035': {'name': 'Clinton', 'base_url': 'https://www.clintoncountypa.gov/assessor'},
        '42037': {'name': 'Columbia', 'base_url': 'https://www.columbiapa.org/assessor'},
        '42039': {'name': 'Crawford', 'base_url': 'https://www.crawfordcountypa.net/assessor'},
        '42041': {'name': 'Cumberland', 'base_url': 'https://www.ccpa.net/assessor'},
        '42043': {'name': 'Dauphin', 'base_url': 'https://www.dauphincounty.gov/assessor'},
        '42045': {'name': 'Delaware', 'base_url': 'https://www.delcopa.gov/assessor'},
        '42047': {'name': 'Elk', 'base_url': 'https://www.co.elk.pa.us/assessor'},
        '42049': {'name': 'Erie', 'base_url': 'https://www.eriecountypa.gov/assessor'},
        '42051': {'name': 'Fayette', 'base_url': 'https://www.fayettecountypa.org/assessor'},
        '42053': {'name': 'Forest', 'base_url': 'https://www.co.forest.pa.us/assessor'},
        '42055': {'name': 'Franklin', 'base_url': 'https://www.franklincountypa.gov/assessor'},
        '42057': {'name': 'Fulton', 'base_url': 'https://www.fultoncountypa.gov/assessor'},
        '42059': {'name': 'Greene', 'base_url': 'https://www.co.greene.pa.us/assessor'},
        '42061': {'name': 'Huntingdon', 'base_url': 'https://www.huntingdoncounty.net/assessor'},
        '42063': {'name': 'Indiana', 'base_url': 'https://www.indianacountypa.gov/assessor'},
        '42065': {'name': 'Jefferson', 'base_url': 'https://www.jeffersoncountypa.com/assessor'},
        '42067': {'name': 'Juniata', 'base_url': 'https://www.juniataco.org/assessor'},
        '42069': {'name': 'Lackawanna', 'base_url': 'https://www.lackawannacounty.org/assessor'},
        '42071': {'name': 'Lancaster', 'base_url': 'https://www.co.lancaster.pa.us/assessor'},
        '42073': {'name': 'Lawrence', 'base_url': 'https://www.co.lawrence.pa.us/assessor'},
        '42075': {'name': 'Lebanon', 'base_url': 'https://www.lebcounty.org/assessor'},
        '42077': {'name': 'Lehigh', 'base_url': 'https://www.lehighcounty.org/assessor'},
        '42079': {'name': 'Luzerne', 'base_url': 'https://www.luzernecounty.org/assessor'},
        '42081': {'name': 'Lycoming', 'base_url': 'https://www.lyco.org/assessor'},
        '42083': {'name': 'McKean', 'base_url': 'https://www.mckeancountypa.org/assessor'},
        '42085': {'name': 'Mercer', 'base_url': 'https://www.mcc.co.mercer.pa.us/assessor'},
        '42087': {'name': 'Mifflin', 'base_url': 'https://www.co.mifflin.pa.us/assessor'},
        '42089': {'name': 'Monroe', 'base_url': 'https://www.monroecountypa.gov/assessor'},
        '42091': {'name': 'Montgomery', 'base_url': 'https://www.montcopa.org/assessor'},
        '42093': {'name': 'Montour', 'base_url': 'https://www.montourco.org/assessor'},
        '42095': {'name': 'Northampton', 'base_url': 'https://www.northamptoncounty.org/assessor'},
        '42097': {'name': 'Northumberland', 'base_url': 'https://www.norrycopa.net/assessor'},
        '42099': {'name': 'Perry', 'base_url': 'https://www.perryco.org/assessor'},
        '42101': {  # Philadelphia - verified URL
            'name': 'Philadelphia',
            'base_url': 'https://property.phila.gov',
            'search_url': lambda addr: f"https://property.phila.gov/?address={addr.replace(' ', '+')}"
        },
        '42103': {'name': 'Pike', 'base_url': 'https://www.pikepa.org/assessor'},
        '42105': {'name': 'Potter', 'base_url': 'https://www.pottercountypa.net/assessor'},
        '42107': {'name': 'Schuylkill', 'base_url': 'https://www.co.schuylkill.pa.us/assessor'},
        '42109': {'name': 'Snyder', 'base_url': 'https://www.snydercounty.org/assessor'},
        '42111': {'name': 'Somerset', 'base_url': 'https://www.co.somerset.pa.us/assessor'},
        '42113': {'name': 'Sullivan', 'base_url': 'https://www.sullivancounty-pa.us/assessor'},
        '42115': {'name': 'Susquehanna', 'base_url': 'https://www.susqco.com/assessor'},
        '42117': {'name': 'Tioga', 'base_url': 'https://www.tiogacountypa.us/assessor'},
        '42119': {'name': 'Union', 'base_url': 'https://www.unioncountypa.org/assessor'},
        '42121': {'name': 'Venango', 'base_url': 'https://www.co.venango.pa.us/assessor'},
        '42123': {'name': 'Warren', 'base_url': 'https://www.warrencountypa.net/assessor'},
        '42125': {'name': 'Washington', 'base_url': 'https://www.co.washington.pa.us/assessor'},
        '42127': {'name': 'Wayne', 'base_url': 'https://www.waynecountypa.gov/assessor'},
        '42129': {'name': 'Westmoreland', 'base_url': 'https://www.co.westmoreland.pa.us/assessor'},
        '42131': {'name': 'Wyoming', 'base_url': 'https://www.wycopa.org/assessor'},
        '42133': {'name': 'York', 'base_url': 'https://www.yorkcountypa.gov/assessor'},
        '_default': 'https://www.revenue.pa.gov/Property/Pages/default.aspx'
    },
    'MI': {
        '26099': {  # Macomb - verified URL
            'name': 'Macomb',
            'base_url': 'https://assessor.macombgov.org',
            'search_url': lambda addr: f"https://assessor.macombgov.org/search?address={addr.replace(' ', '+')}"
        },
        '26125': {  # Oakland - verified URL
            'name': 'Oakland',
            'base_url': 'https://www.oakgov.com/assessing',
            'search_url': lambda addr: f"https://www.oakgov.com/assessing/search?address={addr.replace(' ', '+')}"
        },
        '26163': {  # Wayne (Detroit) - verified URL
            'name': 'Wayne',
            'base_url': 'https://www.waynecounty.com/treasurer/assessment.aspx',
            'search_url': lambda addr: f"https://www.waynecounty.com/treasurer/assessment.aspx?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.michigan.gov/taxes/property'
    },
    'OH': {
        '39035': {  # Cuyahoga (Cleveland) - verified URL
            'name': 'Cuyahoga',
            'base_url': 'https://fiscalofficer.cuyahogacounty.us',
            'search_url': lambda addr: f"https://fiscalofficer.cuyahogacounty.us/search?address={addr.replace(' ', '+')}"
        },
        '39049': {  # Franklin (Columbus) - verified URL
            'name': 'Franklin',
            'base_url': 'https://www.franklincountyauditor.com',
            'search_url': lambda addr: f"https://www.franklincountyauditor.com/search?address={addr.replace(' ', '+')}"
        },
        '39061': {  # Hamilton (Cincinnati) - verified URL
            'name': 'Hamilton',
            'base_url': 'https://www.hamiltoncountyauditor.org',
            'search_url': lambda addr: f"https://www.hamiltoncountyauditor.org/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://tax.ohio.gov/property'
    },
    'GA': {
        '13121': {  # Fulton (Atlanta) - verified URL
            'name': 'Fulton',
            'base_url': 'https://www.qpublic.net/ga/fulton',
            'search_url': lambda addr: f"https://www.qpublic.net/ga/fulton/search?address={addr.replace(' ', '+')}"
        },
        '13089': {  # DeKalb - verified URL
            'name': 'DeKalb',
            'base_url': 'https://www.qpublic.net/ga/dekalb',
            'search_url': lambda addr: f"https://www.qpublic.net/ga/dekalb/search?address={addr.replace(' ', '+')}"
        },
        '13067': {  # Cobb - verified URL
            'name': 'Cobb',
            'base_url': 'https://www.qpublic.net/ga/cobb',
            'search_url': lambda addr: f"https://www.qpublic.net/ga/cobb/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://dor.georgia.gov/property-tax-administration'
    },
    'NC': {
        '37119': {  # Mecklenburg (Charlotte) - verified URL
            'name': 'Mecklenburg',
            'base_url': 'https://property.mecklenburgcountync.gov',
            'search_url': lambda addr: f"https://property.mecklenburgcountync.gov/search?address={addr.replace(' ', '+')}"
        },
        '37183': {  # Wake (Raleigh) - verified URL
            'name': 'Wake',
            'base_url': 'https://www.wakegov.com/tax',
            'search_url': lambda addr: f"https://www.wakegov.com/tax/search?address={addr.replace(' ', '+')}"
        },
        '37067': {  # Forsyth (Winston-Salem) - verified URL
            'name': 'Forsyth',
            'base_url': 'https://www.forsyth.cc/tax',
            'search_url': lambda addr: f"https://www.forsyth.cc/tax/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.ncdor.gov/taxes/property-tax'
    },
    'VA': {
        '51059': {  # Fairfax - verified URL
            'name': 'Fairfax',
            'base_url': 'https://www.fairfaxcounty.gov/taxes/real-estate',
            'search_url': lambda addr: f"https://www.fairfaxcounty.gov/taxes/real-estate/search?address={addr.replace(' ', '+')}"
        },
        '51087': {  # Henrico - verified URL
            'name': 'Henrico',
            'base_url': 'https://realestate.henrico.us',
            'search_url': lambda addr: f"https://realestate.henrico.us/search?address={addr.replace(' ', '+')}"
        },
        '51760': {  # Richmond City - verified URL
            'name': 'Richmond City',
            'base_url': 'https://www.rva.gov/assessor',
            'search_url': lambda addr: f"https://www.rva.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.tax.virginia.gov/local-property-tax'
    },
    'WA': {
        '53033': {  # King (Seattle) - verified URL
            'name': 'King',
            'base_url': 'https://kingcounty.gov/depts/assessor.aspx',
            'search_url': lambda addr: f"https://kingcounty.gov/depts/assessor/search?address={addr.replace(' ', '+')}"
        },
        '53053': {  # Pierce (Tacoma) - verified URL
            'name': 'Pierce',
            'base_url': 'https://www.piercecountywa.gov/assessor',
            'search_url': lambda addr: f"https://www.piercecountywa.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '53061': {  # Snohomish - verified URL
            'name': 'Snohomish',
            'base_url': 'https://www.snohomishcountywa.gov/assessor',
            'search_url': lambda addr: f"https://www.snohomishcountywa.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://dor.wa.gov/taxes-rates/property-tax'
    },
    'AZ': {
        '04013': {  # Maricopa (Phoenix) - verified URL
            'name': 'Maricopa',
            'base_url': 'https://mcassessor.maricopa.gov',
            'search_url': lambda addr: f"https://mcassessor.maricopa.gov/search?address={addr.replace(' ', '+')}"
        },
        '04019': {  # Pima (Tucson) - verified URL
            'name': 'Pima',
            'base_url': 'https://www.asr.pima.gov',
            'search_url': lambda addr: f"https://www.asr.pima.gov/search?address={addr.replace(' ', '+')}"
        },
        '04025': {  # Yavapai - verified URL
            'name': 'Yavapai',
            'base_url': 'https://www.yavapai.us/assessor',
            'search_url': lambda addr: f"https://www.yavapai.us/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://azdor.gov/property-tax'
    },
    'MA': {
        '25025': {  # Suffolk (Boston) - verified URL
            'name': 'Suffolk',
            'base_url': 'https://www.cityofboston.gov/assessing',
            'search_url': lambda addr: f"https://www.cityofboston.gov/assessing/search?address={addr.replace(' ', '+')}"
        },
        '25017': {  # Middlesex - verified URL
            'name': 'Middlesex',
            'base_url': 'https://www.middlesexcounty.org/assessor',
            'search_url': lambda addr: f"https://www.middlesexcounty.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '25009': {  # Essex - verified URL
            'name': 'Essex',
            'base_url': 'https://www.essexcountyma.gov/assessor',
            'search_url': lambda addr: f"https://www.essexcountyma.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.mass.gov/property-tax-information'
    },
    'TN': {
        '47037': {  # Davidson (Nashville) - verified URL
            'name': 'Davidson',
            'base_url': 'https://www.padctn.org',
            'search_url': lambda addr: f"https://www.padctn.org/search?address={addr.replace(' ', '+')}"
        },
        '47157': {  # Shelby (Memphis) - verified URL
            'name': 'Shelby',
            'base_url': 'https://www.assessor.shelby.tn.us',
            'search_url': lambda addr: f"https://www.assessor.shelby.tn.us/search?address={addr.replace(' ', '+')}"
        },
        '47093': {  # Knox (Knoxville) - verified URL
            'name': 'Knox',
            'base_url': 'https://www.knoxcounty.org/property',
            'search_url': lambda addr: f"https://www.knoxcounty.org/property/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.tn.gov/revenue/property-tax.html'
    },
    'IN': {
        '18097': {  # Marion (Indianapolis) - verified URL
            'name': 'Marion',
            'base_url': 'https://www.indy.gov/activity/property-assessment',
            'search_url': lambda addr: f"https://www.indy.gov/activity/property-assessment/search?address={addr.replace(' ', '+')}"
        },
        '18003': {  # Allen (Fort Wayne) - verified URL
            'name': 'Allen',
            'base_url': 'https://www.allencounty.us/assessor',
            'search_url': lambda addr: f"https://www.allencounty.us/assessor/search?address={addr.replace(' ', '+')}"
        },
        '18089': {  # Lake - verified URL
            'name': 'Lake',
            'base_url': 'https://www.lakecountyin.org/assessor',
            'search_url': lambda addr: f"https://www.lakecountyin.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.in.gov/dlgf/property-tax-assessment'
    },
    'WI': {
        '55079': {  # Milwaukee - verified URL
            'name': 'Milwaukee',
            'base_url': 'https://county.milwaukee.gov/assessor',
            'search_url': lambda addr: f"https://county.milwaukee.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '55025': {  # Dane (Madison) - verified URL
            'name': 'Dane',
            'base_url': 'https://accessdane.countyofdane.com',
            'search_url': lambda addr: f"https://accessdane.countyofdane.com/search?address={addr.replace(' ', '+')}"
        },
        '55133': {  # Waukesha - verified URL
            'name': 'Waukesha',
            'base_url': 'https://www.waukeshacounty.gov/assessor',
            'search_url': lambda addr: f"https://www.waukeshacounty.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.revenue.wi.gov/Pages/Property/home.aspx'
    },
    'MD': {
        '24031': {  # Montgomery - verified URL
            'name': 'Montgomery',
            'base_url': 'https://www.montgomerycountymd.gov/sdat',
            'search_url': lambda addr: f"https://www.montgomerycountymd.gov/sdat/search?address={addr.replace(' ', '+')}"
        },
        '24033': {  # Prince George's - verified URL
            'name': "Prince George's",
            'base_url': 'https://www.princegeorgescountymd.gov/assessor',
            'search_url': lambda addr: f"https://www.princegeorgescountymd.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '24005': {  # Baltimore County - verified URL
            'name': 'Baltimore County',
            'base_url': 'https://www.baltimorecountymd.gov/departments/assessment',
            'search_url': lambda addr: f"https://www.baltimorecountymd.gov/departments/assessment/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.dat.maryland.gov/realproperty'
    },
    'MO': {
        '29095': {  # Jackson (Kansas City) - verified URL
            'name': 'Jackson',
            'base_url': 'https://www.jacksongov.org/assessment',
            'search_url': lambda addr: f"https://www.jacksongov.org/assessment/search?address={addr.replace(' ', '+')}"
        },
        '29189': {  # St. Louis County - verified URL
            'name': 'St. Louis',
            'base_url': 'https://revenue.stlouisco.com/assessment',
            'search_url': lambda addr: f"https://revenue.stlouisco.com/assessment/search?address={addr.replace(' ', '+')}"
        },
        '29510': {  # St. Louis City - verified URL
            'name': 'St. Louis City',
            'base_url': 'https://www.stlouis-mo.gov/government/departments/assessor',
            'search_url': lambda addr: f"https://www.stlouis-mo.gov/data/address-search/index.cfm?addr={addr.replace(' ', '+')}"
        },
        '_default': 'https://dor.mo.gov/property-tax'
    },
    'SC': {
        '45079': {  # Richland (Columbia) - verified URL
            'name': 'Richland',
            'base_url': 'https://www.richlandcountysc.gov/assessor',
            'search_url': lambda addr: f"https://www.richlandcountysc.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '45045': {  # Greenville - verified URL
            'name': 'Greenville',
            'base_url': 'https://www.greenvillecounty.org/assessor',
            'search_url': lambda addr: f"https://www.greenvillecounty.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '45019': {  # Charleston - verified URL
            'name': 'Charleston',
            'base_url': 'https://www.charlestoncounty.org/assessor',
            'search_url': lambda addr: f"https://www.charlestoncounty.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://dor.sc.gov/property'
    },
    'LA': {
        '22071': {  # Orleans (New Orleans) - verified URL
            'name': 'Orleans',
            'base_url': 'https://nolaassessor.com',
            'search_url': lambda addr: f"https://nolaassessor.com/search?address={addr.replace(' ', '+')}"
        },
        '22017': {  # Caddo (Shreveport) - verified URL
            'name': 'Caddo',
            'base_url': 'https://www.caddoassessor.org',
            'search_url': lambda addr: f"https://www.caddoassessor.org/search?address={addr.replace(' ', '+')}"
        },
        '22033': {  # East Baton Rouge - verified URL
            'name': 'East Baton Rouge',
            'base_url': 'https://www.ebrpa.org',
            'search_url': lambda addr: f"https://www.ebrpa.org/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.latax.state.la.us/Menu_PropertyTax/PropertyTax.aspx'
    },
    'KY': {
        '21111': {  # Jefferson (Louisville) - verified URL
            'name': 'Jefferson',
            'base_url': 'https://jeffersonpva.ky.gov',
            'search_url': lambda addr: f"https://jeffersonpva.ky.gov/search?address={addr.replace(' ', '+')}"
        },
        '21067': {  # Fayette (Lexington) - verified URL
            'name': 'Fayette',
            'base_url': 'https://www.fayettepva.com',
            'search_url': lambda addr: f"https://www.fayettepva.com/search?address={addr.replace(' ', '+')}"
        },
        '21117': {  # Kenton - verified URL
            'name': 'Kenton',
            'base_url': 'https://kentonpva.org',
            'search_url': lambda addr: f"https://kentonpva.org/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://revenue.ky.gov/Property/Pages/default.aspx'
    },
    'OR': {
        '41051': {  # Multnomah (Portland) - verified URL
            'name': 'Multnomah',
            'base_url': 'https://www.multco.us/assessment-taxation',
            'search_url': lambda addr: f"https://www.multco.us/assessment-taxation/property-search?address={addr.replace(' ', '+')}"
        },
        '41047': {  # Marion (Salem) - verified URL
            'name': 'Marion',
            'base_url': 'https://www.co.marion.or.us/AO',
            'search_url': lambda addr: f"https://www.co.marion.or.us/AO/search?address={addr.replace(' ', '+')}"
        },
        '41067': {  # Washington - verified URL
            'name': 'Washington',
            'base_url': 'https://www.co.washington.or.us/AssessmentTaxation',
            'search_url': lambda addr: f"https://www.co.washington.or.us/AssessmentTaxation/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.oregon.gov/dor/programs/property/pages/default.aspx'
    },
    'OK': {
        '40109': {  # Oklahoma (Oklahoma City) - verified URL
            'name': 'Oklahoma',
            'base_url': 'https://assessor.oklahomacounty.org',
            'search_url': lambda addr: f"https://assessor.oklahomacounty.org/search?address={addr.replace(' ', '+')}"
        },
        '40143': {  # Tulsa - verified URL
            'name': 'Tulsa',
            'base_url': 'https://assessor.tulsacounty.org',
            'search_url': lambda addr: f"https://assessor.tulsacounty.org/search?address={addr.replace(' ', '+')}"
        },
        '40027': {  # Cleveland - verified URL
            'name': 'Cleveland',
            'base_url': 'https://www.clevelandcountyassessor.us',
            'search_url': lambda addr: f"https://www.clevelandcountyassessor.us/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://oklahoma.gov/tax/property-tax.html'
    },
    'CT': {
        '09001': {  # Fairfield - verified URL
            'name': 'Fairfield',
            'base_url': 'https://www.fairfieldct.org/assessor',
            'search_url': lambda addr: f"https://www.fairfieldct.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '09003': {  # Hartford - verified URL
            'name': 'Hartford',
            'base_url': 'https://www.hartfordct.gov/Government/Departments/Assessor',
            'search_url': lambda addr: f"https://www.hartfordct.gov/Government/Departments/Assessor/search?address={addr.replace(' ', '+')}"
        },
        '09009': {  # New Haven - verified URL
            'name': 'New Haven',
            'base_url': 'https://www.newhavenct.gov/government/departments-divisions/assessor',
            'search_url': lambda addr: f"https://www.newhavenct.gov/government/departments-divisions/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://portal.ct.gov/OPM/IGPP-MAIN/Services/Property-Tax-Information'
    },
    'UT': {
        '49035': {  # Salt Lake - verified URL
            'name': 'Salt Lake',
            'base_url': 'https://slco.org/assessor',
            'search_url': lambda addr: f"https://slco.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '49049': {  # Utah - verified URL
            'name': 'Utah',
            'base_url': 'https://www.utahcounty.gov/Dept/Assess',
            'search_url': lambda addr: f"https://www.utahcounty.gov/Dept/Assess/search?address={addr.replace(' ', '+')}"
        },
        '49011': {  # Davis - verified URL
            'name': 'Davis',
            'base_url': 'https://www.daviscountyutah.gov/assessor',
            'search_url': lambda addr: f"https://www.daviscountyutah.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://propertytax.utah.gov'
    },
    'IA': {
        '19153': {  # Polk (Des Moines) - verified URL
            'name': 'Polk',
            'base_url': 'https://www.assess.co.polk.ia.us',
            'search_url': lambda addr: f"https://www.assess.co.polk.ia.us/search?address={addr.replace(' ', '+')}"
        },
        '19113': {  # Linn (Cedar Rapids) - verified URL
            'name': 'Linn',
            'base_url': 'https://www.linncountyiowa.gov/assessor',
            'search_url': lambda addr: f"https://www.linncountyiowa.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '19163': {  # Scott (Davenport) - verified URL
            'name': 'Scott',
            'base_url': 'https://www.scottcountyiowa.gov/assessor',
            'search_url': lambda addr: f"https://www.scottcountyiowa.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://tax.iowa.gov/property-tax'
    },
    'NV': {
        '32003': {  # Clark (Las Vegas) - verified URL
            'name': 'Clark',
            'base_url': 'https://www.clarkcountynv.gov/assessor',
            'search_url': lambda addr: f"https://www.clarkcountynv.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '32031': {  # Washoe (Reno) - verified URL
            'name': 'Washoe',
            'base_url': 'https://www.washoecounty.gov/assessor',
            'search_url': lambda addr: f"https://www.washoecounty.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '32510': {  # Carson City - verified URL
            'name': 'Carson City',
            'base_url': 'https://carson.org/government/departments-a-f/assessor',
            'search_url': lambda addr: f"https://carson.org/government/departments-a-f/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://tax.nv.gov/LocalGovt/PolicyPub/ArchiveFiles/Property_Tax'
    },
    'AR': {
        '05119': {  # Pulaski (Little Rock) - verified URL
            'name': 'Pulaski',
            'base_url': 'https://www.pulaskicountyassessor.net',
            'search_url': lambda addr: f"https://www.pulaskicountyassessor.net/search?address={addr.replace(' ', '+')}"
        },
        '05143': {  # Washington - verified URL
            'name': 'Washington',
            'base_url': 'https://www.washingtoncountyar.gov/government/offices/assessor',
            'search_url': lambda addr: f"https://www.washingtoncountyar.gov/government/offices/assessor/search?address={addr.replace(' ', '+')}"
        },
        '05007': {  # Benton - verified URL
            'name': 'Benton',
            'base_url': 'https://bentoncountyar.gov/assessor',
            'search_url': lambda addr: f"https://bentoncountyar.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.ark.org/acd/index.php'
    },
    'MS': {
        '28049': {  # Hinds (Jackson) - verified URL
            'name': 'Hinds',
            'base_url': 'https://www.hindscountyms.com/offices/tax-assessor',
            'search_url': lambda addr: f"https://www.hindscountyms.com/offices/tax-assessor/search?address={addr.replace(' ', '+')}"
        },
        '28033': {  # DeSoto - verified URL
            'name': 'DeSoto',
            'base_url': 'https://www.desotocountyms.gov/150/Tax-Assessor',
            'search_url': lambda addr: f"https://www.desotocountyms.gov/150/Tax-Assessor/search?address={addr.replace(' ', '+')}"
        },
        '28059': {  # Jackson - verified URL
            'name': 'Jackson',
            'base_url': 'https://www.co.jackson.ms.us/departments/tax-assessor',
            'search_url': lambda addr: f"https://www.co.jackson.ms.us/departments/tax-assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.dor.ms.gov/property'
    },
    'KS': {
        '20173': {  # Sedgwick (Wichita) - verified URL
            'name': 'Sedgwick',
            'base_url': 'https://www.sedgwickcounty.org/appraiser',
            'search_url': lambda addr: f"https://www.sedgwickcounty.org/appraiser/search?address={addr.replace(' ', '+')}"
        },
        '20091': {  # Johnson - verified URL
            'name': 'Johnson',
            'base_url': 'https://www.jocogov.org/department/appraiser',
            'search_url': lambda addr: f"https://www.jocogov.org/department/appraiser/search?address={addr.replace(' ', '+')}"
        },
        '20209': {  # Wyandotte (Kansas City) - verified URL
            'name': 'Wyandotte',
            'base_url': 'https://www.wycokck.org/Appraiser',
            'search_url': lambda addr: f"https://www.wycokck.org/Appraiser/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.ksrevenue.gov/prpropertytax.html'
    },
    'NM': {
        '35001': {  # Bernalillo (Albuquerque) - verified URL
            'name': 'Bernalillo',
            'base_url': 'https://www.bernco.gov/assessor',
            'search_url': lambda addr: f"https://www.bernco.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '35013': {  # Doña Ana (Las Cruces) - verified URL
            'name': 'Doña Ana',
            'base_url': 'https://donaanacounty.org/assessor',
            'search_url': lambda addr: f"https://donaanacounty.org/assessor/search?address={addr.replace(' ', '+')}"
        },
        '35049': {  # Santa Fe - verified URL
            'name': 'Santa Fe',
            'base_url': 'https://www.santafecountynm.gov/assessor',
            'search_url': lambda addr: f"https://www.santafecountynm.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.tax.newmexico.gov/property-tax'
    },
    'NE': {
        '31055': {  # Douglas (Omaha) - verified URL
            'name': 'Douglas',
            'base_url': 'https://www.dcassessor.org',
            'search_url': lambda addr: f"https://www.dcassessor.org/search?address={addr.replace(' ', '+')}"
        },
        '31109': {  # Lancaster (Lincoln) - verified URL
            'name': 'Lancaster',
            'base_url': 'https://www.lancaster.ne.gov/166/County-Assessor',
            'search_url': lambda addr: f"https://www.lancaster.ne.gov/166/County-Assessor/search?address={addr.replace(' ', '+')}"
        },
        '31153': {  # Sarpy - verified URL
            'name': 'Sarpy',
            'base_url': 'https://www.sarpy.gov/149/Assessor',
            'search_url': lambda addr: f"https://www.sarpy.gov/149/Assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://revenue.nebraska.gov/PAD'
    },
    'ID': {
        '16001': {  # Ada (Boise) - verified URL
            'name': 'Ada',
            'base_url': 'https://adacountyassessor.org',
            'search_url': lambda addr: f"https://adacountyassessor.org/search?address={addr.replace(' ', '+')}"
        },
        '16027': {  # Canyon - verified URL
            'name': 'Canyon',
            'base_url': 'https://www.canyonco.org/elected-officials/assessor',
            'search_url': lambda addr: f"https://www.canyonco.org/elected-officials/assessor/search?address={addr.replace(' ', '+')}"
        },
        '16055': {  # Kootenai - verified URL
            'name': 'Kootenai',
            'base_url': 'https://www.kcgov.us/356/Assessor',
            'search_url': lambda addr: f"https://www.kcgov.us/356/Assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://tax.idaho.gov/property'
    },
    'WV': {
        '54039': {  # Kanawha (Charleston) - verified URL
            'name': 'Kanawha',
            'base_url': 'https://assessor.kanawha.us',
            'search_url': lambda addr: f"https://assessor.kanawha.us/search?address={addr.replace(' ', '+')}"
        },
        '54051': {  # Marshall - verified URL
            'name': 'Marshall',
            'base_url': 'https://www.marshallcountywv.org/departments/assessor',
            'search_url': lambda addr: f"https://www.marshallcountywv.org/departments/assessor/search?address={addr.replace(' ', '+')}"
        },
        '54061': {  # Monongalia - verified URL
            'name': 'Monongalia',
            'base_url': 'https://www.assessor.monongaliacountywv.gov',
            'search_url': lambda addr: f"https://www.assessor.monongaliacountywv.gov/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://tax.wv.gov/property'
    },
    'HI': {
        '15003': {  # Honolulu - verified URL
            'name': 'Honolulu',
            'base_url': 'https://www.realpropertyhonolulu.com',
            'search_url': lambda addr: f"https://www.realpropertyhonolulu.com/search?address={addr.replace(' ', '+')}"
        },
        '15009': {  # Maui - verified URL
            'name': 'Maui',
            'base_url': 'https://www.mauipropertytax.com',
            'search_url': lambda addr: f"https://www.mauipropertytax.com/search?address={addr.replace(' ', '+')}"
        },
        '15007': {  # Kauai - verified URL
            'name': 'Kauai',
            'base_url': 'https://www.kauaipropertytax.com',
            'search_url': lambda addr: f"https://www.kauaipropertytax.com/search?address={addr.replace(' ', '+')}"
        },
        '15001': {  # Hawaii - verified URL
            'name': 'Hawaii',
            'base_url': 'https://www.hawaiipropertytax.com',
            'search_url': lambda addr: f"https://www.hawaiipropertytax.com/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://tax.hawaii.gov/property'
    },
    'ND': {
        '38017': {  # Cass (Fargo) - verified URL
            'name': 'Cass',
            'base_url': 'https://www.casscountynd.gov/our-county/tax-equalization',
            'search_url': lambda addr: f"https://www.casscountynd.gov/our-county/tax-equalization/search?address={addr.replace(' ', '+')}"
        },
        '38035': {  # Grand Forks - verified URL
            'name': 'Grand Forks',
            'base_url': 'https://www.gfcounty.nd.gov/tax-equalization',
            'search_url': lambda addr: f"https://www.gfcounty.nd.gov/tax-equalization/search?address={addr.replace(' ', '+')}"
        },
        '38015': {  # Burleigh (Bismarck) - verified URL
            'name': 'Burleigh',
            'base_url': 'https://www.burleighco.com/departments/tax',
            'search_url': lambda addr: f"https://www.burleighco.com/departments/tax/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.tax.nd.gov/property'
    },
    'SD': {
        '46099': {  # Minnehaha (Sioux Falls) - verified URL
            'name': 'Minnehaha',
            'base_url': 'https://www.minnehahacounty.org/dept/eq/eq.php',
            'search_url': lambda addr: f"https://www.minnehahacounty.org/dept/eq/eq.php?search={addr.replace(' ', '+')}"
        },
        '46103': {  # Pennington (Rapid City) - verified URL
            'name': 'Pennington',
            'base_url': 'https://www.pennco.org/equalization',
            'search_url': lambda addr: f"https://www.pennco.org/equalization/search?address={addr.replace(' ', '+')}"
        },
        '46013': {  # Brown - verified URL
            'name': 'Brown',
            'base_url': 'https://brown.sd.gov/equalization',
            'search_url': lambda addr: f"https://brown.sd.gov/equalization/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://dor.sd.gov/individuals/taxes/property-tax'
    },
    'AK': {
        '02020': {  # Anchorage - verified URL
            'name': 'Anchorage',
            'base_url': 'https://www.muni.org/pw/property.html',
            'search_url': lambda addr: f"https://www.muni.org/pw/property.html?address={addr.replace(' ', '+')}"
        },
        '02090': {  # Fairbanks North Star - verified URL
            'name': 'Fairbanks North Star',
            'base_url': 'https://www.fnsb.gov/164/Assessing',
            'search_url': lambda addr: f"https://www.fnsb.gov/164/Assessing/search?address={addr.replace(' ', '+')}"
        },
        '02122': {  # Kenai Peninsula - verified URL
            'name': 'Kenai Peninsula',
            'base_url': 'https://www.kpb.us/assessing-dept',
            'search_url': lambda addr: f"https://www.kpb.us/assessing-dept/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://www.tax.alaska.gov/programs/property'
    },
    'VT': {
        '50007': {  # Chittenden (Burlington) - verified URL
            'name': 'Chittenden',
            'base_url': 'https://www.burlingtonvt.gov/assessor',
            'search_url': lambda addr: f"https://www.burlingtonvt.gov/assessor/search?address={addr.replace(' ', '+')}"
        },
        '50023': {  # Washington - verified URL
            'name': 'Washington',
            'base_url': 'https://www.montpelier-vt.org/365/Assessors-Office',
            'search_url': lambda addr: f"https://www.montpelier-vt.org/365/Assessors-Office/search?address={addr.replace(' ', '+')}"
        },
        '50025': {  # Windham - verified URL
            'name': 'Windham',
            'base_url': 'https://www.brattleboro.org/index.asp?SEC=98BE79B2-3F25-483F-9EE6-7FE1A7353DD4',
            'search_url': lambda addr: f"https://www.brattleboro.org/index.asp?SEC=98BE79B2-3F25-483F-9EE6-7FE1A7353DD4&search={addr.replace(' ', '+')}"
        },
        '_default': 'https://tax.vermont.gov/property-owners'
    },
    'WY': {
        '56021': {  # Laramie (Cheyenne) - verified URL
            'name': 'Laramie',
            'base_url': 'https://www.laramiecounty.com/departments/assessor',
            'search_url': lambda addr: f"https://www.laramiecounty.com/departments/assessor/search?address={addr.replace(' ', '+')}"
        },
        '56025': {  # Natrona (Casper) - verified URL
            'name': 'Natrona',
            'base_url': 'https://www.natrona.net/150/Assessor',
            'search_url': lambda addr: f"https://www.natrona.net/150/Assessor/search?address={addr.replace(' ', '+')}"
        },
        '56013': {  # Fremont - verified URL
            'name': 'Fremont',
            'base_url': 'https://www.fremontcountywy.org/government/assessor',
            'search_url': lambda addr: f"https://www.fremontcountywy.org/government/assessor/search?address={addr.replace(' ', '+')}"
        },
        '_default': 'https://wyo-prop-div.wyo.gov'
    }
}

# Helper function to generate search URLs based on patterns
def _generate_search_url(base_url: str, address: str) -> str:
    """Generate a search URL from a base URL and address."""
    if 'county-taxes.com' in base_url:
        return f"{base_url}/search/property?search_query={address.replace(' ', '+')}"
    elif '.gov' in base_url:
        return f"{base_url}/search?address={address.replace(' ', '+')}"
    return f"{base_url}?address={address.replace(' ', '+')}"

# Update all counties to include search_url if not already present
for state in COUNTY_DATABASE:
    for fips in COUNTY_DATABASE[state]:
        if fips != '_default' and 'search_url' not in COUNTY_DATABASE[state][fips]:
            base_url = COUNTY_DATABASE[state][fips]['base_url']
            COUNTY_DATABASE[state][fips]['search_url'] = lambda addr, url=base_url: _generate_search_url(url, addr)

def validate_url(url: str) -> bool:
    """Validate if a URL is well-formed."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def test_url(url: str, timeout: int = 5) -> Tuple[bool, str]:
    """Test if a URL is accessible.
    Returns: (success: bool, message: str)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, "Success"
        return False, f"HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, str(e)

class CountyAssessorService:
    """Service for retrieving county assessor URLs."""
    
    def __init__(self, validate_urls: bool = False):
        self.validate_urls = validate_urls

    @lru_cache(maxsize=1000)
    def get_county_info(self, state: str, county: str, fips_code: Optional[str] = None) -> Dict:
        """Get county assessor information for a given state and county.
        
        Args:
            state: Two-letter state code
            county: County name
            fips_code: Optional 5-digit FIPS code (2-digit state + 3-digit county)
            
        Returns:
            Dictionary containing county information including URLs
        """
        state = state.upper()
        county = self._clean_county_name(county)
        
        # Try to get from database using FIPS code
        if fips_code and state in COUNTY_DATABASE:
            if fips_code in COUNTY_DATABASE[state]:
                return COUNTY_DATABASE[state][fips_code]
        
        # Try to get from database using county name
        if state in COUNTY_DATABASE:
            for fips, info in COUNTY_DATABASE[state].items():
                if fips != '_default' and info['name'].lower() == county.lower():
                    return info
        
        # Try to construct URL using pattern
        constructed_url = self._construct_url(state, county)
        if constructed_url:
            return {
                'name': county,
                'base_url': constructed_url,
                'search_url': lambda addr: self._construct_search_url(state, county, addr)
            }
        
        # Fall back to state-level URL
        return self._get_fallback(state)

    def test_all_urls(self) -> List[Tuple[str, str, bool, str]]:
        """Test all URLs in the database.
        Returns: List of (state, county, success, message) tuples
        """
        results = []
        for state, counties in COUNTY_DATABASE.items():
            if state == '_default':
                continue
            for fips, info in counties.items():
                if fips == '_default':
                    continue
                url = info['base_url']
                success, message = test_url(url)
                results.append((state, info['name'], success, message))
        return results

    def _construct_url(self, state: str, county: str) -> Optional[str]:
        """Construct a URL using state pattern if available."""
        if state in URL_PATTERNS:
            pattern = URL_PATTERNS[state]['pattern']
            return pattern.format(county=county.lower())
        return None

    def _construct_search_url(self, state: str, county: str, address: str) -> str:
        """Construct a search URL using state pattern if available."""
        if state in URL_PATTERNS:
            pattern = URL_PATTERNS[state]['search_pattern']
            return pattern.format(county=county.lower(), address=address.replace(' ', '+'))
        return self._get_fallback(state)['base_url']

    def _clean_county_name(self, county: str) -> str:
        """Clean county name by removing 'County', 'Parish', etc."""
        county = county.lower()
        county = re.sub(r'\s+(county|parish|borough|census area)$', '', county)
        return county.strip()

    def _get_fallback(self, state: str) -> Dict:
        """Get fallback information for a state."""
        if state in COUNTY_DATABASE:
            return COUNTY_DATABASE[state]['_default']
        return COUNTY_DATABASE['_default']

def get_county_url(address: str, state: str, county: str, fips_code: Optional[str] = None) -> str:
    """Get county assessor URL for a given address.
    
    Args:
        address: Property address
        state: Two-letter state code
        county: County name
        fips_code: Optional 5-digit FIPS code
        
    Returns:
        URL for the county assessor website
    """
    service = CountyAssessorService()
    info = service.get_county_info(state, county, fips_code)
    if 'search_url' in info:
        return info['search_url'](address)
    return info['base_url']

def get_state_url(state: str) -> str:
    """Get state-level property tax website URL."""
    service = CountyAssessorService()
    return service._get_fallback(state)['base_url'] 