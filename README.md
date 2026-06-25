# NodeSeek 每日签到

自动登录 [nodeseek.com](https://www.nodeseek.com) 并点击每日签到。

## 功能

- 自动处理 Cloudflare Turnstile 验证
- Cookie 缓存，减少重复登录
- 签到结果输出

## 部署方式

### 本地 VPS

```bash
# 1. 安装依赖
pip install -r requirements.txt
python -m playwright install chromium

# 2. 配置环境变量
export NODESEEK_USERNAME="你的用户名"
export NODESEEK_PASSWORD="你的密码"

# 3. 手动测试
python nodeseek_checkin.py

# 4. 设置 cron（每天 07:00 CST）
crontab -e
# 添加：
# 0 7 * * * cd /path/to/nodeseek-checkin && python nodeseek_checkin.py
```

### GitHub Actions

> ⚠️ 暂不支持。GitHub Actions 的 headless 环境无法通过 Cloudflare Turnstile 验证，建议在本地 VPS 上通过 cron 执行。

## 项目文件

| 文件 | 说明 |
|------|------|
| `nodeseek_checkin.py` | 签到主脚本 |
| `requirements.txt` | Python 依赖 |

## 原理

1. 使用 `scrapling` 的 StealthyFetcher 加载页面，自动绕过 Cloudflare
2. 模拟鼠标点击触发 Turnstile 自动验证
3. 填写表单，点击登录
4. Cookie 缓存到本地文件，下次优先复用
5. Cookie 过期则自动重新登录
6. 定位到签到按钮并点击

## License

MIT
