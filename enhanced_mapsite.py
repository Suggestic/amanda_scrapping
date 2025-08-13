#!/usr/bin/env python3
"""
Enhanced Mapsite - Two-Phase URL Discovery
Phase 1: Run simple_mapsite.py to get baseline URLs
Phase 2: Intelligently follow key category pages for deeper discovery
"""

import os
import sys
import json
import re
from typing import List, Dict, Set
from collections import defaultdict
sys.path.insert(0, 'src')

from auth.login_broker import LoginBroker
from config.settings import Settings
from firecrawl import FirecrawlApp

class EnhancedMapsite:
    def __init__(self):
        self.settings = Settings()
        self.firecrawl = None
        self.session_cookies = None
        self.all_urls: Set[str] = set()
        self.category_stats = defaultdict(int)
        
    def initialize_session(self) -> bool:
        """Get fresh authentication cookies and initialize Firecrawl"""
        print("🔐 Initializing authenticated session...")
        
        # Get fresh cookies
        broker = LoginBroker()
        session_result = broker.acquire_session(headless=True)
        
        if not session_result or 'cookie_header' not in session_result:
            print("❌ Failed to get authentication cookies")
            return False
        
        self.session_cookies = session_result['cookie_header']
        print(f"✅ Got cookies: {len(self.session_cookies)} chars")
        
        # Initialize Firecrawl
        try:
            self.firecrawl = FirecrawlApp(api_key=self.settings.firecrawl_api_key)
            print("✅ Firecrawl initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Firecrawl: {e}")
            return False
    
    def run_simple_mapsite(self) -> List[str]:
        """Phase 1: Run the existing simple mapsite logic"""
        print("\n🗺️ PHASE 1: Simple Mapsite Discovery")
        print("=" * 50)
        
        base_url = self.settings.base_url
        auth_headers = self.settings.get_firecrawl_headers(self.session_cookies)
        
        try:
            print(f"🚀 Scraping base URL: {base_url}")
            result = self.firecrawl.scrape_url(
                url=base_url,
                formats=["links", "markdown"],
                headers=auth_headers,
                only_main_content=False,
                wait_for=3000,
                timeout=30000
            )
            
            if not (hasattr(result, 'links') and result.links):
                print("❌ No links found in base page")
                return []
            
            # Process links (same logic as simple_mapsite.py)
            base_domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
            simple_urls = []
            
            for link in result.links:
                if isinstance(link, dict):
                    url = link.get('href', link.get('url', ''))
                else:
                    url = str(link)
                
                if url:
                    # Handle relative URLs
                    if url.startswith('/'):
                        url = base_url.rstrip('/') + url
                    elif url.startswith('../'):
                        continue
                    elif not url.startswith('http'):
                        url = base_url.rstrip('/') + '/' + url.lstrip('/')
                    
                    # Keep only same-domain URLs
                    if base_domain in url and url not in simple_urls:
                        simple_urls.append(url)
            
            print(f"✅ Phase 1 complete: {len(simple_urls)} URLs found")
            
            # Add to master set
            self.all_urls.update(simple_urls)
            
            return simple_urls
            
        except Exception as e:
            print(f"❌ Phase 1 failed: {e}")
            return []
    
    def identify_category_pages(self, simple_urls: List[str]) -> List[Dict[str, str]]:
        """Identify key category pages that likely contain more links"""
        print("\n🎯 Identifying Category Pages for Deep Discovery")
        print("-" * 50)
        
        categories = []
        base_url = self.settings.base_url
        
        # Define category patterns and their priorities
        category_patterns = [
            {"pattern": r"/conteudos(?:/[^/]+)?/?$", "name": "content_categories", "priority": 1},
            {"pattern": r"/ead(?:/[^/]+)?/?$", "name": "education_categories", "priority": 1},
            {"pattern": r"/servicos(?:/[^/]+)?/?$", "name": "services", "priority": 2},
            {"pattern": r"/eventos", "name": "events", "priority": 3},
            {"pattern": r"/pwa", "name": "products", "priority": 2},
        ]
        
        for url in simple_urls:
            # Remove base URL to get path
            path = url.replace(base_url, '').rstrip('/')
            
            for pattern_info in category_patterns:
                if re.search(pattern_info["pattern"], path):
                    categories.append({
                        "url": url,
                        "path": path,
                        "category": pattern_info["name"],
                        "priority": pattern_info["priority"]
                    })
                    break
        
        # Sort by priority and limit to avoid overwhelming the system
        categories.sort(key=lambda x: (x["priority"], x["path"]))
        selected_categories = categories[:8]  # Limit to 8 category pages
        
        print(f"📋 Selected {len(selected_categories)} category pages for deep discovery:")
        for i, cat in enumerate(selected_categories, 1):
            print(f"  {i}. {cat['category']}: {cat['path']}")
        
        return selected_categories
    
    def scrape_category_page(self, category_info: Dict[str, str]) -> List[str]:
        """Scrape a single category page for additional links"""
        url = category_info["url"]
        category_name = category_info["category"]
        
        print(f"🔍 Scraping {category_name}: {category_info['path']}")
        
        auth_headers = self.settings.get_firecrawl_headers(self.session_cookies)
        
        try:
            result = self.firecrawl.scrape_url(
                url=url,
                formats=["links"],
                headers=auth_headers,
                only_main_content=False,
                wait_for=5000,  # Longer wait for category pages
                timeout=30000
            )
            
            if not (hasattr(result, 'links') and result.links):
                print(f"  ⚠️ No links found in {category_name}")
                return []
            
            # Process links
            base_url = self.settings.base_url
            base_domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
            category_urls = []
            
            for link in result.links:
                if isinstance(link, dict):
                    link_url = link.get('href', link.get('url', ''))
                else:
                    link_url = str(link)
                
                if link_url:
                    # Handle relative URLs
                    if link_url.startswith('/'):
                        link_url = base_url.rstrip('/') + link_url
                    elif link_url.startswith('../'):
                        continue
                    elif not link_url.startswith('http'):
                        link_url = base_url.rstrip('/') + '/' + link_url.lstrip('/')
                    
                    # Keep only same-domain URLs we haven't seen
                    if (base_domain in link_url and 
                        link_url not in self.all_urls and 
                        link_url not in category_urls):
                        category_urls.append(link_url)
            
            print(f"  ✅ Found {len(category_urls)} new URLs in {category_name}")
            self.category_stats[category_name] += len(category_urls)
            
            return category_urls
            
        except Exception as e:
            print(f"  ❌ Failed to scrape {category_name}: {e}")
            return []
    
    def run_deep_discovery(self, simple_urls: List[str]) -> List[str]:
        """Phase 2: Deep discovery from category pages"""
        print("\n🔬 PHASE 2: Deep Category Discovery")
        print("=" * 50)
        
        # Identify category pages
        categories = self.identify_category_pages(simple_urls)
        
        if not categories:
            print("⚠️ No category pages identified for deep discovery")
            return []
        
        # Scrape each category page
        new_urls = []
        for category_info in categories:
            category_urls = self.scrape_category_page(category_info)
            new_urls.extend(category_urls)
            self.all_urls.update(category_urls)
        
        print(f"\n✅ Phase 2 complete: {len(new_urls)} new URLs discovered")
        
        return new_urls
    
    def save_enhanced_results(self, simple_urls: List[str], deep_urls: List[str]):
        """Save comprehensive results with analysis"""
        print("\n💾 Saving Enhanced Mapsite Results")
        print("=" * 50)
        
        # Combine all URLs
        all_unique_urls = sorted(list(self.all_urls))
        
        # Create comprehensive results
        enhanced_results = {
            "method": "enhanced_two_phase_discovery",
            "timestamp": "2024-01-30T12:00:00",  # Will be updated with real timestamp
            "base_url": self.settings.base_url,
            "summary": {
                "total_urls": len(all_unique_urls),
                "phase1_urls": len(simple_urls),
                "phase2_new_urls": len(deep_urls),
                "improvement": len(deep_urls)
            },
            "phase_breakdown": {
                "phase1_simple_discovery": {
                    "method": "base_page_scraping",
                    "urls_found": len(simple_urls),
                    "description": "Links found on homepage"
                },
                "phase2_deep_discovery": {
                    "method": "category_page_scraping", 
                    "urls_found": len(deep_urls),
                    "description": "Additional links from category pages",
                    "categories_scraped": dict(self.category_stats)
                }
            },
            "all_urls": all_unique_urls,
            "authentication": {
                "cookies_used": True,
                "success": True
            }
        }
        
        # Save to file
        output_file = 'enhanced_mapsite.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Results saved to: {output_file}")
        
        # Display summary
        print(f"\n📊 ENHANCED MAPSITE SUMMARY")
        print("=" * 50)
        print(f"🌐 Base URL: {self.settings.base_url}")
        print(f"🔗 Total URLs: {len(all_unique_urls)}")
        print(f"📄 Phase 1 (Simple): {len(simple_urls)} URLs")
        print(f"🔬 Phase 2 (Deep): {len(deep_urls)} NEW URLs")
        print(f"📈 Improvement: +{len(deep_urls)} URLs ({len(deep_urls)/len(simple_urls)*100:.1f}% increase)")
        
        if self.category_stats:
            print(f"\n📂 Deep Discovery by Category:")
            for category, count in sorted(self.category_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {category}: +{count} URLs")
        
        return len(all_unique_urls)
    
    def run_enhanced_discovery(self) -> bool:
        """Main method: Run complete two-phase discovery"""
        print("🚀 Enhanced Mapsite - Two-Phase URL Discovery")
        print("=" * 60)
        
        # Initialize session
        if not self.initialize_session():
            return False
        
        # Phase 1: Simple discovery
        simple_urls = self.run_simple_mapsite()
        if not simple_urls:
            print("❌ Phase 1 failed - cannot proceed")
            return False
        
        # Phase 2: Deep discovery
        deep_urls = self.run_deep_discovery(simple_urls)
        
        # Save and analyze results
        total_urls = self.save_enhanced_results(simple_urls, deep_urls)
        
        print(f"\n🎉 Enhanced Mapsite Complete!")
        print(f"📊 Discovered {total_urls} total URLs")
        
        return True

def main():
    """Run enhanced mapsite discovery"""
    mapsite = EnhancedMapsite()
    success = mapsite.run_enhanced_discovery()
    
    if success:
        print("\n✅ Enhanced mapsite creation completed successfully!")
    else:
        print("\n❌ Enhanced mapsite creation failed.")
    
    return success

if __name__ == "__main__":
    main()
