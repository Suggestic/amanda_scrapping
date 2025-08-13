# Stage 0.6: Manual Cookie Extraction Instructions

## Purpose
Before we automate login with Playwright, we need to test that our Firecrawl integration works with both Basic Auth and session cookies. This requires manually extracting cookies from your browser.

## Step-by-Step Instructions

### 1. Open Browser and Navigate to Site
1. Open your browser (Chrome/Firefox recommended)
2. Navigate to: `https://dev-73046-nhsc-avante-brazil.pantheonsite.io/`
3. You should see the Basic Auth popup

### 2. Enter Shield Credentials
- **Username**: `shield`
- **Password**: `qaz123!@#`
- Click OK or press Enter

### 3. Login to Application
1. You should now see the site login page
2. Enter the application credentials:
   - **Email**: `bot@nestle.com`
   - **Password**: `80tN3$tl3`
3. Submit the login form

### 4. Extract Session Cookies
Once logged in successfully:

#### For Chrome:
1. Press `F12` to open Developer Tools
2. Go to **Application** tab
3. In the left sidebar, expand **Cookies**
4. Click on `https://dev-73046-nhsc-avante-brazil.pantheonsite.io`
5. You'll see a list of cookies with Name and Value columns

#### For Firefox:
1. Press `F12` to open Developer Tools
2. Go to **Storage** tab
3. Expand **Cookies** in the left sidebar
4. Click on the site URL
5. You'll see the cookies list

### 5. Format Cookie Header
You need to create a Cookie header string in this format:
```
name1=value1; name2=value2; name3=value3
```

**Common cookie names to look for:**
- `sessionid`
- `csrftoken` 
- `PHPSESSID`
- `SESS*` (Drupal session cookies)

**Example:**
If you see:
- sessionid: `abc123def456`
- csrftoken: `xyz789uvw012`

Format as: `sessionid=abc123def456; csrftoken=xyz789uvw012`

### 6. Test with Manual Extraction Script
Copy your formatted cookie string and run:
```bash
python3 test_manual_cookies.py "sessionid=abc123def456; csrftoken=xyz789uvw012"
```

## Expected Results
- The script should connect to Firecrawl
- Pass both Basic Auth and your session cookies
- Retrieve content that is NOT a login page
- Show `metadata.statusCode = 200`

## Troubleshooting
- **401/403 errors**: Check if cookies are formatted correctly
- **Login page returned**: Cookies may have expired, extract fresh ones
- **Connection errors**: Verify the Basic Auth is working first

## Security Note
- Never commit real cookies to version control
- Cookies will expire, so you may need to repeat this process
- This is temporary - Stage 1 will automate this completely