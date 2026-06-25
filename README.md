# NodeSeek 每日签到

自动签到 [nodeseek.com](https://www.nodeseek.com)，每天 07:00 CST 执行。

## 功能

- 通过 `cloudscraper` 直接调用 API，绕过 Cloudflare
- Cookie 复用，无需每次登录
- 签到结果输出鸡腿数量

## 部署方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 准备 Cookie
# 在浏览器登录 nodeseek.com，F12 → Application → Cookies
# 复制 session/pjwt/smac 等 cookie 保存到 cookies.json

# 3. 手动测试
python nodeseek_checkin.py

# 4. 设置 cron（每天 07:00 CST）
crontab -e
# 添加：
# 0 7 * * * cd /path/to/nodeseek-checkin && python nodeseek_checkin.py
```

## 项目文件

| 文件 | 说明 |
|------|------|
| `nodeseek_checkin.py` | 签到脚本 |
| `requirements.txt` | Python 依赖 |

## 原理

1. 读取本地缓存的 Cookie
2. 使用 `cloudscraper` 模拟浏览器 TLS 指纹，绕过 Cloudflare
3. 直接调用 `POST /api/attendance?random=false` 完成签到
4. Cookie 过期时输出失败信息，需重新获取

## License

MIT
