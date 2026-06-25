#!/usr/bin/env python3
"""
NodeSeek Daily Check-in Bot
- Logs in with credentials from env vars (or saved cookies)
- Clicks the daily check-in button
- Reports result via stdout JSON
"""
import json, os, sys, time
from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page

COOKIE_PATH = os.path.expanduser("~/.hermes/nodeseek_cookies.json")
COOKIE_FILE = os.environ.get("NODESEEK_COOKIE_FILE", COOKIE_PATH)
USERNAME = os.environ.get("NODESEEK_USERNAME") or os.environ.get("NODESEEK_EMAIL")
PASSWORD = os.environ.get("NODESEEK_PASSWORD")
LOGIN_URL = "https://www.nodeseek.com/signIn.html"
HOME_URL = "https://www.nodeseek.com/"


def do_login(page: Page) -> bool:
    """Log in with credentials, save cookies, return success"""
    page.goto(LOGIN_URL, wait_until="networkidle")
    page.wait_for_selector("#stacked-email", timeout=15000)
    time.sleep(1)

    page.fill("#stacked-email", USERNAME or "")
    page.fill("#stacked-password", PASSWORD or "")

    # Click blank area to trigger Turnstile
    page.mouse.click(100, 100)
    time.sleep(1)

    # Wait for Turnstile to solve (up to 25s)
    for _ in range(25):
        val = page.evaluate("""() => {
            var inp = document.querySelector('input[name="cf-turnstile-response"]');
            return inp ? inp.value : '';
        }""")
        if val and len(val) > 10:
            break
        time.sleep(1)

    # Click login button
    btn = page.query_selector("form button")
    if btn:
        btn.click()
        time.sleep(3)

    # Save cookies
    try:
        cookies = page.context.cookies()
        os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f)
    except Exception as e:
        print(json.dumps({"status": "warn", "message": f"保存 cookie 失败: {e}"}))

    # Verify login
    page.goto(HOME_URL, wait_until="networkidle")
    time.sleep(2)
    body = page.inner_text("body")
    return "签到" in body or "yubinbin" in body or "user-card" in page.content()


def restore_session(page: Page) -> bool:
    """Restore saved cookies, return True if still valid"""
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE) as f:
                cookies = json.load(f)
            page.context.add_cookies(cookies)
            page.goto(HOME_URL, wait_until="networkidle")
            time.sleep(2)
            body = page.inner_text("body")
            return "签到" in body or "yubinbin" in body or "user-card" in page.content()
        except Exception:
            pass
    return False


def click_checkin(page: Page) -> str:
    """Click the check-in button, return status"""
    return page.evaluate("""() => {
        var span = document.querySelector('span[title="签到"]');
        if (span) { span.click(); return 'clicked'; }
        return 'not_found';
    }""")


def main():
    result = {"status": "fail", "message": "", "checkin_result": ""}

    if not USERNAME or not PASSWORD:
        result = {
            "status": "error",
            "message": "环境变量 NODESEEK_USERNAME/NODESEEK_PASSWORD 未设置",
        }
        print(json.dumps(result, ensure_ascii=False))
        return 1

    try:
        def run(page: Page):
            nonlocal result

            logged_in = restore_session(page)

            if not logged_in:
                print(json.dumps({"status": "info", "message": "Cookie 过期，重新登录..."}, ensure_ascii=False), flush=True)
                logged_in = do_login(page)

            if not logged_in:
                result = {"status": "error", "message": "登录失败"}
                return

            checkin_status = click_checkin(page)
            time.sleep(3)

            body_text = page.inner_text("body")

            # Detect check-in result messages
            checkin_msgs = []
            for line in body_text.split("\n"):
                line = line.strip()
                if any(k in line for k in ["签到成功", "已签到", "积分", "奖励", "连续签到", "今日签到"]):
                    checkin_msgs.append(line)

            result = {
                "status": "success" if checkin_status == "clicked" else "warning",
                "message": "; ".join(checkin_msgs[:5]) if checkin_msgs else "签到按钮已点击",
                "checkin_result": checkin_status,
            }

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

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
