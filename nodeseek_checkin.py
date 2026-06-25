#!/usr/bin/env python3
"""
NodeSeek Daily Check-in Bot
- Login via Turnstile-protected form
- Visit /board to auto check-in
- Verify result via page text
"""
import json, os, sys, time
from scrapling.fetchers import StealthyFetcher
from playwright.sync_api import Page

USERNAME = os.environ.get("NODESEEK_USERNAME")
PASSWORD = os.environ.get("NODESEEK_PASSWORD")

COOKIE_PATH = os.environ.get("NODESEEK_COOKIE_FILE", "/tmp/nodeseek_cookies.json")
LOGIN_URL = "https://www.nodeseek.com/signIn.html"
BOARD_URL = "https://www.nodeseek.com/board"


def get_session_cookies(cookies: list) -> list:
    return [c for c in cookies if c["name"] not in ("colorscheme", "cf_clearance")]


def load_cookies() -> list:
    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH) as f:
            return json.load(f)
    return []


def save_cookies(cookies: list) -> bool:
    if get_session_cookies(cookies):
        with open(COOKIE_PATH, "w") as f:
            json.dump(cookies, f)
        return True
    return False


def do_login(page: Page) -> bool:
    page.goto(LOGIN_URL, wait_until="networkidle")
    time.sleep(2)
    page.wait_for_selector("#stacked-email", timeout=15000)
    page.fill("#stacked-email", USERNAME or "")
    page.fill("#stacked-password", PASSWORD or "")
    page.mouse.click(100, 100)

    for _ in range(30):
        v = page.evaluate(
            "document.querySelector('input[name=\"cf-turnstile-response\"]')?.value || ''"
        )
        if v and len(v) > 10:
            break
        time.sleep(1)

    page.query_selector("form button").click()
    time.sleep(3)
    return save_cookies(page.context.cookies())


def do_checkin(page: Page) -> dict:
    page.goto(BOARD_URL, wait_until="domcontentloaded")
    time.sleep(3)
    body_text = page.inner_text("body")

    if "今日签到获得" in body_text:
        idx = body_text.index("今日签到获得")
        msg = body_text[idx:idx+50].split("\n")[0]
        return {"status": "success", "message": msg.strip()}

    if "yubinbin" in body_text:
        return {"status": "success", "message": "今日已签到"}

    if "登录后签到" in body_text:
        return {"status": "error", "message": "未登录状态"}

    return {"status": "unknown", "message": "签到页面状态未知"}


def main():
    result = {"status": "error", "message": ""}
    exit_code = 1

    if not USERNAME or not PASSWORD:
        result = {"status": "error", "message": "需要设置 NODESEEK_USERNAME 和 NODESEEK_PASSWORD"}
        print(json.dumps(result, ensure_ascii=False))
        return 1

    try:
        def run(page: Page):
            nonlocal result, exit_code

            cookies = load_cookies()
            if cookies:
                page.context.add_cookies(cookies)

            checkin = do_checkin(page)
            if checkin["status"] == "success":
                result = checkin
                exit_code = 0
                return

            print(json.dumps({"status": "info", "message": "Cookie 过期，重新登录..."}), flush=True)
            logged_in = do_login(page)

            if not logged_in:
                result = {"status": "error", "message": "登录失败"}
                return

            checkin = do_checkin(page)
            result = checkin
            exit_code = 0 if checkin["status"] == "success" else 1

        StealthyFetcher.fetch(
            BOARD_URL,
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
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
