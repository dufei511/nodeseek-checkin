# NodeSeek 每日签到

自动登录 [nodeseek.com](https://www.nodeseek.com) 并点击每日签到。

## 功能

- 自动处理 Cloudflare Turnstile 验证
- Cookie 缓存，减少重复登录
- 支持本地 VPS cron 和 GitHub Actions 两种部署方式
- 签到结果 JSON 输出

## 部署方式

### 方式一：本地 VPS（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt
python -m playwright install chromium

# 2. 手动测试
export NODESEEK_USERNAME="你的用户名"
export NODESEEK_PASSWORD="你的密码"
python nodeseek_checkin.py

# 3. 设置 cron（每天 07:00 CST）
crontab -e
# 添加：
# 0 7 * * * cd /path/to/nodeseek-checkin && python nodeseek_checkin.py >> /var/log/nodeseek.log 2>&1
```

### 方式二：GitHub Actions

1. Fork 此仓库
2. 进入 Settings → Secrets and variables → Actions
3. 添加以下 Secrets：

| Secret | 说明 |
|--------|------|
| `NODESEEK_USERNAME` | NodeSeek 用户名 |
| `NODESEEK_PASSWORD` | NodeSeek 密码 |

4. Actions 会自动按 **UTC 23:00（CST 07:00）** 每天运行
5. 也可在 Actions 页面手动触发 `workflow_dispatch`

> ⚠️ 密码仅存储在 GitHub Secrets 中，不会泄露到日志或代码

## 项目文件

| 文件 | 说明 |
|------|------|
| `nodeseek_checkin.py` | 签到主脚本 |
| `.github/workflows/checkin.yml` | GitHub Actions 配置 |
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
