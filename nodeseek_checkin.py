#!/usr/bin/env python3
"""
NodeSeek Daily Check-in Bot
- Uses Playwright to login (handles Cloudflare Turnstile + Vue form)
- Clicks daily check-in button
- Reports result as JSON

Can save/load cookies between runs to minimize login attempts.
"""
import json, os, sys, time
from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page

# Config from environment or defaults
USERNAME = os.environ.get("NODESEEK_USERNAME")
PASSWORD = os.environ.get("NODESEEK_PASSWORD")
COOKIE_FILE = os.environ.get("NODESEEK_COOKIE_FILE", "/tmp/nodeseek_cookies.json")

HOME_URL = "https://www.nodeseek.com/"
LOGIN_URL = "https://www.nodeseek.com/signIn.html"


def do_login(page: Page) -> bool:
    """Login with credentials and save cookies"""
    page.goto(LOGIN_URL, wait_until="networkidle")
    page.wait_for_selector("#stacked-email", timeout=15000)
    time.sleep(1)

    page.fill("#stacked-email", USERNAME or "")
    page.fill("#stacked-password", PASSWORD or "")

    # Click blank area to trigger Turnstile auto-solve
    page.locator("body").click(position={"x": 100, "y": 100})
    time.sleep(1)

    # Wait for Turnstile to solve (up to 30s)
    for _ in range(30):
        val = page.evaluate(
            "document.querySelector('input[name=\"cf-turnstile-response\"]')?.value || ''"
        )
        if val and len(val) > 10:
            break
        time.sleep(1)

    # Click login button with native Playwright click
    btn = page.locator("form button[type='submit']").first
    if btn.count() > 0:
        btn.click()
        time.sleep(3)

    # Save cookies regardless
    cookies = page.context.cookies()
    try:
        os.makedirs(os.path.dirname(COOKIE_FILE) or ".", exist_ok=True)
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f)
    except OSError:
        pass

    # Check login success by looking for session cookies
    session_cookies = [
        c for c in cookies if c["name"] not in ("colorscheme", "cf_clearance")
    ]
    return len(session_cookies) > 0


def restore_session(page: Page) -> bool:
    """Load saved cookies and check if session still valid"""
    if not os.path.exists(COOKIE_FILE):
        return False

    try:
        with open(COOKIE_FILE) as f:
            cookies = json.load(f)
        page.context.add_cookies(cookies)
    except Exception:
        return False

    # Check if session works on home page
    page.goto(HOME_URL, wait_until="domcontentloaded")
    time.sleep(3)

    body = page.inner_text("body")
    return "签到" in body or "yubinbin" in body


def do_checkin(page: Page) -> dict:
    """Click check-in button, return result info"""
    result = page.evaluate("""() => {
        var span = document.querySelector('span[title="签到"]');
        if (span) {
            span.dispatchEvent(new MouseEvent('click', {bubbles: true, view: window}));
            return {status: "clicked", detail: span.outerHTML.slice(0, 100)};
        }
        // Check if already signed in
        var body = document.body.innerText;
        if (body.indexOf('已签到') >= 0) {
            return {status: "already", detail: "今日已签到"};
        }
        return {status: "not_found", detail: "签到按钮未找到"};
    }""")
    time.sleep(2)
    return result


def main():
    result = {"status": "error", "message": "未知错误"}
    exit_code = 1

    try:
        def run(page: Page):
            nonlocal result, exit_code

            # Step 1: Try session restore
            logged_in = restore_session(page)

            # Step 2: Login if needed
            if not logged_in:
                print(json.dumps({"status": "info", "message": "Cookie过期或不存在，重新登录..."}, ensure_ascii=False), flush=True)
                logged_in = do_login(page)

            if not logged_in:
                result = {"status": "error", "message": "登录失败"}
                return

            # Step 3: Click check-in
            checkin = do_checkin(page)

            if checkin["status"] == "already":
                result = {"status": "success", "message": "今日已签到"}
                exit_code = 0
            elif checkin["status"] == "clicked":
                result = {"status": "success", "message": "签到成功"}
                exit_code = 0
            else:
                # Try navigating to home page and retry
                page.goto(HOME_URL, wait_until="domcontentloaded")
                time.sleep(5)
                checkin = do_checkin(page)
                if checkin["status"] in ("clicked", "already"):
                    result = {"status": "success", "message": "签到成功"}
                    exit_code = 0
                else:
                    result = {"status": "warning", "message": f"页面已登录但找不到签到按钮: {checkin['detail']}"}

        StealthyFetcher.fetch(
            HOME_URL,
            headless=True,
            solve_cloudflare=True,
            block_webrtc=True,
            hide_canvas=True,
            timeout=90000,
            page_action=run,
        )
    except Exception as e:
        result = {"status": "error", "message": str(e)}

    # Handle special case: scrapling's StealthyFetcher might bypass the
    # page_action and directly return the page. Check the fetch result.
    output = json.dumps(result, ensure_ascii=False)
    print(output)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
