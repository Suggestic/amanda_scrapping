"""
Configuration management for Amanda Scrapping.
Loads settings from environment variables with proper validation.
"""

import os
import base64
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Pantheon Basic Auth credentials
        self.pantheon_username: str = os.getenv('PANTHEON_USERNAME', '')
        self.pantheon_password: str = os.getenv('PANTHEON_PASSWORD', '')
        
        # Application login credentials
        self.app_email: str = os.getenv('APP_EMAIL', '')
        self.app_password: str = os.getenv('APP_PASSWORD', '')
        
        # Site configuration
        self.base_url: str = os.getenv('BASE_URL', '')
        self.user_agent: str = os.getenv('USER_AGENT', 
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nestle-Scraper/1.0')
        
        # Firecrawl configuration
        self.firecrawl_api_key: str = os.getenv('FIRECRAWL_API_KEY', '')
        self.zero_data_retention: bool = os.getenv('ZERO_DATA_RETENTION', 'true').lower() == 'true'
        
        # Logging
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        
        # Validate required settings
        self._validate()
    
    def _validate(self):
        """Validate that required environment variables are set."""
        required_fields = [
            ('PANTHEON_USERNAME', self.pantheon_username),
            ('PANTHEON_PASSWORD', self.pantheon_password),
            ('APP_EMAIL', self.app_email),
            ('APP_PASSWORD', self.app_password),
            ('BASE_URL', self.base_url),
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    @property
    def basic_auth_header(self) -> str:
        """Generate the Basic Authorization header for Pantheon shield."""
        credentials = f"{self.pantheon_username}:{self.pantheon_password}"
        encoded = base64.b64encode(credentials.encode()).decode('ascii')
        return f"Basic {encoded}"
    
    @property
    def login_url(self) -> str:
        """Get the login URL for the application."""
        return f"{self.base_url}/login?destination=/"
    
    def get_firecrawl_headers(self, cookie_header: Optional[str] = None) -> dict:
        """
        Get headers for Firecrawl requests.
        
        Args:
            cookie_header: Optional session cookies string
            
        Returns:
            Dict of headers including Basic auth, User-Agent, and optionally cookies
        """
        headers = {
            "Authorization": self.basic_auth_header,
            "User-Agent": self.user_agent,
        }
        
        if cookie_header:
            headers["Cookie"] = cookie_header
            
        return headers

# Global settings instance
settings = Settings()