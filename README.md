# County Assessor URL Database

A comprehensive database of county tax assessor URLs for US counties, with support for direct property search where available.

## Features

- Database of verified county assessor URLs for major counties
- FIPS code support for unique county identification
- URL pattern templates for common county website structures
- State-level fallback URLs
- URL validation and testing utilities
- Caching for improved performance

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```python
from county_assessor_urls import CountyAssessorService, get_county_url

# Basic usage
url = get_county_url(
    address="123 Main St",
    state="FL",
    county="Miami-Dade",
    fips_code="12086"
)

# Create service instance with URL validation
service = CountyAssessorService(validate_urls=True)

# Get county info
info = service.get_county_info(
    state="FL",
    county="Miami-Dade",
    fips_code="12086"
)

# Test all URLs in database
results = service.test_all_urls()
for state, county, success, message in results:
    print(f"{state} - {county}: {'✓' if success else '✗'} ({message})")
```

## Database Structure

The database includes:
- Major counties in FL, NY, CA, TX, IL, AZ, CO, MA, NJ, MN, MO, OR
- State-level fallback URLs
- URL patterns for common county website structures

## Contributing

To add more counties or update URLs:
1. Update the `COUNTY_DATABASE` dictionary in `county_assessor_urls.py`
2. Add URL patterns to `URL_PATTERNS` if applicable
3. Run URL tests to verify changes

## License

MIT License 