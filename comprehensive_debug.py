#!/usr/bin/env python3
"""
Comprehensive debug of the login page to find form elements
"""

import os
import sys
sys.path.insert(0, 'src')

from playwright.sync_api import sync_playwright

def comprehensive_debug():
    """Comprehensive analysis of the login page."""
    
    # Set environment
    os.environ.update({
        'PANTHEON_USERNAME': 'shield',
        'PANTHEON_PASSWORD': 'qaz123!@#',
        'BASE_URL': 'https://dev-73046-nhsc-avante-brazil.pantheonsite.io',
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nestle-Scraper/1.0',
    })
    
    basic_auth = "Basic c2hpZWxkOnFhejEyMyFAIw=="
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visual mode
        
        context = browser.new_context(
            user_agent=os.getenv('USER_AGENT'),
            extra_http_headers={"Authorization": basic_auth}
        )
        
        page = context.new_page()
        
        print("🌐 Navigating to login page...")
        page.goto(f"{os.getenv('BASE_URL')}/login?destination=/")
        
        # Wait for page to fully load
        page.wait_for_load_state("networkidle")
        print(f"📍 URL: {page.url}")
        print(f"📄 Title: {page.title()}")
        
        # Take screenshot for analysis
        page.screenshot(path="login_page_debug.png")
        print("📸 Screenshot saved as login_page_debug.png")
        
        # Wait for any dynamic content
        print("⏳ Waiting 3 seconds for dynamic content...")
        page.wait_for_timeout(3000)
        
        # Look for text containing "email", "senha", "login", etc.
        print("\\n🔍 Looking for login-related text on page...")
        login_keywords = ["email", "senha", "login", "entrar", "usuário", "password", "user"]
        
        for keyword in login_keywords:
            elements = page.locator(f"text=/{keyword}/i").all()
            if elements:
                print(f"  Found '{keyword}' in {len(elements)} elements")
        
        # Look for ANY input elements (not just form inputs)
        print("\\n📝 ALL input elements on page:")
        all_inputs = page.locator('input').all()
        for i, inp in enumerate(all_inputs):
            try:
                name = inp.get_attribute('name') or 'no-name'
                input_type = inp.get_attribute('type') or 'no-type'
                input_id = inp.get_attribute('id') or 'no-id'
                placeholder = inp.get_attribute('placeholder') or 'no-placeholder'
                value = inp.get_attribute('value') or 'no-value'
                classes = inp.get_attribute('class') or 'no-class'
                
                print(f"  {i+1}. name='{name}' type='{input_type}' id='{input_id}'")
                print(f"      placeholder='{placeholder}' value='{value}'")
                print(f"      class='{classes}'")
                print(f"      visible={inp.is_visible()}")
                print("")
            except Exception as e:
                print(f"  {i+1}. Error: {e}")
        
        # Look for elements that might trigger login form
        print("\\n🔘 Looking for potential login triggers...")
        login_triggers = [
            "button:has-text('login')",
            "button:has-text('entrar')",
            "a:has-text('login')",
            "a:has-text('entrar')",
            "[data-login]",
            ".login-button",
            "#login",
            ".auth-trigger"
        ]
        
        for trigger in login_triggers:
            try:
                elements = page.locator(trigger).all()
                if elements:
                    print(f"  Found {len(elements)} elements matching '{trigger}'")
            except Exception as e:
                print(f"  Error checking '{trigger}': {e}")
        
        # Get page content for manual review
        print("\\n📄 Saving page content for analysis...")
        content = page.content()
        with open("login_page_content.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("💾 Page HTML saved as login_page_content.html")
        
        # Look in iframes if any
        frames = page.frames
        if len(frames) > 1:
            print(f"\\n🖼️  Found {len(frames)} frames, checking for login forms...")
            for i, frame in enumerate(frames):
                try:
                    frame_inputs = frame.locator('input[type="email"], input[type="password"], input[name*="mail"], input[name*="pass"]').all()
                    if frame_inputs:
                        print(f"  Frame {i}: Found {len(frame_inputs)} potential login inputs")
                except Exception as e:
                    print(f"  Frame {i}: Error - {e}")
        
        print("\\n⏸️  Pausing 15 seconds for manual inspection...")
        print("   Check the browser window and files:")
        print("   - login_page_debug.png (screenshot)")
        print("   - login_page_content.html (page source)")
        page.wait_for_timeout(15000)
        
        browser.close()

if __name__ == "__main__":
    comprehensive_debug()