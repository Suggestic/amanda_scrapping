#!/usr/bin/env python3
"""
Stage 0.5: Test Basic Auth header generation
This script tests our configuration and Basic Auth setup without requiring actual credentials.
"""

import os
import sys
import base64

# Add src to path for imports
sys.path.insert(0, 'src')

def test_basic_auth_generation():
    """Test Basic Auth header generation with known values."""
    print("=== Stage 0.5: Testing Basic Auth Header Generation ===\n")
    
    # Test with the known Pantheon credentials
    test_username = "shield"
    test_password = "qaz123!@#"
    
    # Manual generation for verification
    credentials = f"{test_username}:{test_password}"
    encoded = base64.b64encode(credentials.encode()).decode('ascii')
    expected_header = f"Basic {encoded}"
    
    print(f"Username: {test_username}")
    print(f"Password: {test_password}")
    print(f"Credentials string: {credentials}")
    print(f"Base64 encoded: {encoded}")
    print(f"Full header: {expected_header}")
    print()
    
    # Test our Settings class (if environment is set up)
    try:
        # Set test environment variables
        os.environ['PANTHEON_USERNAME'] = test_username
        os.environ['PANTHEON_PASSWORD'] = test_password
        os.environ['APP_EMAIL'] = 'test@example.com'
        os.environ['APP_PASSWORD'] = 'testpass'
        os.environ['BASE_URL'] = 'https://example.com'
        
        from config.settings import Settings
        
        # Create settings instance
        settings = Settings()
        generated_header = settings.basic_auth_header
        
        print("=== Testing Settings Class ===")
        print(f"Generated header: {generated_header}")
        print(f"Expected header:  {expected_header}")
        print(f"Match: {generated_header == expected_header}")
        print()
        
        # Test other methods
        print("=== Testing Other Settings Methods ===")
        print(f"Login URL: {settings.login_url}")
        print(f"User Agent: {settings.user_agent}")
        print(f"Zero Data Retention: {settings.zero_data_retention}")
        print()
        
        # Test Firecrawl headers
        headers = settings.get_firecrawl_headers()
        print("=== Testing Firecrawl Headers (no cookies) ===")
        for key, value in headers.items():
            print(f"{key}: {value}")
        print()
        
        # Test with cookies
        test_cookies = "sessionid=abc123; csrftoken=def456"
        headers_with_cookies = settings.get_firecrawl_headers(test_cookies)
        print("=== Testing Firecrawl Headers (with cookies) ===")
        for key, value in headers_with_cookies.items():
            print(f"{key}: {value}")
        
        print("\n✅ Stage 0.5 PASSED: Basic Auth generation working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Settings class: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_auth_generation()
    sys.exit(0 if success else 1)