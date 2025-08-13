"""
LoginBroker - Automated cookie acquisition using Playwright
Handles the dual authentication flow:
1. Basic Auth via HTTP headers (Pantheon shield)
2. Form login via browser automation
"""

import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

class LoginBroker:
    """
    Handles automated login and cookie extraction using Playwright.
    Manages both Basic Auth and application session authentication.
    """
    
    def __init__(self):
        # Load credentials from environment
        self.pantheon_username = os.getenv('PANTHEON_USERNAME', 'shield')
        self.pantheon_password = os.getenv('PANTHEON_PASSWORD', 'qaz123!@#')
        self.app_email = os.getenv('APP_EMAIL', 'bot@nestle.com')
        self.app_password = os.getenv('APP_PASSWORD', '80tN3$tl3')
        self.base_url = os.getenv('BASE_URL', 'https://dev-73046-nhsc-avante-brazil.pantheonsite.io')
        self.user_agent = os.getenv('USER_AGENT', 
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nestle-Scraper/1.0')
        
        # Generate Basic auth header once
        basic_creds = f"{self.pantheon_username}:{self.pantheon_password}"
        self.basic_auth_header = f"Basic {base64.b64encode(basic_creds.encode()).decode('ascii')}"
        
        print(f"LoginBroker initialized for {self.base_url}")
        print(f"Using Basic Auth: {self.basic_auth_header[:20]}...")
    
    def acquire_session(self, headless: bool = True) -> Dict[str, any]:
        """
        Acquire session cookies by automating the login process.
        
        Args:
            headless: Whether to run browser in headless mode
            
        Returns:
            Dict containing cookie_header, expires_at, and other session info
        """
        print("=== Starting Playwright Session Acquisition ===")
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=headless)
            
            try:
                # Create context with Basic Auth credentials and consistent User-Agent
                context = browser.new_context(
                    user_agent=self.user_agent,
                    http_credentials={
                        'username': self.pantheon_username,
                        'password': self.pantheon_password
                    }
                )
                
                print(f"✅ Browser context created with Basic Auth credentials")
                print(f"🛡️ Username: {self.pantheon_username}")
                
                # Navigate to login page
                page = context.new_page()
                login_url = f"{self.base_url}/login?destination=/"
                
                print(f"🌐 Navigating to: {login_url}")
                print("🛡️ Attempting Basic Auth (Shield) automatically...")
                
                page.goto(login_url, wait_until="networkidle", timeout=30000)
                
                # Wait a moment for page to stabilize
                page.wait_for_timeout(2000)
                
                # Check if we successfully passed Basic Auth
                print(f"📍 Current URL: {page.url}")
                print(f"📄 Page title: {page.title()}")
                
                # Check for Basic Auth success - should see the login page
                current_title = page.title()
                if "login" in current_title.lower() or "avante" in current_title.lower():
                    print("✅ Successfully passed Basic Auth (Shield)")
                else:
                    print(f"⚠️ Unexpected page after Basic Auth: {current_title}")
                    # Take a screenshot for debugging
                    if not headless:
                        page.screenshot(path="debug_after_basic_auth.png")
                        print("📸 Screenshot saved: debug_after_basic_auth.png")
                
                # Look for login form elements
                login_result = self._perform_login(page)
                if not login_result:
                    return {"error": "Login failed"}
                
                # Extract cookies
                cookie_data = self._extract_cookies(context)
                
                return cookie_data
                
            finally:
                browser.close()
    
    def _perform_login(self, page: Page) -> bool:
        """
        Perform the application login via form submission.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            print("🔍 Looking for login triggers and form elements...")
            
            # First, try to trigger the login form by clicking login links
            login_triggers = [
                "a:has-text('login')",
                "a:has-text('entrar')",
                "button:has-text('login')",
                "button:has-text('entrar')",
                "[data-login]",
                ".login-button"
            ]
            
            # Try to click a login trigger
            login_triggered = False
            for trigger in login_triggers:
                try:
                    elements = page.locator(trigger).all()
                    if elements and len(elements) > 0:
                        print(f"🔗 Found {len(elements)} login triggers: {trigger}")
                        # Click the first visible one
                        for element in elements:
                            if element.is_visible():
                                print(f"🔗 Clicking login trigger: {trigger}")
                                element.click()
                                login_triggered = True
                                # Wait for login form to appear
                                page.wait_for_timeout(2000)
                                break
                        if login_triggered:
                            break
                except Exception as e:
                    print(f"⚠️ Error trying trigger {trigger}: {e}")
                    continue
            
            # Wait a bit more for dynamic content
            if login_triggered:
                print("⏳ Waiting for login form to load...")
                page.wait_for_timeout(3000)
            
            # Look for login form fields (Portuguese-specific selectors from screenshot)
            email_selectors = [
                'input[placeholder*="E-mail"]',     # From screenshot: "E-mail ou CPF *"
                'input[placeholder*="CPF"]',        # From screenshot: "E-mail ou CPF *"  
                'input[placeholder*="e-mail"]',     # Lowercase variant
                'input[placeholder*="email"]',      # Generic email
                'input[name="mail"]',
                'input[type="email"]', 
                '#edit-name',
                '#user-email',
                'input[name="email"]',
                'input[name="username"]',
                'input[name="user"]',
                'input[placeholder*="usuário"]',
                'input[id*="email"]',
                'input[id*="user"]'
            ]
            
            password_selectors = [
                'input[placeholder*="Senha"]',      # From screenshot: "Senha *"
                'input[placeholder*="senha"]',      # Lowercase variant
                'input[type="password"]',           # Most likely match
                'input[name="pass"]',
                'input[name="password"]',
                '#edit-pass',
                '#user-password',
                'input[name="senha"]',
                'input[placeholder*="password"]',
                'input[id*="pass"]',
                'input[id*="senha"]'
            ]
            
            # Also check iframes for login forms
            frames = page.frames
            if len(frames) > 1:
                print(f"🖼️ Checking {len(frames)} frames for login forms...")
                for i, frame in enumerate(frames):
                    try:
                        # Look for email/password inputs in frames
                        frame_email = None
                        frame_password = None
                        
                        for selector in email_selectors:
                            if frame.locator(selector).is_visible():
                                frame_email = selector
                                print(f"✅ Found email in frame {i}: {selector}")
                                break
                        
                        for selector in password_selectors:
                            if frame.locator(selector).is_visible():
                                frame_password = selector
                                print(f"✅ Found password in frame {i}: {selector}")
                                break
                        
                        if frame_email and frame_password:
                            print(f"🎯 Using login form in frame {i}")
                            return self._fill_login_form(frame, [frame_email], [frame_password])
                            
                    except Exception as e:
                        print(f"⚠️ Error checking frame {i}: {e}")
                        continue
            
            # Try to find email field in main page
            return self._fill_login_form(page, email_selectors, password_selectors)
            
        except Exception as e:
            print(f"❌ Login failed with error: {e}")
            return False
    
    def _fill_login_form(self, page_or_frame, email_selectors, password_selectors):
        """
        Fill and submit the login form.
        
        Args:
            page_or_frame: Playwright page or frame object
            email_selectors: List of email field selectors
            password_selectors: List of password field selectors
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Try to find email field
            email_field = None
            for selector in email_selectors:
                try:
                    if page_or_frame.locator(selector).is_visible(timeout=2000):
                        email_field = selector
                        print(f"✅ Found email field: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                print("❌ Could not find email field")
                return False
            
            # Try to find password field
            password_field = None
            for selector in password_selectors:
                try:
                    if page_or_frame.locator(selector).is_visible(timeout=2000):
                        password_field = selector
                        print(f"✅ Found password field: {selector}")
                        break
                except:
                    continue
            
            if not password_field:
                print("❌ Could not find password field")
                return False
            
            # Fill login form
            print(f"📝 Filling email: {self.app_email}")
            page_or_frame.fill(email_field, self.app_email)
            
            print(f"📝 Filling password: {'*' * len(self.app_password)}")
            page_or_frame.fill(password_field, self.app_password)
            
            # Submit form (try multiple methods)
            print("🚀 Submitting login form")
            try:
                # Try clicking submit button first (Portuguese-specific from screenshot)
                submit_selectors = [
                    'input[value="Enviar"]',            # Specific to the login submit button
                    'button:has-text("ENVIAR")',       # From screenshot: "ENVIAR" button
                    'button:has-text("Enviar")',       # Case variants
                    'button:has-text("enviar")',
                    '.gigya-input-submit[value="Enviar"]',  # More specific Gigya login submit
                    'input[type="submit"][value="Enviar"]', # Specific submit with Enviar text
                    'input.submitBtn',                  # Class from the output
                    'button:has-text("entrar")',
                    'button:has-text("login")',
                    '.login-submit'
                ]
                
                submit_clicked = False
                for submit_selector in submit_selectors:
                    try:
                        submit_element = page_or_frame.locator(submit_selector)
                        if submit_element.count() > 0 and submit_element.is_visible(timeout=1000):
                            print(f"🎯 Found submit button: {submit_selector}")
                            submit_element.click()
                            submit_clicked = True
                            print(f"✅ Clicked submit button: {submit_selector}")
                            break
                    except Exception as btn_e:
                        print(f"⚠️ Submit button {submit_selector} failed: {btn_e}")
                        continue
                
                if not submit_clicked:
                    # Fallback to pressing Enter on the form field
                    print("🔄 Fallback: Pressing Enter on password field")
                    try:
                        # Focus the password field and press Enter
                        page_or_frame.focus(password_field)
                        # If it's a frame, we need to use the page's keyboard
                        if hasattr(page_or_frame, 'page'):  # It's a frame
                            page_or_frame.page.keyboard.press("Enter")
                        else:  # It's a page
                            page_or_frame.keyboard.press("Enter")
                    except Exception as kb_e:
                        print(f"⚠️ Keyboard fallback failed: {kb_e}")
                    
            except Exception as e:
                print(f"⚠️ Submit attempt failed: {e}")
                return False
            
            # Wait for navigation/response - be very patient!
            print("⏳ Waiting for login response (being patient)...")
            try:
                # For frames, we need to wait on the page instead
                if hasattr(page_or_frame, 'page'):  # It's a frame
                    page_or_frame.page.wait_for_load_state("networkidle", timeout=20000)
                else:  # It's a page
                    page_or_frame.wait_for_load_state("networkidle", timeout=20000)
            except Exception as wait_e:
                print(f"⚠️ Wait for navigation failed: {wait_e}")
                # Continue anyway to check results
            
            # Give extra time for any delayed responses (login can take time)
            print("⏳ Giving extra time for login processing...")
            page_or_frame.wait_for_timeout(5000)  # 5 seconds extra
            
            # Check for and handle cookie consent dialog (sign of successful login!)
            print("🍪 Checking for cookie consent dialog...")
            cookie_consent_handled = self._handle_cookie_consent(page_or_frame)
            if cookie_consent_handled:
                print("✅ Successfully handled cookie consent - login worked!")
                return True
            
            # Check for login error messages in Portuguese
            error_indicators = [
                'text="Usuário ou senha inválidos"',
                'text="Login inválido"', 
                'text="Credenciais inválidas"',
                'text="Erro"',
                '.error-message',
                '.alert-error',
                '[role="alert"]'
            ]
            
            for error_sel in error_indicators:
                try:
                    if page_or_frame.locator(error_sel).is_visible():
                        error_text = page_or_frame.locator(error_sel).text_content()
                        print(f"❌ Login error detected: {error_text}")
                        return False
                except:
                    continue
            
            # Check if login was successful (more comprehensive check)
            page = page_or_frame.page if hasattr(page_or_frame, 'page') else page_or_frame
            
            print("🔍 Performing comprehensive login success check...")
            
            # Get current URL
            current_url = page.url if hasattr(page, 'url') else "unknown"
            current_title = page.title() if hasattr(page, 'title') else "unknown"
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Current title: {current_title}")
            
            # Wait a bit more for any final redirects
            print("⏳ Waiting for any final redirects...")
            page.wait_for_timeout(3000)
            
            # Check URL again after waiting
            final_url = page.url if hasattr(page, 'url') else current_url
            final_title = page.title() if hasattr(page, 'title') else current_title
            print(f"📍 Final URL: {final_url}")
            print(f"📄 Final title: {final_title}")
            
            # Look for indicators of successful login
            success_indicators = [
                'a[href*="logout"]',  # Logout link
                'a[href*="sair"]',    # Portuguese logout
                '.user-menu',         # User menu
                '[data-testid="user-menu"]',
                '.user-account',
                'nav.user',
                '.user-profile',
                '.logged-in',
                '.user-info'
            ]
            
            for indicator in success_indicators:
                try:
                    if page.locator(indicator).is_visible(timeout=5000):
                        print(f"✅ Login successful - found indicator: {indicator}")
                        return True
                except:
                    continue
            
            # Check if we're not on login page anymore
            if "/login" not in final_url.lower():
                print("✅ Login likely successful - redirected away from login page")
                return True
            
            # Check if title changed (another success indicator)
            if "login" not in final_title.lower() and final_title != current_title:
                print(f"✅ Login likely successful - title changed to: {final_title}")
                return True
            
            # If we're still here, check page content for success indicators
            success_text_indicators = [
                "bem-vindo",  # Welcome in Portuguese
                "dashboard",
                "perfil",
                "minha conta",
                "logout",
                "sair"
            ]
            
            page_content = ""
            try:
                page_content = page.content().lower()
                for text_indicator in success_text_indicators:
                    if text_indicator in page_content and "login" not in page_content[:1000]:  # Check first 1000 chars
                        print(f"✅ Login likely successful - found text indicator: {text_indicator}")
                        return True
            except:
                pass
            
            print("⚠️ Could not confirm login success - may need manual verification")
            return False
            
        except Exception as e:
            print(f"❌ Form filling failed: {e}")
            return False
    
    def _handle_cookie_consent(self, page_or_frame) -> bool:
        """
        Look for and handle cookie consent dialogs.
        
        Args:
            page_or_frame: Playwright page or frame object
            
        Returns:
            True if cookie consent found and handled, False otherwise
        """
        try:
            # Get the page reference (if we're in a frame)
            page = page_or_frame.page if hasattr(page_or_frame, 'page') else page_or_frame
            
            # Common Portuguese cookie consent selectors
            cookie_consent_selectors = [
                # Text-based selectors for "Accept" in Portuguese
                'button:has-text("Aceitar")',
                'button:has-text("Aceitar todos")',
                'button:has-text("Aceitar cookies")',
                'button:has-text("ACEITAR")',
                'button:has-text("Accept")',
                'button:has-text("Allow all")',
                
                # Common cookie consent element IDs/classes
                '#accept-cookies',
                '#accept-all-cookies',
                '.accept-cookies',
                '.cookie-accept',
                '[data-accept="cookies"]',
                '.onetrust-accept-btn-handler',
                '#onetrust-accept-btn-handler',
                '.consent-accept',
                
                # OneTrust specific (common cookie consent platform)
                '.ot-sdk-button',
                '#accept-recommended-btn-handler'
            ]
            
            print(f"🔍 Looking for cookie consent dialogs...")
            
            for selector in cookie_consent_selectors:
                try:
                    element = page.locator(selector)
                    if element.count() > 0 and element.is_visible(timeout=2000):
                        print(f"🍪 Found cookie consent element: {selector}")
                        element.click()
                        print(f"✅ Clicked cookie consent: {selector}")
                        
                        # Wait a moment for the dialog to disappear
                        page.wait_for_timeout(2000)
                        return True
                        
                except Exception as click_e:
                    print(f"⚠️ Failed to click {selector}: {click_e}")
                    continue
            
            print("ℹ️ No cookie consent dialog found")
            return False
            
        except Exception as e:
            print(f"⚠️ Error handling cookie consent: {e}")
            return False
    
    def _extract_cookies(self, context: BrowserContext) -> Dict[str, any]:
        """
        Extract and format cookies from browser context.
        
        Args:
            context: Playwright browser context
            
        Returns:
            Dict with cookie_header, expires_at, etc.
        """
        try:
            print("🍪 Extracting cookies from browser context")
            
            # Get all cookies
            cookies = context.cookies()
            print(f"📊 Found {len(cookies)} cookies")
            
            # Build cookie header string and find expiry
            cookie_parts = []
            earliest_expiry = None
            session_cookies_found = []
            
            for cookie in cookies:
                cookie_name = cookie['name']
                cookie_value = cookie['value']
                
                # Add to header string
                cookie_parts.append(f"{cookie_name}={cookie_value}")
                
                # Track session-related cookies
                if any(pattern in cookie_name.lower() for pattern in ['sess', 'session', 'auth', 'login']):
                    session_cookies_found.append(cookie_name)
                
                # Find earliest expiry for cache management
                if cookie.get('expires') and cookie['expires'] > 0:
                    cookie_expires = datetime.fromtimestamp(cookie['expires'])
                    if not earliest_expiry or cookie_expires < earliest_expiry:
                        earliest_expiry = cookie_expires
            
            # Create cookie header
            cookie_header = "; ".join(cookie_parts)
            
            # Default expiry if none found (8 hours from now)
            if not earliest_expiry:
                earliest_expiry = datetime.now() + timedelta(hours=8)
            
            print(f"✅ Session cookies found: {session_cookies_found}")
            print(f"📅 Cookies expire at: {earliest_expiry}")
            print(f"🍪 Cookie header length: {len(cookie_header)} chars")
            
            return {
                "cookie_header": cookie_header,
                "expires_at": earliest_expiry,
                "session_cookies": session_cookies_found,
                "total_cookies": len(cookies),
                "success": True,
                "user_agent": self.user_agent,
                "basic_auth": self.basic_auth_header
            }
            
        except Exception as e:
            print(f"❌ Cookie extraction failed: {e}")
            return {
                "error": f"Cookie extraction failed: {e}",
                "success": False
            }