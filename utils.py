# Modifyies url for direct download as User Content
from urllib.parse import urlparse, parse_qs

def transform_google_drive_url(url):
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Extract the query parameters
    query_params = parse_qs(parsed_url.query)
    
    # Check if 'view' or 'open' parameter is present
    if 'view' in query_params:
        query_params.pop('view')
    if 'open' in query_params:
        query_params.pop('open')
    
    # Add 'uc' parameter
    query_params['export'] = 'uc'
    
    # Construct the modified URL
    modified_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + "&".join([f"{key}={value[0]}" for key, value in query_params.items()])
    
    return modified_url
