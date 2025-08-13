#!/usr/bin/env python3
"""
Stage 1.1-1.5: Test Playwright LoginBroker
This script tests the automated login and cookie extraction.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, 'src')

def test_login_broker(headless=True):
    """Test the LoginBroker automation."""
    print("=== Stage 1: Testing Playwright LoginBroker ===\n")
    
    # Set up environment
    os.environ.update({
        'PANTHEON_USERNAME': 'shield',
        'PANTHEON_PASSWORD': 'qaz123!@#',
        'APP_EMAIL': 'bot@nestle.com',
        'APP_PASSWORD': '80tN3$tl3',
        'BASE_URL': 'https://dev-73046-nhsc-avante-brazil.pantheonsite.io',
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nestle-Scraper/1.0',
    })
    
    try:
        from auth.login_broker import LoginBroker
        
        # Initialize broker
        print("🤖 Initializing LoginBroker...")
        broker = LoginBroker()
        
        # Acquire session
        print("\\n🚀 Starting automated session acquisition...")
        result = broker.acquire_session(headless=headless)
        
        if not result.get('success'):
            print(f"❌ Login failed: {result.get('error', 'Unknown error')}")
            return False
        
        print("\\n=== Session Acquisition Results ===")
        print(f"✅ Success: {result['success']}")
        print(f"🍪 Total cookies: {result['total_cookies']}")
        print(f"🔑 Session cookies: {result['session_cookies']}")
        print(f"📅 Expires at: {result['expires_at']}")
        print(f"🍪 Cookie header length: {len(result['cookie_header'])} chars")
        print(f"Cookie preview: {result['cookie_header'][:100]}...")
        
        # Test the cookies with Firecrawl
        print("\\n🔥 Testing cookies with Firecrawl...")
        return test_cookies_with_firecrawl(result['cookie_header'])
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cookies_with_firecrawl(cookie_header):
    """Test the automated cookies with Firecrawl."""
    try:
        from firecrawl import FirecrawlApp
        from config.settings import Settings
        
        # Check for API key
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            print("❌ FIRECRAWL_API_KEY not set")
            return False
        
        # Initialize Firecrawl
        settings = Settings()
        firecrawl = FirecrawlApp(api_key=api_key)
        
        # Get headers with automated cookies
        headers = settings.get_firecrawl_headers(cookie_header)
        
        print("=== Testing Automated Cookies with Firecrawl ===")
        print(f"URL: {settings.base_url}")
        
        # Test scrape
        response = firecrawl.scrape_url(
            url=settings.base_url,
            headers=headers,
            formats=["markdown"],
            only_main_content=True
        )
        
        # Check response
        if hasattr(response, 'markdown') and response.markdown:
            content = response.markdown
            content_preview = content[:200] + "..." if len(content) > 200 else content
            print(f"✅ Content received: {content_preview}")
            
            # Check for login indicators
            login_indicators = ['login', 'entrar', 'senha', 'password', 'email']
            found_indicators = [ind for ind in login_indicators if ind in content.lower()]
            
            if found_indicators:
                print(f"⚠️  Found login indicators: {found_indicators}")
                print("May still be showing login page")
                return False
            else:
                print("✅ No login indicators - automated cookies working!")
                return True
        else:
            print("❌ No content received")
            return False
            
    except Exception as e:
        print(f"❌ Firecrawl test failed: {e}")
        return False

def main():
    """Main test function."""
    # Check if user wants to see browser (for debugging)
    headless = "--visual" not in sys.argv
    
    if not headless:
        print("🖥️  Running in visual mode (browser will be visible)")
    
    success = test_login_broker(headless=headless)
    
    if success:
        print("\\n🎉 Stage 1 PASSED: Automated login working!")
        print("✅ LoginBroker successfully automated cookie acquisition")
        print("✅ Cookies work with Firecrawl")
        print("✅ End-to-end automation complete")
    else:
        print("\\n❌ Stage 1 FAILED: Check logs above for issues")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()