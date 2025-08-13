#!/usr/bin/env python3
"""
Quick test to validate extracted cookies work
"""

import os
import sys
sys.path.insert(0, 'src')

from auth.login_broker import LoginBroker
import requests

def test_extracted_cookies():
    """Test cookies extracted by LoginBroker with a simple request"""
    print("🤖 Quick Cookie Validation Test")
    print("=" * 50)
    
    # Get fresh cookies from LoginBroker
    print("🔐 Getting fresh session cookies...")
    broker = LoginBroker()
    result = broker.acquire_session(headless=True)  # Headless for speed
    
    if not result or 'cookie_header' not in result:
        print("❌ Failed to get cookies")
        return False
    
    cookie_header = result['cookie_header']
    print(f"✅ Got cookies: {len(cookie_header)} chars")
    print(f"🍪 Preview: {cookie_header[:100]}...")
    
    # Test with simple HTTP request
    print("\n🌐 Testing cookies with direct HTTP request...")
    
    url = "https://dev-73046-nhsc-avante-brazil.pantheonsite.io/"
    headers = {
        'Authorization': 'Basic c2hpZWxkOnFhejEyMyFAIw==',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nestle-Scraper/1.0',
        'Cookie': cookie_header
    }
    
    try:
        print(f"📡 Making request to: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Content Length: {len(response.text)} chars")
        
        # Check for login indicators in response
        content_lower = response.text.lower()
        
        if response.status_code == 200:
            if 'login' in content_lower and 'senha' in content_lower:
                print("⚠️ Still seeing login form - cookies may not be working")
                return False
            elif any(indicator in content_lower for indicator in ['logout', 'sair', 'bem-vindo', 'dashboard']):
                print("✅ SUCCESS! Found logged-in content")
                return True
            else:
                print("✅ SUCCESS! Got authenticated response (no login form)")
                return True
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_extracted_cookies()
    if success:
        print("\n🎉 Cookie validation PASSED! Login automation is working!")
    else:
        print("\n❌ Cookie validation FAILED!")
    
    sys.exit(0 if success else 1)