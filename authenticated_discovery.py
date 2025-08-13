#!/usr/bin/env python3
"""
Authenticated URL Discovery using crawl_url with authentication headers
"""

import os
import sys
import json
import time
sys.path.insert(0, 'src')

from auth.login_broker import LoginBroker
from config.settings import Settings
from firecrawl import FirecrawlApp
from firecrawl.firecrawl import ScrapeOptions

def discover_authenticated_urls():
    """Discover URLs using authenticated crawling"""
    
    print("🕷️ Authenticated URL Discovery")
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
    
    # Step 2: Initialize Firecrawl
    print("\n🔥 Step 2: Initializing Firecrawl...")
    settings = Settings()
    
    try:
        firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
        print("✅ Firecrawl initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Firecrawl: {e}")
        return False
    
    # Step 3: Authenticated crawling configurations
    print("\n🕷️ Step 3: Authenticated crawling...")
    
    base_url = settings.base_url
    print(f"📍 Base URL: {base_url}")
    
    # Prepare authenticated headers
    auth_headers = settings.get_firecrawl_headers(cookie_header)
    print(f"🔑 Using headers: {list(auth_headers.keys())}")
    
    # Different crawling strategies for authenticated discovery
    crawl_configs = [
        {
            "name": "Root Discovery (Limited)",
            "params": {
                "url": base_url,
                "limit": 50,
                "scrape_options": ScrapeOptions(
                    formats=["markdown", "links"],
                    headers=auth_headers,
                    waitFor=3000,
                    timeout=30000,
                    onlyMainContent=True
                ),
                "max_depth": 2,
                "delay": 1000  # 1 second delay between requests
            }
        },
        {
            "name": "Deep Discovery (Broader)",
            "params": {
                "url": base_url,
                "limit": 200,
                "scrape_options": ScrapeOptions(
                    formats=["markdown", "links"],
                    headers=auth_headers,
                    onlyMainContent=True,
                    waitFor=2000,
                    timeout=25000
                ),
                "include_paths": ["^/.*$"],  # All paths
                "exclude_paths": [".*\\.(?:pdf|zip|exe|dmg)$"],  # Exclude files
                "max_depth": 3,
                "delay": 1000
            }
        },
        {
            "name": "Targeted Discovery (Recipes/Products)",
            "params": {
                "url": base_url,
                "limit": 100,
                "scrape_options": ScrapeOptions(
                    formats=["markdown", "links"],
                    headers=auth_headers,
                    onlyMainContent=True,
                    waitFor=2000,
                    timeout=20000
                ),
                "include_paths": ["^/(receitas|produtos|recipes|products)/.*$"],
                "max_depth": 2,
                "delay": 1500
            }
        }
    ]
    
    all_results = {}
    
    for config in crawl_configs:
        print(f"\n🎯 Running: {config['name']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            print("🚀 Starting crawl...")
            result = firecrawl.crawl_url(**config['params'])
            
            elapsed = time.time() - start_time
            print(f"⏱️ Completed in {elapsed:.1f} seconds")
            
            if hasattr(result, 'success') and result.success:
                crawl_data = getattr(result, 'data', [])
                total_urls = len(crawl_data) if crawl_data else 0
                
                print(f"✅ Success! Discovered {total_urls} URLs")
                
                # Extract URLs from crawl data
                discovered_urls = []
                if crawl_data:
                    for item in crawl_data:
                        if hasattr(item, 'metadata') and hasattr(item.metadata, 'sourceURL'):
                            discovered_urls.append(item.metadata.sourceURL)
                        elif hasattr(item, 'url'):
                            discovered_urls.append(item.url)
                
                all_results[config['name']] = {
                    'success': True,
                    'url_count': total_urls,
                    'discovered_urls': discovered_urls,
                    'config': config['params'],
                    'elapsed_time': elapsed
                }
                
                # Show sample URLs
                if discovered_urls:
                    print("📄 Sample URLs discovered:")
                    for i, url in enumerate(discovered_urls[:5]):
                        print(f"  {i+1}. {url}")
                    if len(discovered_urls) > 5:
                        print(f"  ... and {len(discovered_urls) - 5} more")
                        
            else:
                error_msg = getattr(result, 'error', 'Unknown error')
                print(f"❌ Failed: {error_msg}")
                all_results[config['name']] = {
                    'success': False,
                    'error': error_msg,
                    'config': config['params'],
                    'elapsed_time': elapsed
                }
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Exception during crawl: {e}")
            all_results[config['name']] = {
                'success': False,
                'error': str(e),
                'config': config['params'],
                'elapsed_time': elapsed
            }
    
    # Step 4: Aggregate and save results
    print(f"\n💾 Step 4: Processing and saving results...")
    
    # Collect all unique URLs
    all_discovered_urls = set()
    for result in all_results.values():
        if result.get('success') and 'discovered_urls' in result:
            all_discovered_urls.update(result['discovered_urls'])
    
    # Convert datetime to string for JSON serialization
    expires_at = session_result.get('expires_at', 'Unknown')
    if hasattr(expires_at, 'isoformat'):
        expires_at = expires_at.isoformat()
    
    # Create comprehensive summary
    summary = {
        'discovery_method': 'authenticated_crawl',
        'timestamp': str(expires_at),
        'base_url': base_url,
        'total_unique_urls': len(all_discovered_urls),
        'discovered_urls': sorted(list(all_discovered_urls)),
        'detailed_results': all_results,
        'authentication': {
            'cookies_used': True,
            'cookie_count': len(session_result.get('cookies', [])),
            'session_cookies': session_result.get('session_cookies', [])
        },
        'success_rate': sum(1 for r in all_results.values() if r.get('success')) / len(all_results)
    }
    
    # Save to JSON file
    output_file = 'authenticated_discovery_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Results saved to: {output_file}")
    
    # Step 5: Analysis and Summary
    print(f"\n📊 DISCOVERY SUMMARY")
    print("=" * 50)
    print(f"🌐 Base URL: {base_url}")
    print(f"🔗 Total unique URLs discovered: {len(all_discovered_urls)}")
    print(f"🔐 Authentication: Fresh cookies used")
    print(f"📈 Success rate: {summary['success_rate']:.1%}")
    print(f"💾 Results saved to: {output_file}")
    
    # Analyze URL patterns
    if all_discovered_urls:
        print(f"\n📋 URL Patterns Discovered:")
        patterns = {}
        for url in all_discovered_urls:
            if base_url in url:
                path = url.replace(base_url, '').lstrip('/')
                if '?' in path:
                    path = path.split('?')[0]  # Remove query params
                pattern = path.split('/')[0] if '/' in path else path
                if not pattern:
                    pattern = 'root'
                patterns[pattern] = patterns.get(pattern, 0) + 1
        
        for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  /{pattern}: {count} URLs")
        
        # Show specific URL examples by pattern
        print(f"\n📝 URL Examples by Pattern:")
        pattern_examples = {}
        for url in sorted(all_discovered_urls):
            if base_url in url:
                path = url.replace(base_url, '').lstrip('/')
                if '?' in path:
                    path = path.split('?')[0]
                pattern = path.split('/')[0] if '/' in path else 'root'
                if pattern not in pattern_examples:
                    pattern_examples[pattern] = []
                if len(pattern_examples[pattern]) < 3:  # Max 3 examples per pattern
                    pattern_examples[pattern].append(url)
        
        for pattern, examples in pattern_examples.items():
            print(f"  /{pattern}:")
            for example in examples:
                print(f"    • {example}")
    
    return len(all_discovered_urls) > 0

if __name__ == "__main__":
    success = discover_authenticated_urls()
    if success:
        print("\n🎉 Authenticated URL discovery completed successfully!")
    else:
        print("\n❌ Authenticated URL discovery failed.")