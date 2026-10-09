# Showroom AKB48 Qmsg Monitor

## 中文说明

自动监控 Showroom 上的 AKB48 直播，并通过 Qmsg 私聊发送通知。

默认行为：

- 监控全部 AKB48 成员
- 每 3 分钟检查一次
- 自动避免重复通知
- 通过 Qmsg v3 私聊推送
- 成员筛选为可选功能

### 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests

