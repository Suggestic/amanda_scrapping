#!/usr/bin/env python3
"""
Create a comprehensive mapsite of the authenticated website
"""

import os
import sys
import json
sys.path.insert(0, 'src')

from auth.login_broker import LoginBroker
from config.settings import Settings
from firecrawl import FirecrawlApp

def create_authenticated_mapsite():
    """Create a mapsite using fresh authentication cookies"""
    
    print("🗺️ Creating Authenticated Mapsite")
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
    print(f"🍪 Expires at: {session_result.get('expires_at', 'Unknown')}")
    
    # Step 2: Initialize Firecrawl with authentication
    print("\n🔥 Step 2: Initializing Firecrawl...")
    settings = Settings()
    
    try:
        firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
        print("✅ Firecrawl initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Firecrawl: {e}")
        return False
    
    # Step 3: Create comprehensive mapsite
    print("\n🗺️ Step 3: Creating mapsite...")
    
    base_url = settings.base_url
    print(f"📍 Mapping URL: {base_url}")
    
    # Prepare headers with authentication
    headers = settings.get_firecrawl_headers(cookie_header)
    print(f"🔑 Using headers: {list(headers.keys())}")
    
    # Try mapping with different configurations
    # NOTE: map_url does NOT support authentication headers!
    print("⚠️ Note: map_url doesn't support authentication - discovering public URLs only")
    
    mapping_configs = [
        {
            "name": "Public Sitemap Only",
            "params": {
                "url": base_url,
                "sitemap_only": True,
                "include_subdomains": False,
                "timeout": 30000
            }
        },
        {
            "name": "Public Deep Map (Limited)",
            "params": {
                "url": base_url,
                "include_subdomains": False,
                "ignore_sitemap": False,
                "limit": 100,
                "timeout": 30000
            }
        },
        {
            "name": "Public Deep Map (Extended)",
            "params": {
                "url": base_url,
                "include_subdomains": False,
                "ignore_sitemap": False,
                "limit": 500,
                "timeout": 60000
            }
        }
    ]
    
    all_results = {}
    
    for config in mapping_configs:
        print(f"\n🎯 Trying: {config['name']}")
        print("-" * 30)
        
        try:
            result = firecrawl.map_url(**config['params'])
            
            if hasattr(result, 'success') and result.success:
                links = getattr(result, 'links', [])
                print(f"✅ Success! Found {len(links)} URLs")
                
                all_results[config['name']] = {
                    'success': True,
                    'url_count': len(links),
                    'links': links,
                    'config': config['params']
                }
                
                # Show sample URLs
                if links:
                    print("📄 Sample URLs:")
                    for i, link in enumerate(links[:5]):
                        print(f"  {i+1}. {link}")
                    if len(links) > 5:
                        print(f"  ... and {len(links) - 5} more")
                        
            else:
                error_msg = getattr(result, 'error', 'Unknown error')
                print(f"❌ Failed: {error_msg}")
                all_results[config['name']] = {
                    'success': False,
                    'error': error_msg,
                    'config': config['params']
                }
                
        except Exception as e:
            print(f"❌ Exception during mapping: {e}")
            all_results[config['name']] = {
                'success': False,
                'error': str(e),
                'config': config['params']
            }
    
    # Step 4: Save results
    print(f"\n💾 Step 4: Saving mapsite results...")
    
    # Create results summary
    total_unique_urls = set()
    for result in all_results.values():
        if result.get('success') and 'links' in result:
            total_unique_urls.update(result['links'])
    
    # Convert datetime to string for JSON serialization
    expires_at = session_result.get('expires_at', 'Unknown')
    if hasattr(expires_at, 'isoformat'):
        expires_at = expires_at.isoformat()
    
    summary = {
        'timestamp': str(expires_at),
        'base_url': base_url,
        'total_unique_urls': len(total_unique_urls),
        'unique_urls': sorted(list(total_unique_urls)),
        'detailed_results': all_results,
        'authentication': {
            'cookies_used': True,
            'cookie_count': len(session_result.get('cookies', [])),
            'session_cookies': session_result.get('session_cookies', []),
            'note': 'map_url does not support authentication headers'
        },
        'limitations': {
            'map_url_no_auth': True,
            'public_urls_only': True,
            'recommendation': 'Use authenticated crawl for protected content discovery'
        }
    }
    
    # Save to JSON file
    output_file = 'mapsite_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Results saved to: {output_file}")
    
    # Step 5: Summary
    print(f"\n📊 MAPSITE SUMMARY")
    print("=" * 50)
    print(f"🌐 Base URL: {base_url}")
    print(f"🔗 Total unique URLs found: {len(total_unique_urls)}")
    print(f"🔐 Authentication: Used cookies from fresh login")
    print(f"💾 Results saved to: {output_file}")
    
    # Show URL patterns
    if total_unique_urls:
        print(f"\n📋 URL Patterns Found:")
        patterns = {}
        for url in total_unique_urls:
            # Extract path pattern
            if base_url in url:
                path = url.replace(base_url, '').lstrip('/')
                pattern = path.split('/')[0] if '/' in path else path
                if not pattern:
                    pattern = 'root'
                patterns[pattern] = patterns.get(pattern, 0) + 1
        
        for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  /{pattern}: {count} URLs")
    
    # Suggest authenticated discovery alternatives
    print(f"\n🔍 ALTERNATIVE: Authenticated URL Discovery")
    print("-" * 50)
    print("Since map_url doesn't support authentication, consider:")
    print("1. 🕷️ Use crawl_url with authentication headers for deep discovery")
    print("2. 🔗 Start from known authenticated URLs and follow links")
    print("3. 📋 Manual sitemap.xml inspection with authenticated requests")
    print("4. 🎯 Target specific URL patterns (e.g., /receitas/, /produtos/)")
    
    return len(total_unique_urls) > 0

if __name__ == "__main__":
    success = create_authenticated_mapsite()
    if success:
        print("\n🎉 Mapsite creation completed successfully!")
    else:
        print("\n❌ Mapsite creation failed.")