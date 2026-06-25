# NodeSeek 每日签到 Bot

自动登录 nodeseek.com 并点击每日签到按钮。

## 使用方法

```bash
export NODESEEK_USERNAME="你的用户名"
export NODESEEK_PASSWORD="你的密码"
pip install -r requirements.txt
python -m playwright install chromium
python nodeseek_checkin.py
```

## GitHub Actions 部署

1. Fork 此仓库
2. 设置 Secrets:
   - `NODESEEK_USERNAME` — 你的 NodeSeek 用户名
   - `NODESEEK_PASSWORD` — 你的 NodeSeek 密码
3. 启用 Actions（默认每天 UTC 23:00 = CST 07:00 自动签到）
4. 在 Actions 页面查看签到结果

> ⚠️ 密码仅存储在 GitHub Secrets 中，不会泄露到日志或代码中。
