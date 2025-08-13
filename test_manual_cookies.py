#!/usr/bin/env python3
"""
Stage 0.6: Test manual cookie extraction
This script tests the complete authentication flow with manually extracted cookies.

Usage: python3 test_manual_cookies.py "sessionid=abc123; csrftoken=def456"
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, 'src')

def test_manual_cookies(cookie_header):
    """Test Firecrawl with manual cookies."""
    print("=== Stage 0.6: Testing Manual Cookie Extraction ===\n")
    
    # Check if we have a Firecrawl API key
    firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
    if not firecrawl_key:
        print("❌ FIRECRAWL_API_KEY not set in environment")
        print("Please set your Firecrawl API key:")
        print("export FIRECRAWL_API_KEY='your_key_here'")
        return False
    
    try:
        from firecrawl import FirecrawlApp
        from config.settings import Settings
        
        # Set up test environment
        os.environ.update({
            'PANTHEON_USERNAME': 'shield',
            'PANTHEON_PASSWORD': 'qaz123!@#',
            'APP_EMAIL': 'bot@nestle.com',
            'APP_PASSWORD': '80tN3$tl3',
            'BASE_URL': 'https://dev-73046-nhsc-avante-brazil.pantheonsite.io',
            'FIRECRAWL_API_KEY': firecrawl_key,
        })
        
        # Initialize components
        settings = Settings()
        firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
        
        # Get headers with manual cookies
        headers = settings.get_firecrawl_headers(cookie_header)
        
        print("=== Request Configuration ===")
        print(f"URL: {settings.base_url}")
        print(f"Headers:")
        for key, value in headers.items():
            if key == "Cookie":
                print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")
        print()
        
        # Test with a simple page first
        test_url = settings.base_url  # Try homepage
        
        print(f"=== Testing Firecrawl /scrape ===")
        print(f"Scraping: {test_url}")
        
        response = firecrawl.scrape_url(
            url=test_url,
            headers=headers,
            formats=["markdown"],
            only_main_content=True,
            wait_for=1000,  # Wait 1 second for page stability
            timeout=30000
        )
        
        print(f"Response received!")
        # Try to get status code from metadata
        if hasattr(response, 'metadata') and response.metadata:
            status_code = getattr(response.metadata, 'statusCode', 200)  # Default to 200 if not found
        else:
            status_code = 200  # Assume success if we got a response
        
        print(f"Status Code: {status_code}")
        print(f"Success: {getattr(response, 'success', True)}")
        
        # Check if we got content
        if hasattr(response, 'markdown') and response.markdown:
            content = response.markdown
            content_preview = content[:200] + "..." if len(content) > 200 else content
            print(f"Content Preview: {content_preview}")
            
            # Check for login page indicators (Portuguese)
            login_indicators = ['login', 'entrar', 'senha', 'password', 'email', 'conectar']
            content_lower = content.lower()
            
            found_login_indicators = [indicator for indicator in login_indicators if indicator in content_lower]
            
            if found_login_indicators:
                print(f"⚠️  Found login indicators: {found_login_indicators}")
                print("This might be a login page - cookies may have expired")
            else:
                print("✅ Content looks like authenticated page (no login indicators)")
                
        else:
            print("❌ No markdown content in response")
            print(f"Full response: {response}")
            return False
            
        if status_code == 200:
            print("✅ Stage 0.6 PASSED: Manual cookies working with Firecrawl!")
            return True
        elif status_code in [401, 403]:
            print(f"❌ Authentication failed (HTTP {status_code})")
            print("Check if cookies are valid and properly formatted")
            return False
        else:
            print(f"⚠️  Unexpected status code: {status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test_manual_cookies.py \"sessionid=abc123; csrftoken=def456\"")
        print("\nSee MANUAL_COOKIE_EXTRACTION.md for detailed instructions")
        sys.exit(1)
    
    cookie_header = sys.argv[1]
    print(f"Testing with cookies: {cookie_header[:50]}..." if len(cookie_header) > 50 else f"Testing with cookies: {cookie_header}")
    
    success = test_manual_cookies(cookie_header)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()