# models for mongo db storing of the html data

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ImageData:
    url: str
    alt_text: Optional[str] = None
    title: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None  # in bytes
    format: Optional[str] = None  # e.g., 'jpeg', 'png'
    last_fetched: Optional[str] = None  # ISO formatted date string


@dataclass
class WebPage:
    url: str
    redirected: bool = False
    redirect_url: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    text_content: Optional[str] = None
    extracted_urls: List[str] = field(default_factory=list)
    image_data: List[ImageData] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    last_fetched: Optional[str] = None  # ISO formatted date string

@dataclass
class crawlTask:
    url: str
    status: str = "pending"  # could be 'pending', 'in_progress', 'completed', 'failed'
    attempts: int = 0
    last_attempted: Optional[str] = None  # ISO formatted date string
    error_message: Optional[str] = None