# models for mongo db storing of the html data

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from urllib import response

@dataclass
class WebPage:
    url: str
    redirected: bool = False
    redirect_url: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    text_content: Optional[str] = None
    extracted_urls: List[str] = field(default_factory=list)
    image_data: List[Dict[str, Any]] = field(default_factory=list)  # Changed this line
    metadata: Dict[str, str] = field(default_factory=dict)
    last_fetched: Optional[str] = None
    
@dataclass
class crawlTask:
    url: str
    status: str = "pending"  # could be 'pending', 'in_progress', 'completed', 'failed'
    attempts: int = 0
    last_attempted: Optional[str] = None  # ISO formatted date string
    error_message: Optional[str] = None

@dataclass
class webpageQueueItem:
    url: str
    webpage_content: str  # Store the HTML content as a string
    status_code: int = 200  # Store the HTTP status code
    redirected: bool = False
    redirect_url: Optional[str] = None