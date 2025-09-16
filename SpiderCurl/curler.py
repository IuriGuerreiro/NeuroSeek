import requests
import asyncio
import httpx

def fetch_url(url):
    with httpx.Client() as client:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = client.get(url, headers=headers)
            response.raise_for_status()
            
            # Check if the response is HTML - if not, skip it
            content_type = response.headers.get('Content-Type', '').lower()
            if not (content_type.startswith('text/html') or 
                    content_type.startswith('application/xhtml') or 
                    content_type.startswith('application/xml') or
                    'text/' in content_type):
                print(f"Skipping non-HTML URL: {url} (Content-Type: {content_type})")
                return False, None, None
            
            return False, response, None
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (4xx, 5xx)
            if e.response.status_code == 301 or e.response.status_code == 302:
                redirect_url = e.response.headers.get("Location")
                if redirect_url:
                    doesnt, response, matter = fetch_url(redirect_url)  # Recursively follow redirect
                    return True, response, redirect_url
            print(f"HTTP {e.response.status_code} error for {url}")
            return False, None, None
        except (httpx.UnsupportedProtocol, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            print(f"Network error for {url}: {type(e).__name__}")
            return False, None, None
        except Exception as e:
            print(f"Unexpected error for {url}: {e}")
            return False, None, None

def get_image_size(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        # Use a HEAD request to only fetch headers
        response = requests.head(url, headers=headers)
        # Raise an exception for bad status codes
        response.raise_for_status()

        # Check for the Content-Length header
        if 'Content-Length' in response.headers:
            size_in_bytes = int(response.headers['Content-Length'])
        else:
            print("Content-Length header not found.")
        
        if 'Content-Type' in response.headers:
            content_type = response.headers['Content-Type']
            # MIME types for images typically start with 'image/'
            if content_type.startswith('image/'):
                image_format = content_type.split('/')[-1]
            else:
                print(f"URL content is not an image (Content-Type: {content_type})")
        return size_in_bytes , image_format
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None