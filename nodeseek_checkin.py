#!/usr/bin/env python3
"""
NodeSeek daily check-in script
Uses cloudscraper to bypass Cloudflare, calls API directly
Outputs plain text for no_agent cron delivery
"""
import json, os, sys
import cloudscraper

COOKIE_PATH = os.path.expanduser("~/.hermes/nodeseek_cookies.json")
API_URL = "https://www.nodeseek.com/api/attendance?random=false"
REFERER = "https://www.nodeseek.com/board"


def load_cookies() -> dict:
    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH) as f:
            cookies = json.load(f)
        return {c["name"]: c["value"] for c in cookies}
    return {}


def main():
    cookie_dict = load_cookies()
    if not cookie_dict:
        print("❌ NodeSeek 签到失败：Cookie 文件为空")
        return 1

    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://www.nodeseek.com",
        "Referer": REFERER,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        resp = scraper.post(API_URL, headers=headers, cookies=cookie_dict, timeout=30)
        data = resp.json()
        if data.get("success"):
            gain = data.get("gain", 0)
            total = data.get("current", 0)
            print(f"✅ NodeSeek 签到成功！获得 {gain} 🍗，当前共 {total} 鸡腿")
            return 0
        else:
            msg = data.get("message", "未知错误")
            print(f"❌ NodeSeek 签到失败：{msg}")
            return 1
    except Exception as e:
        print(f"❌ NodeSeek 签到异常：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
