#!/usr/bin/env python3
"""
Simple mapsite - just get URLs from the base page, no crawling
"""

import os
import sys
import json
import re
sys.path.insert(0, 'src')

from auth.login_broker import LoginBroker
from config.settings import Settings
from firecrawl import FirecrawlApp

def create_simple_mapsite():
    """Get URLs from the base page only - simple and direct"""
    
    print("🗺️ Simple Mapsite - Base Page URLs Only")
    print("=" * 50)
    
    # Step 1: Get fresh authentication cookies
    print("🔐 Step 1: Getting fresh authentication cookies...")
    broker = LoginBroker()
    session_result = broker.acquire_session(headless=True)
    
    if not session_result or 'cookie_header' not in session_result:
        print("❌ Failed to get authentication cookies")
        return False
    
    cookie_header = session_result['cookie_header']
    print(f"✅ Got cookies: {len(cookie_header)} chars")
    
    # Step 2: Initialize Firecrawl
    print("\n🔥 Step 2: Initializing Firecrawl...")
    settings = Settings()
    
    try:
        firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
        print("✅ Firecrawl initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Firecrawl: {e}")
        return False
    
    # Step 3: Scrape base URL to get links
    print("\n🌐 Step 3: Scraping base URL for links...")
    
    base_url = settings.base_url
    print(f"📍 Target URL: {base_url}")
    
    # Prepare authenticated headers
    auth_headers = settings.get_firecrawl_headers(cookie_header)
    print(f"🔑 Using headers: {list(auth_headers.keys())}")
    
    try:
        # Simple scrape with links format
        print("🚀 Scraping for links...")
        result = firecrawl.scrape_url(
            url=base_url,
            formats=["links", "markdown"],
            headers=auth_headers,
            only_main_content=False,  # Get all content to find all links
            wait_for=3000,
            timeout=30000
        )
        
        if hasattr(result, 'links') and result.links:
            links = result.links
            print(f"✅ Found {len(links)} links!")
            
            # Filter to keep only same-domain URLs
            base_domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
            same_domain_urls = []
            
            for link in links:
                if isinstance(link, dict):
                    url = link.get('href', link.get('url', ''))
                else:
                    url = str(link)
                
                # Clean and validate URL
                if url:
                    # Handle relative URLs
                    if url.startswith('/'):
                        url = base_url.rstrip('/') + url
                    elif url.startswith('../'):
                        continue  # Skip relative parent URLs
                    elif not url.startswith('http'):
                        url = base_url.rstrip('/') + '/' + url.lstrip('/')
                    
                    # Keep only same-domain URLs
                    if base_domain in url and url not in same_domain_urls:
                        same_domain_urls.append(url)
            
            print(f"🎯 Filtered to {len(same_domain_urls)} same-domain URLs")
            
            # Step 4: Save simple mapsite
            print("\n💾 Step 4: Saving simple mapsite...")
            
            # Convert datetime to string for JSON serialization
            expires_at = session_result.get('expires_at', 'Unknown')
            if hasattr(expires_at, 'isoformat'):
                expires_at = expires_at.isoformat()
            
            simple_mapsite = {
                'method': 'simple_scrape',
                'timestamp': str(expires_at),
                'base_url': base_url,
                'total_urls': len(same_domain_urls),
                'urls': sorted(same_domain_urls),
                'authentication': {
                    'cookies_used': True,
                    'success': True
                }
            }
            
            # Save to JSON file
            output_file = 'simple_mapsite.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(simple_mapsite, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Mapsite saved to: {output_file}")
            
            # Step 5: Display results
            print(f"\n📊 SIMPLE MAPSITE RESULTS")
            print("=" * 50)
            print(f"🌐 Base URL: {base_url}")
            print(f"🔗 Total URLs found: {len(same_domain_urls)}")
            print(f"💾 Saved to: {output_file}")
            
            # Show all URLs
            if same_domain_urls:
                print(f"\n📋 All URLs found:")
                for i, url in enumerate(same_domain_urls, 1):
                    print(f"  {i:2d}. {url}")
                
                # Simple pattern analysis
                print(f"\n📂 URL Patterns:")
                patterns = {}
                for url in same_domain_urls:
                    path = url.replace(base_url, '').lstrip('/')
                    if '?' in path:
                        path = path.split('?')[0]
                    pattern = path.split('/')[0] if '/' in path else (path if path else 'root')
                    patterns[pattern] = patterns.get(pattern, 0) + 1
                
                for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {pattern}: {count} URLs")
            
            return len(same_domain_urls) > 0
            
        else:
            print("❌ No links found in the scraped content")
            return False
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return False

if __name__ == "__main__":
    success = create_simple_mapsite()
    if success:
        print("\n🎉 Simple mapsite creation completed successfully!")
    else:
        print("\n❌ Simple mapsite creation failed.")