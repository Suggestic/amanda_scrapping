#!/usr/bin/env python3
"""
Check what parameters crawl_url actually supports
"""

import os
import sys
sys.path.insert(0, 'src')

from firecrawl import FirecrawlApp

def check_crawl_params():
    """Check crawl_url method signature"""
    
    os.environ['FIRECRAWL_API_KEY'] = 'dummy_key_for_inspection'
    
    try:
        firecrawl = FirecrawlApp(api_key='dummy_key_for_inspection')
        
        print("🕷️ Checking crawl_url method signature:")
        print("=" * 50)
        
        if hasattr(firecrawl, 'crawl_url'):
            help(firecrawl.crawl_url)
        else:
            print("❌ crawl_url method not found")
            
        # Also check for any other crawling methods
        methods = [method for method in dir(firecrawl) if 'crawl' in method.lower()]
        print(f"\n🔍 All crawl-related methods: {methods}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_crawl_params()