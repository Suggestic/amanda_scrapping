#!/usr/bin/env python3
"""
Debug: Inspect login form elements on the Portuguese site
"""

import os
import sys
sys.path.insert(0, 'src')

from playwright.sync_api import sync_playwright

def debug_login_form():
    """Debug the actual form elements on the login page."""
    
    # Set environment
    os.environ.update({
        'PANTHEON_USERNAME': 'shield',
        'PANTHEON_PASSWORD': 'qaz123!@#',
        'BASE_URL': 'https://dev-73046-nhsc-avante-brazil.pantheonsite.io',
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nestle-Scraper/1.0',
    })
    
    basic_auth = "Basic c2hpZWxkOnFhejEyMyFAIw=="
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible for debugging
        
        context = browser.new_context(
            user_agent=os.getenv('USER_AGENT'),
            extra_http_headers={"Authorization": basic_auth}
        )
        
        page = context.new_page()
        
        print("🌐 Navigating to login page...")
        page.goto(f"{os.getenv('BASE_URL')}/login?destination=/")
        
        print(f"📍 URL: {page.url}")
        print(f"📄 Title: {page.title()}")
        
        # Get all input elements
        inputs = page.locator('input').all()
        print(f"\\n📝 Found {len(inputs)} input elements:")
        
        for i, input_elem in enumerate(inputs):
            try:
                name = input_elem.get_attribute('name') or 'no-name'
                input_type = input_elem.get_attribute('type') or 'no-type'
                input_id = input_elem.get_attribute('id') or 'no-id'
                placeholder = input_elem.get_attribute('placeholder') or 'no-placeholder'
                
                print(f"  {i+1}. name='{name}' type='{input_type}' id='{input_id}' placeholder='{placeholder}'")
            except Exception as e:
                print(f"  {i+1}. Error reading attributes: {e}")
        
        # Look for form elements
        forms = page.locator('form').all()
        print(f"\\n📋 Found {len(forms)} form elements")
        
        # Look for buttons
        buttons = page.locator('button, input[type="submit"]').all()
        print(f"\\n🔘 Found {len(buttons)} buttons/submit elements:")
        
        for i, btn in enumerate(buttons):
            try:
                btn_type = btn.get_attribute('type') or 'no-type'
                btn_text = btn.text_content() or btn.get_attribute('value') or 'no-text'
                print(f"  {i+1}. type='{btn_type}' text='{btn_text}'")
            except Exception as e:
                print(f"  {i+1}. Error reading button: {e}")
        
        print("\\n⏸️  Pausing for 10 seconds to inspect page...")
        page.wait_for_timeout(10000)
        
        browser.close()

if __name__ == "__main__":
    debug_login_form()