#!/usr/bin/env python3
"""
Step-by-step debug: Analyze the entire login flow in detail
"""

import os
import sys
sys.path.insert(0, 'src')

from playwright.sync_api import sync_playwright

def debug_login_flow():
    """Debug the entire login flow step by step."""
    
    # Set environment
    os.environ.update({
        'PANTHEON_USERNAME': 'shield',
        'PANTHEON_PASSWORD': 'qaz123!@#',
        'BASE_URL': 'https://dev-73046-nhsc-avante-brazil.pantheonsite.io',
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nestle-Scraper/1.0',
    })
    
    basic_auth = "Basic c2hpZWxkOnFhejEyMyFAIw=="
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visual mode for debugging
        
        context = browser.new_context(
            user_agent=os.getenv('USER_AGENT'),
            extra_http_headers={"Authorization": basic_auth}
        )
        
        page = context.new_page()
        
        print("=== STEP 1: Initial navigation ===")
        page.goto(f"{os.getenv('BASE_URL')}/login?destination=/")
        page.wait_for_load_state("networkidle")
        
        print(f"📍 URL: {page.url}")
        print(f"📄 Title: {page.title()}")
        
        # Save initial state
        page.screenshot(path="step1_initial.png")
        with open("step1_initial.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("💾 Saved: step1_initial.png and step1_initial.html")
        
        # Analyze all login links in detail
        print("\\n=== STEP 2: Analyzing ALL login links ===")
        login_patterns = [
            "a:has-text('login')",
            "a:has-text('Login')", 
            "a:has-text('LOGIN')",
            "button:has-text('login')",
            "button:has-text('Login')",
            "button:has-text('LOGIN')",
            ".login",
            "#login",
            "[data-login]"
        ]
        
        all_login_elements = []
        for pattern in login_patterns:
            try:
                elements = page.locator(pattern).all()
                for i, elem in enumerate(elements):
                    try:
                        text = elem.text_content()
                        href = elem.get_attribute('href')
                        classes = elem.get_attribute('class')
                        visible = elem.is_visible()
                        
                        all_login_elements.append({
                            'pattern': pattern,
                            'index': i,
                            'text': text,
                            'href': href,
                            'classes': classes,
                            'visible': visible,
                            'element': elem
                        })
                        
                        print(f"  Found: {pattern}[{i}]")
                        print(f"    Text: '{text}'")
                        print(f"    Href: '{href}'")
                        print(f"    Classes: '{classes}'")
                        print(f"    Visible: {visible}")
                        print()
                        
                    except Exception as e:
                        print(f"    Error reading element: {e}")
            except Exception as e:
                print(f"  Error with pattern {pattern}: {e}")
        
        print(f"\\n📊 Total login elements found: {len(all_login_elements)}")
        
        # Try clicking each visible login element
        for i, login_elem in enumerate(all_login_elements):
            if not login_elem['visible']:
                print(f"\\n⏭️ Skipping invisible element {i+1}")
                continue
                
            print(f"\\n=== STEP 3.{i+1}: Clicking login element {i+1} ===")
            print(f"Pattern: {login_elem['pattern']}")
            print(f"Text: '{login_elem['text']}'")
            print(f"Href: '{login_elem['href']}'")
            
            try:
                # Click the element
                login_elem['element'].click()
                print("✅ Clicked successfully")
                
                # Wait for any changes
                page.wait_for_timeout(3000)
                page.wait_for_load_state("networkidle", timeout=10000)
                
                # Check what happened
                new_url = page.url
                new_title = page.title()
                
                print(f"📍 New URL: {new_url}")
                print(f"📄 New Title: {new_title}")
                
                # Save state after click
                page.screenshot(path=f"step3_{i+1}_after_click.png")
                with open(f"step3_{i+1}_after_click.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print(f"💾 Saved: step3_{i+1}_after_click.png and step3_{i+1}_after_click.html")
                
                # Look for login form fields now
                print("\\n🔍 Looking for login form fields...")
                
                # Portuguese form field selectors from screenshot
                email_selectors = [
                    'input[placeholder*="E-mail"]',
                    'input[placeholder*="CPF"]',
                    'input[placeholder*="e-mail"]',
                    'input[type="email"]',
                    'input[name="email"]'
                ]
                
                password_selectors = [
                    'input[placeholder*="Senha"]',
                    'input[placeholder*="senha"]',
                    'input[type="password"]'
                ]
                
                email_found = False
                password_found = False
                
                for selector in email_selectors:
                    try:
                        if page.locator(selector).is_visible():
                            print(f"✅ Found email field: {selector}")
                            email_found = True
                            
                            # Get more details
                            elem = page.locator(selector).first
                            placeholder = elem.get_attribute('placeholder')
                            name = elem.get_attribute('name')
                            print(f"    Placeholder: '{placeholder}'")
                            print(f"    Name: '{name}'")
                            break
                    except:
                        continue
                
                for selector in password_selectors:
                    try:
                        if page.locator(selector).is_visible():
                            print(f"✅ Found password field: {selector}")
                            password_found = True
                            
                            # Get more details
                            elem = page.locator(selector).first
                            placeholder = elem.get_attribute('placeholder')
                            name = elem.get_attribute('name')
                            print(f"    Placeholder: '{placeholder}'")
                            print(f"    Name: '{name}'")
                            break
                    except:
                        continue
                
                if email_found and password_found:
                    print("\\n🎯 SUCCESS! Found both email and password fields!")
                    print("This is the correct login trigger to use.")
                    
                    # Try to perform actual login here
                    print("\\n=== STEP 4: Attempting actual login ===")
                    try:
                        # Fill the form
                        email_field = page.locator('input[placeholder*="E-mail"], input[placeholder*="CPF"]').first
                        password_field = page.locator('input[placeholder*="Senha"], input[type="password"]').first
                        
                        print("📝 Filling email field...")
                        email_field.fill("bot@nestle.com")
                        
                        print("📝 Filling password field...")
                        password_field.fill("80tN3$tl3")
                        
                        # Look for submit button
                        submit_button = None
                        submit_selectors = [
                            'button:has-text("ENVIAR")',
                            'button:has-text("Enviar")',
                            'button[type="submit"]'
                        ]
                        
                        for submit_sel in submit_selectors:
                            if page.locator(submit_sel).is_visible():
                                submit_button = submit_sel
                                print(f"✅ Found submit button: {submit_sel}")
                                break
                        
                        if submit_button:
                            print("🚀 Clicking submit button...")
                            page.click(submit_button)
                        else:
                            print("🚀 Pressing Enter as fallback...")
                            page.keyboard.press("Enter")
                        
                        # Wait for response
                        page.wait_for_load_state("networkidle", timeout=15000)
                        
                        final_url = page.url
                        final_title = page.title()
                        
                        print(f"📍 Final URL: {final_url}")
                        print(f"📄 Final Title: {final_title}")
                        
                        # Save final state
                        page.screenshot(path="step4_final_login.png")
                        with open("step4_final_login.html", "w", encoding="utf-8") as f:
                            f.write(page.content())
                        print("💾 Saved: step4_final_login.png and step4_final_login.html")
                        
                        # Check for success indicators
                        if "/login" not in final_url.lower():
                            print("🎉 LOGIN SUCCESS! Redirected away from login page")
                            
                            # Extract cookies
                            cookies = context.cookies()
                            print(f"🍪 Got {len(cookies)} cookies")
                            
                            # Show session cookies
                            session_cookies = [c for c in cookies if 'sess' in c['name'].lower()]
                            for cookie in session_cookies:
                                print(f"  Session cookie: {cookie['name']} = {cookie['value'][:20]}...")
                            
                        else:
                            print("⚠️ Still on login page - check for errors")
                        
                    except Exception as e:
                        print(f"❌ Login attempt failed: {e}")
                    
                    # Pause for manual inspection
                    print("\\n⏸️ Pausing 10 seconds for inspection...")
                    page.wait_for_timeout(10000)
                    break
                    
                elif email_found or password_found:
                    print(f"⚠️ Partial success: email={email_found}, password={password_found}")
                else:
                    print("❌ No login form fields found after clicking")
                
                print("\\n" + "="*50)
                
            except Exception as e:
                print(f"❌ Error clicking element: {e}")
                continue
        
        browser.close()

if __name__ == "__main__":
    debug_login_flow()