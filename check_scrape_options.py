#!/usr/bin/env python3
"""
Check ScrapeOptions structure for authentication headers
"""

import os
import sys
sys.path.insert(0, 'src')

from firecrawl import FirecrawlApp
from firecrawl.firecrawl import ScrapeOptions

def check_scrape_options():
    """Check ScrapeOptions structure"""
    
    print("🔍 Checking ScrapeOptions structure:")
    print("=" * 50)
    
    try:
        # Check ScrapeOptions class
        if hasattr(ScrapeOptions, '__annotations__'):
            print("ScrapeOptions fields:")
            for field, field_type in ScrapeOptions.__annotations__.items():
                print(f"  {field}: {field_type}")
        
        # Try to create a ScrapeOptions instance to see what it accepts
        print("\n🧪 Testing ScrapeOptions creation with headers:")
        
        test_headers = {
            "Authorization": "Basic test",
            "User-Agent": "Test-Agent",
            "Cookie": "test=value"
        }
        
        try:
            scrape_opts = ScrapeOptions(
                headers=test_headers,
                formats=["markdown"],
                only_main_content=True
            )
            print("✅ ScrapeOptions created successfully with headers")
            print(f"Created object: {scrape_opts}")
        except Exception as e:
            print(f"❌ Failed to create ScrapeOptions with headers: {e}")
            
            # Try without headers
            try:
                scrape_opts = ScrapeOptions(
                    formats=["markdown"],
                    only_main_content=True
                )
                print("✅ ScrapeOptions created without headers")
                print(f"Available attributes: {dir(scrape_opts)}")
            except Exception as e2:
                print(f"❌ Failed to create ScrapeOptions at all: {e2}")
        
    except Exception as e:
        print(f"Error checking ScrapeOptions: {e}")

if __name__ == "__main__":
    check_scrape_options()