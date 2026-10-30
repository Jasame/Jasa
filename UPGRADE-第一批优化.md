# 第一批优化：账户安全、可靠备份、新手引导

适用于已经运行的 https://jasa.hk/bank/，应用目录 `/www/wwwroot/jwb-cloud`，运行用户 `www`，服务名 `jwb-cloud`。本次更新不改 Nginx、SMTP 配置或应用密钥，不重新创建账户。新增数据表会在服务启动时自动创建，旧账户、卡片、模拟资产与登录会话保持兼容。

## 这一批完成了什么

- 账户安全页面：查看当前和其他浏览器会话、登录与最近活跃时间、会话到期时间、近似网段；单独撤销一个其他会话或退出其他所有会话。旧版会话没有设备详情，可用“退出其他设备”清理。
- 修改密码：验证当前密码，新密码 10–128 位；成功后所有设备退出，重新登录。找回密码仍可使用。
- 换绑邮箱：当前密码、新旧邮箱各一个验证码，三者同时验证。验证码与用户及用途绑定，成功后撤销所有会话和相关验证码；资产仍属于同一个账户。
- 展示最近 20 条成功登录、撤销会话、密码更新及邮箱更新安全记录。设备是浏览器会话，不是硬件清单；只存 IPv4 /24 或 IPv6 /64 网段，不做地理位置推断；最近活跃时间约 5 分钟更新一次。
- 保留原有密码登录 IP / 邮箱双重限流，增加安全设置限流；验证码发送沿用上次修复后的共享冷却与准确等待时间。SMTP SSL 连接显式启用系统证书验证。
- 网络异常、请求超时、服务端异常提示；交易响应丢失后，在当前页面重试相同参数会复用幂等键。若刷新页面导致重试键丢失，先检查账单与余额再决定是否重新提交。
- 四步体验引导：模拟入金、申请卡片、首次消费、查看账单。进度由服务端真实记录推导；隐藏偏好跨设备保存，支持重新显示。账户重置后重新计算进度。
- 备份：在线一致性复制、SHA-256、SQLite 完整性/外键/核心结构检查、独立内存数据库恢复检查。每日任务默认保留最近 14 份自动备份，不删除手动备份。恢复前自动保留当前数据副本，恢复后清除旧会话与验证码。

## 1. 更新前先备份

宝塔终端使用有管理权限的账户执行：

```bash
cd /www/wwwroot/jwb-cloud
mkdir -p /www/backup/jwb-cloud
chown www:www /www/backup/jwb-cloud
chmod 700 /www/backup/jwb-cloud
sudo -u www .venv/bin/python manage.py backup "/www/backup/jwb-cloud/pre-phase1-$(date +%Y%m%d-%H%M%S).sqlite3"
```

确认命令成功后再继续。该路径不应被任何 Nginx 静态目录或 alias 公开。请另外保存当前程序文件的副本，方便回退；备份 `.env` 时保持私密。数据库备份不包含 SMTP 密码和 APP_SECRET。

## 2. 停止服务，覆盖更新文件

```bash
systemctl stop jwb-cloud
```

将部署包内下列文件覆盖到 `/www/wwwroot/jwb-cloud/` 的对应位置：

```text
app.py
manage.py
backup_tools.py
static/cloud.js
static/cloud.css
static/index.html
deploy/jwb-backup.service
deploy/jwb-backup.timer
```

也可同步 README、此升级说明及 tests。不要覆盖服务器现有 `.env`、`data/`、`.venv/` 或 `gunicorn.conf.py`。本次没有新增第三方依赖。

```bash
cd /www/wwwroot/jwb-cloud
chown www:www app.py manage.py backup_tools.py static/cloud.js static/cloud.css static/index.html
systemctl start jwb-cloud
systemctl status jwb-cloud --no-pager
```

打开网站按 Ctrl+F5。进入“账户总览”检查体验引导，进入“账户安全”检查设备列表。测试修改密码会让所有设备退出，请准备好重新登录。无需重新运行 create-user 或重建数据库。

若启动失败，查看 `journalctl -u jwb-cloud -n 80 --no-pager`，恢复旧程序文件再启动。新表是额外表，旧版程序可忽略它们；程序回退通常不需要回退数据库。

## 3. 先手动执行一次新备份

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py backup-daily /www/backup/jwb-cloud --keep 14
```

成功输出应包含 `restoreDrill: passed`，以及备份绝对路径。目录中会有 `.sqlite3` 和同名 `.sqlite3.json` 校验报告。该恢复检查在独立内存数据库执行，不覆盖正在运行的数据，也不代表服务器级灾难恢复已经验收。

如果失败，先处理权限或错误，暂不启用每日任务。

## 4. 启用每日自动备份

```bash
cd /www/wwwroot/jwb-cloud
cp deploy/jwb-backup.service /etc/systemd/system/jwb-backup.service
cp deploy/jwb-backup.timer /etc/systemd/system/jwb-backup.timer
systemctl daemon-reload
systemctl start jwb-backup.service
systemctl status jwb-backup.service --no-pager
```

这是一次性任务，完成后显示 `inactive (dead)` 属正常；关键是退出状态成功，而不是持续运行。确认成功后：

```bash
systemctl enable --now jwb-backup.timer
systemctl list-timers --all jwb-backup.timer
journalctl -u jwb-backup.service -n 40 --no-pager
```

定时器设置为北京时间每天 04:15 后的 5 分钟内运行；服务器关机错过任务时，开机后补执行一次。若系统不接受时区写法，先用 `systemd-analyze calendar '*-*-* 04:15:00 Asia/Shanghai'` 查看错误再调整。不要另外在宝塔计划任务重复安排同一备份。

默认仅保留最近 14 份“自动”备份；失败不会触发轮换。此轮提供同机备份，不能抵御整台服务器或磁盘丢失，请把重要备份定期复制到另一处受限存储。

## 5. 需要恢复时才执行

日常更新不要执行本节。恢复会将账户数据回退到选定备份时间。将示例文件名换成真实存在的备份文件名。

先验证目标备份：

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py verify-backup /www/backup/jwb-cloud/实际备份文件名.sqlite3
```

验证通过后，暂停定时器并停止应用；确认没有其他宝塔进程在运行此应用，再恢复：

```bash
systemctl stop jwb-backup.timer
systemctl stop jwb-cloud
sudo -u www .venv/bin/python manage.py restore /www/backup/jwb-cloud/实际备份文件名.sqlite3 --safety-copy "/www/backup/jwb-cloud/before-restore-$(date +%Y%m%d-%H%M%S).sqlite3" --service-stopped
```

`--service-stopped` 是你确认已停止服务的显式标志，不会自动检查所有应用进程。工具先验证备份，再备份当前数据库到一个全新文件名，然后通过 SQLite 备份接口恢复，不手工覆盖带 WAL 的数据库文件。任何错误都先看输出，不要删除唯一数据副本。

恢复成功后：

```bash
systemctl start jwb-cloud
systemctl start jwb-backup.timer
```

所有用户需重新登录；检查用户数、卡片、余额和账务。旧版备份可能没有新表，应用启动后会自动补齐。必须自行保管 `.env`，恢复数据库不包含它。

## 验证记录

本轮 29 项自动化测试覆盖旧功能、旧数据库升级、设备归属/撤销、改密全设备退出、换绑双重验证、限流、引导隔离与重置、备份校验/轮换/恢复与恢复前留档。浏览器验证覆盖中英文、320/390/768/1440 宽度、会话撤销、改密与换绑、模拟丢失交易响应后的安全重试。测试邮件使用内存收件箱，不发送真实邮件。

最终部署、真实 SMTP 验证码与定时任务需在你的服务器按上述步骤验收；更新包并不表示已自动修改线上服务器。

实现参考：Python 3.11 sqlite3 在线备份接口 https://docs.python.org/3.11/library/sqlite3.html ，SMTP SSL context https://docs.python.org/3.11/library/smtplib.html ，systemd timer https://github.com/systemd/systemd/blob/main/man/systemd.timer.xml 。
