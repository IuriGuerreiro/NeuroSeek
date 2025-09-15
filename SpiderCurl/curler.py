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
            response.raise_for_status()  # Raise an error for bad responses
            return False, response, None
        except httpx.HTTPError as e:
            # if the error is a 301 redirect, we can ignore it
            if e.response is not None and e.response.status_code == 301:
                # curl the quoted url
                doesnt, response, matter = fetch_url(e.response.headers.get("Location"))
                return True, response, e.response.headers.get("Location")
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