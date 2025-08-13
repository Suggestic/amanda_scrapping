#!/usr/bin/env python3
"""
Ultra-Deep Mapsite Discovery - Comprehensive Site Crawling
4-Phase Discovery System for Maximum Content Coverage
"""

import os
import sys
import json
import re
import time
import hashlib
import threading
from typing import List, Dict, Set, Tuple, Optional
from collections import deque, defaultdict
from urllib.parse import urljoin, urlparse
from pathlib import Path
sys.path.insert(0, 'src')

from auth.login_broker import LoginBroker
from config.settings import Settings
from firecrawl import FirecrawlApp

class ContentClassifier:
    """Classifies URLs by content type and priority"""
    
    def __init__(self, base_domain: str):
        self.base_domain = base_domain
        
        # High priority content patterns (always follow)
        self.high_priority_patterns = [
            r"/ead(/.*)?$",                          # Education/courses
            r"/conteudos(/.*)?$",                    # Content/articles
            r"/educacao-a-distancia(/.*)?$",         # Distance learning
            r"/servicos(/.*)?$",                     # Services/tools
            r"/eventos(/.*)?$",                      # Events
            r"/pwa/produtos(/.*)?$",                 # Products
            r"/podcast(/.*)?$",                      # Podcasts
            r"/receitas(/.*)?$",                     # Recipes
            r"/calculadoras(/.*)?$",                 # Calculators
            r"/acervo(/.*)?$",                       # Library/archive
        ]
        
        # Medium priority patterns (follow selectively)
        self.medium_priority_patterns = [
            r"/sobre-nos",                           # About us
            r"/perguntas-frequentes",                # FAQ
            r"/cadastro",                            # Registration
            r"/meus-cursos",                         # My courses
            r"/meus-certificados",                   # My certificates
        ]
        
        # File download patterns (HIGH PRIORITY - valuable content!)
        self.file_download_patterns = [
            r"\.(pdf|doc|docx|ppt|pptx|xls|xlsx)$",  # Documents
            r"\.(zip|rar|tar|gz)$",                  # Archives
            r"\.(mp4|mp3|avi|mov|wmv)$",             # Media files
            r"/download/",                           # Download directories
            r"/materials/",                          # Materials/resources
            r"/recursos/",                           # Resources (Portuguese)
            r"/arquivos/",                           # Files (Portuguese)
        ]
        
        # Exclude patterns (never follow)
        self.exclude_patterns = [
            r"^tel:",                                # Phone links
            r"^mailto:",                             # Email links
            r"^#",                                   # Anchor links only
            r"/user/logout",                         # Logout links
            r"utm_source=",                          # Tracking URLs
            r"facebook\.com|twitter\.com|instagram\.com|linkedin\.com",  # Social media
        ]
    
    def classify_url(self, url: str) -> Tuple[str, int]:
        """
        Classify URL and return (category, priority)
        Priority: 1=high, 2=medium, 0=exclude
        """
        if not url or not url.startswith('http'):
            return "invalid", 0
        
        # Check if same domain
        parsed = urlparse(url)
        if self.base_domain not in parsed.netloc:
            return "external", 0
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return "excluded", 0
        
        # Check file download patterns (HIGH PRIORITY!)
        for pattern in self.file_download_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return "file_downloads", 1  # High priority for downloads!
        
        # Check high priority patterns
        for pattern in self.high_priority_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                category = self._extract_category(pattern, url)
                return category, 1
        
        # Check medium priority patterns
        for pattern in self.medium_priority_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return "medium_priority", 1  # Changed to priority 1 - we want EVERYTHING!
        
        # EVERYTHING ELSE: Include all same-domain URLs (was priority 3, now priority 1)
        return "general", 1  # Priority 1 - we want ALL content under this domain!
    
    def _extract_category(self, pattern: str, url: str) -> str:
        """Extract category name from pattern match"""
        if "/ead" in pattern:
            return "education"
        elif "/conteudos" in pattern:
            return "content"
        elif "/servicos" in pattern:
            return "services"
        elif "/eventos" in pattern:
            return "events"
        elif "/pwa/produtos" in pattern:
            return "products"
        elif "/podcast" in pattern:
            return "podcast"
        elif "/receitas" in pattern:
            return "recipes"
        elif "/calculadoras" in pattern:
            return "calculators"
        elif "/acervo" in pattern:
            return "archive"
        else:
            return "high_priority"


class InteractionEngine:
    """Handles complex page interactions using Playwright"""
    
    def __init__(self, login_broker: LoginBroker):
        self.login_broker = login_broker
        self.interaction_patterns = {
            "pagination": [
                "a:has-text('Next')", "a:has-text('Próximo')",
                "button:has-text('Load More')", "button:has-text('Carregar Mais')",
                "a:has-text('Show All')", "a:has-text('Mostrar Todos')",
                ".pagination a", ".pager a"
            ],
            "menus": [
                ".dropdown-toggle", ".menu-toggle",
                "button[aria-expanded]", "a[aria-expanded]",
                ".has-children > a", ".expandable"
            ],
            "forms": [
                "select", "input[type='search']",
                ".filter-form", ".search-form"
            ]
        }
    
    def extract_interactive_urls(self, url: str, user_agent: str, auth_headers: Dict) -> List[str]:
        """Use Playwright to interact with page and extract additional URLs"""
        from playwright.sync_api import sync_playwright
        
        discovered_urls = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=user_agent,
                    extra_http_headers=auth_headers
                )
                
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for dynamic content
                page.wait_for_timeout(3000)
                
                # Scroll to trigger lazy loading
                self._scroll_page(page)
                
                # Interact with menus
                menu_urls = self._interact_with_menus(page)
                discovered_urls.extend(menu_urls)
                
                # Handle pagination
                pagination_urls = self._handle_pagination(page)
                discovered_urls.extend(pagination_urls)
                
                # Interact with forms
                form_urls = self._interact_with_forms(page)
                discovered_urls.extend(form_urls)
                
                # Extract all links after interactions
                final_links = page.evaluate("""
                    Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => href && href.startsWith('http'))
                """)
                discovered_urls.extend(final_links)
                
                browser.close()
                
        except Exception as e:
            print(f"  ⚠️ Interactive extraction failed for {url}: {e}")
        
        return list(set(discovered_urls))  # Remove duplicates
    
    def _scroll_page(self, page):
        """Scroll page to trigger lazy loading"""
        try:
            page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            page.wait_for_timeout(2000)
            
            page.evaluate("""
                window.scrollTo(0, 0);
            """)
            page.wait_for_timeout(1000)
        except:
            pass
    
    def _interact_with_menus(self, page) -> List[str]:
        """Interact with dropdown menus and expandable elements"""
        urls = []
        
        for selector in self.interaction_patterns["menus"]:
            try:
                elements = page.query_selector_all(selector)
                for element in elements:  # NO LIMIT - interact with ALL menu elements
                    try:
                        element.hover()
                        page.wait_for_timeout(500)
                        
                        element.click()
                        page.wait_for_timeout(1000)
                        
                        # Extract new links
                        new_links = page.evaluate("""
                            Array.from(document.querySelectorAll('a[href]'))
                                .map(a => a.href)
                                .filter(href => href && href.startsWith('http'))
                        """)
                        urls.extend(new_links)
                        
                    except:
                        continue
            except:
                continue
        
        return urls
    
    def _handle_pagination(self, page) -> List[str]:
        """Handle pagination and load more buttons"""
        urls = []
        max_pages = 50  # Much higher limit - we want ALL pages
        
        for i in range(max_pages):
            try:
                # Look for pagination elements
                pagination_found = False
                
                for selector in self.interaction_patterns["pagination"]:
                    try:
                        element = page.query_selector(selector)
                        if element and element.is_visible():
                            element.click()
                            page.wait_for_load_state("networkidle", timeout=10000)
                            
                            # Extract URLs from new page
                            page_links = page.evaluate("""
                                Array.from(document.querySelectorAll('a[href]'))
                                    .map(a => a.href)
                                    .filter(href => href && href.startsWith('http'))
                            """)
                            urls.extend(page_links)
                            pagination_found = True
                            break
                    except:
                        continue
                
                if not pagination_found:
                    break
                    
            except:
                break
        
        return urls
    
    def _interact_with_forms(self, page) -> List[str]:
        """Interact with search forms and filters"""
        urls = []
        
        try:
            # Look for search forms
            search_inputs = page.query_selector_all("input[type='search'], input[name*='search']")
            for search_input in search_inputs:  # NO LIMIT - try all search forms
                try:
                    search_input.fill("nutrição")  # Common term for nutrition site
                    page.keyboard.press("Enter")
                    page.wait_for_load_state("networkidle", timeout=10000)
                    
                    search_results = page.evaluate("""
                        Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(href => href && href.startsWith('http'))
                    """)
                    urls.extend(search_results)
                    
                except:
                    continue
            
            # Look for select dropdowns
            selects = page.query_selector_all("select")
            for select in selects:  # NO LIMIT - try all select dropdowns
                try:
                    options = select.query_selector_all("option")
                    if len(options) > 1:
                        # Try selecting first non-empty option
                        options[1].click()
                        page.wait_for_timeout(2000)
                        
                        select_results = page.evaluate("""
                            Array.from(document.querySelectorAll('a[href]'))
                                .map(a => a.href)
                                .filter(href => href && href.startsWith('http'))
                        """)
                        urls.extend(select_results)
                        
                except:
                    continue
                    
        except:
            pass
        
        return urls


class URLPatternAnalyzer:
    """Analyzes URL patterns and generates systematic variations"""
    
    def __init__(self):
        self.discovered_patterns = defaultdict(list)
    
    def analyze_patterns(self, urls: List[str]) -> Dict[str, List[str]]:
        """Analyze URL patterns and suggest systematic completions"""
        patterns = {}
        
        # Group URLs by pattern
        for url in urls:
            pattern = self._extract_pattern(url)
            if pattern:
                self.discovered_patterns[pattern].append(url)
        
        # Generate systematic variations for each pattern
        for pattern, pattern_urls in self.discovered_patterns.items():
            if len(pattern_urls) >= 3:  # Only analyze patterns with multiple examples
                variations = self._generate_pattern_variations(pattern, pattern_urls)
                if variations:
                    patterns[pattern] = variations
        
        return patterns
    
    def _extract_pattern(self, url: str) -> Optional[str]:
        """Extract URL pattern (e.g., /ead/course-{id})"""
        parsed = urlparse(url)
        path = parsed.path
        
        # Common patterns to detect
        patterns = [
            (r'/ead/[^/]+/[^/]+-(\d+)', '/ead/category/item-{id}'),
            (r'/conteudos/[^/]+/[^/]+-(\d+)', '/conteudos/category/item-{id}'),
            (r'/node/(\d+)', '/node/{id}'),
            (r'/produtos/[^/]+-(\d+)', '/produtos/item-{id}'),
        ]
        
        for regex, pattern_template in patterns:
            if re.search(regex, path):
                return pattern_template
        
        return None
    
    def _generate_pattern_variations(self, pattern: str, examples: List[str]) -> List[str]:
        """Generate systematic URL variations based on pattern"""
        variations = []
        
        # Extract IDs from examples
        ids = []
        for url in examples:
            id_match = re.search(r'-(\d+)', url)
            if id_match:
                ids.append(int(id_match.group(1)))
        
        if len(ids) >= 3:
            # Generate range of IDs
            min_id, max_id = min(ids), max(ids)
            
            # Extend range slightly to catch missing items
            start_id = max(1, min_id - 10)
            end_id = min_id + 50  # Conservative extension
            
            # Generate comprehensive variations - NO artificial limit!
            base_url = examples[0].rsplit('-', 1)[0]
            for i in range(start_id, end_id):
                if i not in ids:  # Only suggest missing IDs
                    variation = f"{base_url}-{i}"
                    variations.append(variation)
        
        return variations  # Return ALL variations, no limit


class DiskStorage:
    """Thread-safe disk storage for URLs and scraped content"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.scrapped_dir = self.data_dir / "scrapped"
        self.mapsite_file = self.data_dir / "mapsite.json"
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.scrapped_dir.mkdir(exist_ok=True)
        
        # Thread lock for mapsite updates
        self.mapsite_lock = threading.Lock()
        
        # Initialize mapsite if it doesn't exist
        if not self.mapsite_file.exists():
            self._save_mapsite_update({"discovered_urls": [], "total_count": 0, "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S")})
    
    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename using hash"""
        # Create a safe filename from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        # Also include a readable part
        parsed = urlparse(url)
        path_part = parsed.path.replace('/', '_').replace('?', '_').replace('&', '_')[:50]
        return f"{url_hash}_{path_part}.json"
    
    def save_scraped_content(self, url: str, firecrawl_response, phase: str, depth: int, category: str):
        """Save individual scraped content to disk immediately"""
        try:
            filename = self._url_to_filename(url)
            filepath = self.scrapped_dir / filename
            
            # Convert firecrawl response to serializable format
            content_data = {
                "url": url,
                "phase": phase,
                "depth": depth,
                "category": category,
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "firecrawl_response": self._serialize_firecrawl_response(firecrawl_response)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            print(f"  💾 Saved content: {filename}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to save content for {url}: {e}")
            return False
    
    def _serialize_firecrawl_response(self, response):
        """Convert Firecrawl response to JSON-serializable format"""
        try:
            # Handle different response types
            serialized = {}
            
            if hasattr(response, 'markdown') and response.markdown:
                serialized['markdown'] = response.markdown
            
            if hasattr(response, 'links') and response.links:
                serialized['links'] = response.links
            
            if hasattr(response, 'metadata') and response.metadata:
                serialized['metadata'] = {
                    'title': getattr(response.metadata, 'title', ''),
                    'description': getattr(response.metadata, 'description', ''),
                    'statusCode': getattr(response.metadata, 'statusCode', ''),
                    'error': getattr(response.metadata, 'error', '')
                }
            
            if hasattr(response, 'html') and response.html:
                serialized['html'] = response.html
            
            return serialized
            
        except Exception as e:
            return {"error": f"Serialization failed: {e}"}
    
    def add_url_to_mapsite(self, url: str, category: str, phase: str, depth: int):
        """Thread-safely add URL to mapsite.json with deduplication"""
        with self.mapsite_lock:
            try:
                # Read current mapsite
                mapsite_data = self._load_mapsite()
                
                # Check if URL already exists
                existing_urls = {item['url'] for item in mapsite_data['discovered_urls']}
                if url not in existing_urls:
                    # Add new URL entry
                    mapsite_data['discovered_urls'].append({
                        "url": url,
                        "category": category,
                        "phase": phase,
                        "depth": depth,
                        "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                    })
                    
                    # Update metadata
                    mapsite_data['total_count'] = len(mapsite_data['discovered_urls'])
                    mapsite_data['last_updated'] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    
                    # Save back to disk
                    self._save_mapsite_update(mapsite_data)
                    
                    print(f"  📍 Added to mapsite: {url} [{category}]")
                    return True
                
                print(f"  🔄 Already exists: {url}")
                return False  # URL already exists
                
            except Exception as e:
                print(f"  ❌ Failed to update mapsite for {url}: {e}")
                return False
    
    def is_url_already_discovered(self, url: str) -> bool:
        """Check if URL has already been discovered (thread-safe)"""
        with self.mapsite_lock:
            try:
                mapsite_data = self._load_mapsite()
                existing_urls = {item['url'] for item in mapsite_data['discovered_urls']}
                return url in existing_urls
            except:
                return False
    
    def _load_mapsite(self):
        """Load current mapsite from disk"""
        try:
            with open(self.mapsite_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"discovered_urls": [], "total_count": 0, "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    
    def _save_mapsite_update(self, mapsite_data):
        """Save mapsite to disk"""
        with open(self.mapsite_file, 'w', encoding='utf-8') as f:
            json.dump(mapsite_data, f, indent=2, ensure_ascii=False)
    
    def get_current_stats(self):
        """Get current discovery statistics"""
        mapsite_data = self._load_mapsite()
        
        # Count by category
        category_counts = defaultdict(int)
        phase_counts = defaultdict(int)
        
        for item in mapsite_data['discovered_urls']:
            category_counts[item.get('category', 'unknown')] += 1
            phase_counts[item.get('phase', 'unknown')] += 1
        
        return {
            'total_urls': mapsite_data['total_count'],
            'categories': dict(category_counts),
            'phases': dict(phase_counts),
            'last_updated': mapsite_data['last_updated']
        }


class UltraDeepMapsite:
    """Ultra-comprehensive site discovery system with immediate disk storage"""
    
    def __init__(self):
        self.settings = Settings()
        self.firecrawl = None
        self.login_broker = None
        self.session_cookies = None
        
        # Disk storage system
        self.storage = DiskStorage()
        
        # Discovery tracking (disk-based deduplication for consistency)
        self.crawl_queue: deque = deque()
        self.queued_urls: Set[str] = set()  # Track URLs in queue to avoid duplicates
        self.failed_urls: Set[str] = set()
        
        # Initialize components
        base_domain = self.settings.base_url.replace('https://', '').replace('http://', '').split('/')[0]
        self.classifier = ContentClassifier(base_domain)
        self.pattern_analyzer = URLPatternAnalyzer()
        
    def initialize_session(self) -> bool:
        """Initialize authentication and Firecrawl"""
        print("🔐 Initializing Ultra-Deep Discovery Session...")
        
        # Get authentication
        self.login_broker = LoginBroker()
        session_result = self.login_broker.acquire_session(headless=True)
        
        if not session_result or 'cookie_header' not in session_result:
            print("❌ Failed to get authentication cookies")
            return False
        
        self.session_cookies = session_result['cookie_header']
        print(f"✅ Authentication successful: {len(self.session_cookies)} chars")
        
        # Initialize Firecrawl
        try:
            self.firecrawl = FirecrawlApp(api_key=self.settings.firecrawl_api_key)
            print("✅ Firecrawl initialized")
            return True
        except Exception as e:
            print(f"❌ Firecrawl initialization failed: {e}")
            return False
    
    def phase1_foundation_discovery(self) -> List[str]:
        """Phase 1: Foundation discovery (baseline URL collection)"""
        print("\n🏗️ PHASE 1: Foundation Discovery")
        print("=" * 60)
        
        base_url = self.settings.base_url
        auth_headers = self.settings.get_firecrawl_headers(self.session_cookies)
        
        print(f"🚀 Scraping foundation URL: {base_url}")
        
        try:
            # SINGLE CALL: Get both links AND content in one request
            result = self.firecrawl.scrape_url(
                url=base_url,
                formats=["links", "markdown"],  # Get BOTH links and content
                headers=auth_headers,
                only_main_content=False,
                wait_for=5000,  # Extra wait for foundation
                timeout=30000
            )
            
            if not (hasattr(result, 'links') and result.links):
                print("❌ No links found in foundation page")
                return []
            
            # Process complete response: save content AND extract links from SINGLE call
            foundation_urls = self._process_complete_response(result, base_url, "phase1_foundation", 0, "homepage")
            
            print(f"✅ Foundation discovery complete: {len(foundation_urls)} URLs")
            
                        # Populate initial crawl queue with ALL valid URLs (not just high priority)
            for url in foundation_urls:
                category, priority = self.classifier.classify_url(url)
                if priority > 0:  # ANY valid content (not just priority 1)
                    self.crawl_queue.append((url, 1, category))  # (url, depth, category)
                    self.queued_urls.add(url)  # Track queued URLs
            
            print(f"📋 Queued {len(self.crawl_queue)} URLs for comprehensive deep crawling")
            
            return foundation_urls
            
        except Exception as e:
            print(f"❌ Foundation discovery failed: {e}")
            return []
    
    def phase2_recursive_discovery(self) -> List[str]:
        """Phase 2: Recursive deep crawling of content URLs"""
        print("\n🔬 PHASE 2: Recursive Deep Discovery")
        print("=" * 60)
        
        phase2_urls = []
        # NO ARTIFICIAL LIMITS - only stop when no new URLs found
        category_counts = defaultdict(int)
        
        print(f"🎯 Starting unlimited recursive crawl with {len(self.crawl_queue)} queued URLs")
        print(f"📊 Smart stopping: Only stop when no new URLs discovered")
        
        while self.crawl_queue:
            url, depth, category = self.crawl_queue.popleft()
            
            # SMART STOPPING: Check if URL already discovered (disk-based deduplication)
            if self.storage.is_url_already_discovered(url):
                print(f"  🔄 Skipping already scraped: {url}")
                continue
            
            print(f"\n📍 Crawling [D{depth}] {category}: {url}")
            
            # Crawl the URL and save content
            new_urls = self._crawl_single_url(url, depth, category, "phase2_recursive")
            
            if new_urls:
                phase2_urls.extend(new_urls)
                category_counts[category] += len(new_urls)
                
                # Add ALL valid URLs to queue for deeper crawling - NO DEPTH LIMIT!
                for new_url in new_urls:
                    # Smart deduplication: check both disk storage AND queue
                    if (not self.storage.is_url_already_discovered(new_url) and 
                        new_url not in self.queued_urls):
                        new_category, priority = self.classifier.classify_url(new_url)
                        if priority > 0:  # Any valid URL - NO depth restriction!
                            self.crawl_queue.append((new_url, depth + 1, new_category))
                            self.queued_urls.add(new_url)  # Track queued URLs
                
                print(f"  ✅ Found {len(new_urls)} new URLs, queued for deeper crawling")
            else:
                print(f"  ⚪ No new URLs found")
            
            # Remove from queued URLs as it's now processed
            self.queued_urls.discard(url)
            
            # Progress update with real-time disk statistics
            remaining = len(self.crawl_queue)
            stats = self.storage.get_current_stats()
            print(f"  📊 Progress: {stats['total_urls']} total URLs on disk, {remaining} remaining in queue")
            
            # Brief pause to be respectful
            time.sleep(1)
        
        print(f"\n✅ Phase 2 complete: {len(phase2_urls)} new URLs discovered")
        
        return phase2_urls
    
    def phase3_interactive_discovery(self) -> List[str]:
        """Phase 3: Interactive discovery using Playwright"""
        print("\n🎭 PHASE 3: Interactive Discovery")
        print("=" * 60)
        
        phase3_urls = []
        
        # Initialize interaction engine
        interaction_engine = InteractionEngine(self.login_broker)
        
        # Select key pages for interactive discovery
        interactive_targets = self._select_interactive_targets()
        
        print(f"🎯 Selected {len(interactive_targets)} pages for interactive discovery")
        
        auth_headers = {
            "Authorization": self.settings.basic_auth_header,
            "Cookie": self.session_cookies
        }
        
        for i, (url, category) in enumerate(interactive_targets, 1):
            print(f"\n🎭 Interactive crawl {i}/{len(interactive_targets)}: {category}")
            print(f"   {url}")
            
            try:
                interactive_urls = interaction_engine.extract_interactive_urls(
                    url, self.settings.user_agent, auth_headers
                )
                
                # Filter and classify new URLs, save to disk immediately
                new_urls = []
                for int_url in interactive_urls:
                    # Check if URL already exists in disk storage
                    mapsite_data = self.storage._load_mapsite()
                    existing_urls = {item['url'] for item in mapsite_data['discovered_urls']}
                    
                    if int_url not in existing_urls:
                        category_type, priority = self.classifier.classify_url(int_url)
                        if priority > 0:  # Valid content URL
                            new_urls.append(int_url)
                            # IMMEDIATELY save to mapsite
                            self.storage.add_url_to_mapsite(int_url, category_type, "phase3_interactive", 0)
                
                if new_urls:
                    phase3_urls.extend(new_urls)
                    print(f"  ✅ Interactive discovery: +{len(new_urls)} new URLs")
                else:
                    print(f"  ⚪ No new URLs from interactive discovery")
                
            except Exception as e:
                print(f"  ❌ Interactive discovery failed: {e}")
            
            # Brief pause between interactive sessions
            time.sleep(2)
        
        print(f"\n✅ Phase 3 complete: {len(phase3_urls)} URLs from interactive discovery")
        
        return phase3_urls
    
    def phase4_pattern_completion(self) -> List[str]:
        """Phase 4: Pattern-based URL completion"""
        print("\n🧩 PHASE 4: Pattern-Based Completion")
        print("=" * 60)
        
        phase4_urls = []
        
        # Analyze patterns in discovered URLs from disk storage
        mapsite_data = self.storage._load_mapsite()
        all_discovered = [item['url'] for item in mapsite_data['discovered_urls']]
        patterns = self.pattern_analyzer.analyze_patterns(all_discovered)
        
        if not patterns:
            print("⚪ No systematic patterns detected for completion")
            return []
        
        print(f"🔍 Analyzing {len(patterns)} URL patterns for systematic completion")
        
        auth_headers = self.settings.get_firecrawl_headers(self.session_cookies)
        
        for pattern, suggestions in patterns.items():
            print(f"\n🧩 Testing pattern: {pattern}")
            print(f"   {len(suggestions)} systematic variations to test")
            
            valid_urls = []
            for suggested_url in suggestions:  # NO LIMIT - test ALL suggestions
                try:
                    # SINGLE CALL: Get both content AND links for validation
                    result = self.firecrawl.scrape_url(
                        url=suggested_url,
                        formats=["links", "markdown"],  # Get both for efficiency
                        headers=auth_headers,
                        only_main_content=True,
                        wait_for=2000,
                        timeout=15000
                    )
                    
                    # Basic validation - check if we got meaningful content
                    if (hasattr(result, 'markdown') and result.markdown and 
                        len(result.markdown.strip()) > 100):
                        valid_urls.append(suggested_url)
                        
                        # Use unified function: save content AND process any links found
                        category, priority = self.classifier.classify_url(suggested_url)
                        additional_urls = self._process_complete_response(result, suggested_url, "phase4_patterns", 0, category)
                        
                        # Add any additional URLs found in the pattern-completed page
                        if additional_urls:
                            print(f"  ✅ Valid + {len(additional_urls)} bonus URLs: {suggested_url}")
                        else:
                            print(f"  ✅ Valid: {suggested_url}")
                    else:
                        print(f"  ❌ Invalid: {suggested_url}")
                        
                except Exception as e:
                    print(f"  ❌ Failed: {suggested_url}")
                
                time.sleep(0.5)  # Brief pause between tests
            
            if valid_urls:
                phase4_urls.extend(valid_urls)
                print(f"  ✅ Pattern completion: +{len(valid_urls)} valid URLs")
        
        print(f"\n✅ Phase 4 complete: {len(phase4_urls)} URLs from pattern completion")
        
        return phase4_urls
    
    def save_ultra_comprehensive_results(self):
        """Save complete ultra-deep discovery results"""
        print("\n💾 Final Ultra-Comprehensive Results Summary")
        print("=" * 60)
        
        # Get final statistics from disk storage
        final_stats = self.storage.get_current_stats()
        total_urls = final_stats['total_urls']
        
        # Display comprehensive summary - data is already saved to disk during discovery
        print(f"✅ Ultra-deep discovery completed successfully!")
        print(f"📊 COMPREHENSIVE DISCOVERY SUMMARY")
        print("=" * 60)
        print(f"🌐 Base URL: {self.settings.base_url}")
        print(f"🔗 Total URLs Discovered: {total_urls}")
        print(f"💾 Mapsite saved to: data/mapsite.json")
        print(f"📁 Scraped content saved to: data/scrapped/")
        
        if final_stats['categories']:
            print(f"\n📂 Content Categories Discovered:")
            for category, count in sorted(final_stats['categories'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {category}: {count} URLs")
        
        if final_stats['phases']:
            print(f"\n📊 Discovery by Phase:")
            for phase, count in sorted(final_stats['phases'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {phase}: {count} URLs")
        
        print(f"\n🎯 Real-time Storage: All URLs and content saved immediately to disk")
        print(f"📈 Comprehensive site coverage achieved")
        print(f"⏱️ Last updated: {final_stats['last_updated']}")
        
        return total_urls

    
    def _process_complete_response(self, firecrawl_response, source_url: str, phase: str, depth: int, category: str) -> List[str]:
        """Process complete Firecrawl response: save content AND extract links in one function"""
        
        # STEP 1: Save the scraped content immediately
        self.storage.save_scraped_content(source_url, firecrawl_response, phase, depth, category)
        
        # STEP 2: Process and save links from the SAME response
        if not (hasattr(firecrawl_response, 'links') and firecrawl_response.links):
            return []
            
        processed_urls = []
        base_url = self.settings.base_url
        base_domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        for link in firecrawl_response.links:
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
                
                # Classify URL
                link_category, priority = self.classifier.classify_url(url)
                
                # Only keep valid content URLs
                if priority > 0 and url not in processed_urls:
                    processed_urls.append(url)
                    
                    # IMMEDIATELY save URL to mapsite on disk
                    self.storage.add_url_to_mapsite(url, link_category, phase, depth + 1)
        
        return processed_urls
    
    def _crawl_single_url(self, url: str, depth: int, category: str, phase: str) -> List[str]:
        """Crawl a single URL with SINGLE CALL - save content and extract links efficiently"""
        auth_headers = self.settings.get_firecrawl_headers(self.session_cookies)
        
        try:
            # SINGLE EFFICIENT CALL: Get both links and content
            result = self.firecrawl.scrape_url(
                url=url,
                formats=["links", "markdown"],  # Get both links AND content
                headers=auth_headers,
                only_main_content=False,
                wait_for=3000,
                timeout=25000
            )
            
            # Process complete response: save content AND extract links from SINGLE call
            new_urls = self._process_complete_response(result, url, phase, depth, category)
            
            # Filter out already discovered URLs (disk-based check)
            truly_new = [u for u in new_urls if not self.storage.is_url_already_discovered(u)]
            return truly_new
                
        except Exception as e:
            print(f"  ❌ Crawl failed: {e}")
            self.failed_urls.add(url)
            return []
    
    def _select_interactive_targets(self) -> List[Tuple[str, str]]:
        """Select key pages for interactive discovery"""
        targets = []
        
        # Group URLs by category from disk storage
        category_urls = defaultdict(list)
        mapsite_data = self.storage._load_mapsite()
        for item in mapsite_data['discovered_urls']:
            category_urls[item['category']].append(item['url'])
        
        # Select representative URLs from each category - NO LIMITS!
        for category, urls in category_urls.items():
            # Take more samples per category for comprehensive interactive discovery
            selected = urls[:10]  # Increased from 3 to 10
            for url in selected:
                targets.append((url, category))
        
        # NO ARBITRARY LIMIT - do interactive discovery on ALL valuable targets
        return targets
    
    def run_ultra_deep_discovery(self) -> bool:
        """Execute complete ultra-deep discovery process"""
        print("🚀 ULTRA-DEEP MAPSITE DISCOVERY")
        print("=" * 70)
        print("🎯 Goal: Maximum comprehensive site coverage")
        print("🔍 Method: 4-phase systematic discovery")
        print("⏱️ Time: Unlimited (thoroughness prioritized)")
        print("=" * 70)
        
        # Initialize
        if not self.initialize_session():
            return False
        
        try:
            # Phase 1: Foundation
            phase1_urls = self.phase1_foundation_discovery()
            if not phase1_urls:
                print("❌ Foundation discovery failed - cannot proceed")
                return False
            
            # Phase 2: Recursive Deep Crawling
            phase2_urls = self.phase2_recursive_discovery()
            
            # Phase 3: Interactive Discovery
            phase3_urls = self.phase3_interactive_discovery()
            
            # Phase 4: Pattern Completion
            phase4_urls = self.phase4_pattern_completion()
            
            # Save comprehensive results
            total_discovered = self.save_ultra_comprehensive_results()
            
            print(f"\n🎉 ULTRA-DEEP DISCOVERY COMPLETE!")
            print(f"🏆 {total_discovered} URLs discovered across 4 phases")
            print(f"📈 Comprehensive site coverage achieved")
            
            return True
            
        except Exception as e:
            print(f"❌ Ultra-deep discovery failed: {e}")
            return False


def main():
    """Run ultra-deep comprehensive mapsite discovery"""
    print("🌟 Ultra-Deep Mapsite Discovery System")
    print("Comprehensive 4-phase site crawling for maximum coverage")
    print("=" * 70)
    
    mapsite = UltraDeepMapsite()
    success = mapsite.run_ultra_deep_discovery()
    
    if success:
        print("\n✅ Ultra-deep mapsite discovery completed successfully!")
        print("🗂️ Check 'ultra_deep_mapsite.json' for comprehensive results")
    else:
        print("\n❌ Ultra-deep mapsite discovery failed.")
    
    return success


if __name__ == "__main__":
    main()
