from bs4 import BeautifulSoup
import urllib.parse
import time
import curler
import mongo
from typing import Dict, List, Any

def process_html_content(content: str, base_url: str) -> Dict[str, Any]:
    """
    Parses HTML content once and extracts all relevant information.
    """
    # Parse the content only once
    soup = BeautifulSoup(content, 'html.parser')

    # Get all information from the single parsed object
    processed_data = {
        "title": _get_title(soup),
        "meta_description": _get_meta_description(soup),
        "metadata": _get_metadata(soup),
        "extracted_urls": _get_urls(soup, base_url),
        "images_info": _get_images(soup, base_url),
        "text_content": _get_page_text(soup)
    }

    return processed_data

def _get_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    urls = []
    for link in soup.find_all('a', href=True):
        abs_url = urllib.parse.urljoin(base_url, link['href'])
        urls.append(abs_url)
    return urls

def _get_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find('title')
    return title_tag.string if title_tag else 'No title found'

def _get_meta_description(soup: BeautifulSoup) -> str:
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    return meta_tag['content'] if meta_tag and 'content' in meta_tag.attrs else 'No description found'

def _get_page_text(soup: BeautifulSoup) -> str:
    for tag in ['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'img']:
        for element in soup.find_all(tag):
            element.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return text

def _get_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    metadata = {}
    for meta in soup.find_all('meta'):
        if 'name' in meta.attrs and 'content' in meta.attrs:
            metadata[meta['name']] = meta['content']
        elif 'property' in meta.attrs and 'content' in meta.attrs:
            metadata[meta['property']] = meta['content']
    return metadata

def _get_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
    import mongo  # Import here to avoid circular dependency
    db = mongo.connect_to_mongo()
    images = []
    for img in soup.find_all('img', src=True):
        if not img['src']:
            continue
        abs_url = urllib.parse.urljoin(base_url, img['src'])

        if mongo.get_image_by_url_count(db, abs_url) > 0:
            continue

        images.append({
            "url": abs_url,
            "alt_text": img.get('alt', None),
            "title": img.get('title', None),
            "width": int(img.get('width')) if img.get('width') and img.get('width').isdigit() else None,
            "height": int(img.get('height')) if img.get('height') and img.get('height').isdigit() else None,
            "file_size": None,
            "format": None,
            "last_fetched": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        })
    return images