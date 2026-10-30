# JWB 6.0.0：现有宝塔站点升级

适用于已经正常运行的 `https://jasa.hk/bank/`，程序目录 `/www/wwwroot/jwb-cloud`，systemd 服务 `jwb-cloud`，应用用户 `www`，端口 `127.0.0.1:8895`。本轮是完整后端升级，不能只覆盖 app.py 和 static。

## 本轮内容

- 原交易关联的部分/全额退款；欠款、钱包、积分、权益抵扣、统计和账单同步冲回，保留审计记录。
- 年费周年续期、到期状态与提醒、挂失/损坏/到期补换卡、结清后销卡并保留历史。
- 可选验证器二次验证（MFA）、一次性恢复码；邮箱验证码登录和密码重置也不能绕过已启用的 MFA。管理员建议先启用。
- 服务中心：常用币种、默认卡、语言、金额隐藏及通知偏好同步；展示模式；权益与还款日历、ICS 导出。
- 用户反馈、管理员处理与站内回复、版本记录。
- 每五分钟运行的健康检查、管理员异常邮件、升级包校验、程序快照和受保护的回退流程。
- 独立临时数据库的 Playwright 浏览器回归配置，以及手机、平板、桌面项目与截图比较入口。

## 1. 上传两个文件

部署 ZIP 保留原文件名 `JWB-Cloud-5.0-宝塔部署包.zip`，包内版本为 **6.0.0**。

1. 将 ZIP 上传到 `/www/backup/JWB-Cloud-5.0-宝塔部署包.zip`。不要解压到网站公开目录。
2. 在电脑上解压同一个 ZIP，取出 `jwb-cloud/deploy/update.py`，改名为 `jwb-update.py`，上传到 `/www/backup/jwb-update.py`。

升级器保留服务器 `.env`、`data/`、`gunicorn.conf.py`；不修改 Nginx、域名、飞书 SMTP 或现有账号。ZIP 内的 gunicorn 文件仅供新安装参考，升级器会校验但不会覆盖服务器配置。请勿以包里的 `.env.example` 替换现有 `.env`，尤其不要更换 `APP_SECRET`。

## 2. 先校验，再升级

在宝塔终端以 root 执行：

```bash
/www/wwwroot/jwb-cloud/.venv/bin/python /www/backup/jwb-update.py --check-only /www/backup/JWB-Cloud-5.0-宝塔部署包.zip
```

应显示 `Package checks passed: 6.0.0`。这一步只检查 ZIP 清单、路径、文件数量、大小和 SHA-256，不修改站点。校验用于发现文件损坏，不替代对下载来源的信任。

然后执行：

```bash
/www/wwwroot/jwb-cloud/.venv/bin/python /www/backup/jwb-update.py /www/backup/JWB-Cloud-5.0-宝塔部署包.zip
```

工具会先在旁路目录安装新依赖，核对导入和 PDF 字体，再生成已校验数据库备份；暂停应用与相关定时任务，切换代码和虚拟环境，增量建表，启动服务并进行本机健康检查。安装依赖需要服务器能够访问 Python 软件包源。新增加的 `cryptography` 可能需要匹配系统的预编译 wheel；若安装阶段失败，应用尚未切换，先解决依赖下载/系统兼容问题再重试。

正常结果包含：

```text
Upgrade passed: 6.0.0
Rollback snapshot: /www/backup/jwb-releases/实际时间戳
Verified database backup: /www/backup/jwb-cloud/before-update-实际时间戳.sqlite3
```

保留输出中的实际快照路径。快照含旧程序和虚拟环境，数据库单独备份。升级器不自动清理这些快照；确认稳定后自行按保留策略清理，勿删除正在排查的问题快照。

## 3. 核对服务与页面

```bash
systemctl status jwb-cloud --no-pager
curl -fsS http://127.0.0.1:8895/bank/api/health
systemctl list-timers --all 'jwb-*'
systemctl start jwb-ops.service
journalctl -u jwb-cloud -u jwb-ops.service -n 80 --no-pager
```

健康接口应返回 `ok: true`、`version: 6.0.0`。应有 `jwb-backup.timer`、`jwb-maintenance.timer`、新增 `jwb-ops.timer`。浏览器强制刷新后核对：

1. 访客只能浏览卡片，注册用户保持零余额零卡片。
2. 登录后“我的”进入“持卡服务、日历与偏好”，或使用侧边栏“服务中心”。
3. 用模拟消费检查小额退款、账单、奖励变化；不要拿真实银行信息作测试。
4. 进入“账户安全”启用 MFA，离线保存恢复码，再测试退出重新登录。
5. 管理员打开 `/bank/admin/` →“运行与反馈”，检查监控结果及反馈回复。
6. 手机、平板、电脑检查导航、对话框、账单以及金额遮挡；切换中英文。

若最后出现“Application is healthy; post-update maintenance/monitor setup needs attention”，新应用已通过健康检查并保留运行，但后续维护或监控安装失败。先查看日志，修复后执行：

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py maintenance
cp deploy/jwb-ops.service deploy/jwb-ops.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now jwb-ops.timer
```

不要因为后置任务报错就盲目恢复旧数据库。

## 4. 新规则与数据兼容

**退款**：只支持系统已完整记录、归属当前账户的消费；按原 USD 入账额退款，不重新计算外币汇率。多次部分退款按累计比例及分币精度冲回积分和权益抵扣，不能超退。欠款归零后的盈余进入 USD 钱包。已花掉的积分被冲回时可出现负数，后续奖励先补足；开卡奖励按当前累计消费进度回落是否跌破原门槛判断冲回。旧系统没有完整来源记录的历史消费不会伪造退款入口。

**权益冲回**：仅在原消费所属权益周年周期仍有效时恢复原产品对应额度，不把已经过期的权益挪到新周期。销卡后不恢复未用权益。

**年费与到期**：旧卡的续期锚点对齐原始开卡周年的下一次未来日期，不追收升级前漏记的历年年费；今后自动记账，每期只收一次。年费可能使欠款超过可用授信。到期/冻结不会自动销卡，仍需处理已出账债务与续年费用；决定不再使用请结清后主动销卡。补换卡更新卡号、安全码和五年有效期，保留内部账户、欠款、奖励进度与历史，恢复可用状态。

**销卡**：须先结清欠款；授信额度与未用权益失效，历史交易和账单保留。以后可再次申请该卡种。历史销卡交易仍可按规则退款。

**偏好与展示**：常用币种应用到新表单，不覆盖已有草稿；默认卡、语言与通知偏好保存在账户中。系统与安全通知不受普通通知关闭影响。展示模式遮挡当前页面个人信息，并暂停资金操作与个人文件下载；账户仍然登录，展示完成后退出该模式或退出账号。ICS 是导出时的日历快照，变更账期/卡片后重新导出。

## 5. MFA 与恢复

身份验证器使用六位、30 秒验证码。界面支持手动录入设置密钥；恢复码仅显示一次，每个只能用一次。同一验证码成功使用后不能再用于下一项敏感操作，请等待下一码或使用未用过的恢复码；确保手机与服务器时间准确。

密钥加密依赖现有 `APP_SECRET`，升级时必须原样保留。不要在聊天、截图或反馈中发送设置密钥、恢复码、密码或 SMTP 授权码。

若确已失去验证器和所有恢复码，由服务器管理员核对账户所有权后，在终端恢复指定账户：

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py disable-mfa owner@example.com --confirm
```

替换成实际待恢复邮箱。该操作关闭其 MFA，删除登录挑战并撤销全部会话，用户需要重新登录和绑定。普通用户不能通过网页调用这一恢复命令。

## 6. 监控与告警

`jwb-ops.timer` 每五分钟检查应用本机心跳、SQLite、近期连续邮件失败、参考汇率新鲜度、最近自动备份、磁盘、接口连续 5xx 与独立维护心跳。不会将“监控任务自己运行成功”当作“维护任务成功”。

异常进入管理员站内通知，并按每类每小时最多一次合并发送邮件。默认发给可用管理员邮箱，可在现有 `.env` 末尾增加：

```dotenv
ADMIN_ALERT_EMAIL=owner@example.com
OPS_HEALTH_URL=http://127.0.0.1:8895/bank/api/health
OPS_DISK_MIN_MB=512
```

邮箱按实际修改；本机健康地址只允许 loopback HTTP。改 `.env` 后重启 `jwb-cloud`。无需重复填写已有 SMTP。首次启用尚无新监控/维护记录时，先运行维护和监控任务。

独立 watchdog 在应用或数据库启动失败时也会尝试邮件提醒；若 SMTP 本身失败，邮件无法送达，需看 systemd 日志，应用可用时看后台/站内提醒。机器断电、系统宕机、监控定时器未运行或网络完全断开仍需服务器外部监测，不能由同一台服务器保证发现。

## 7. 程序回退

升级切换后未通过健康检查，工具会尝试恢复旧程序和旧虚拟环境，**始终保留当前数据库**。若回退被拒绝或失败，工具明确提示并保留快照供排查。

手动回退时先保留当前日志和最新备份，再用实际输出路径：

```bash
/www/wwwroot/jwb-cloud/.venv/bin/python /www/backup/jwb-update.py --rollback /www/backup/jwb-releases/实际时间戳
```

每个快照的旧虚拟环境只能恢复一次。回退到 5.x 时，若已有启用的 MFA、退款、新卡片生命周期状态或续期年费，工具将拒绝：旧程序不能正确强制 MFA 或处理这些数据。不要绕过检查或直接覆盖旧代码。

回退检查是在暂停服务后进行的；被兼容性检查拒绝时，当前新代码和数据库仍保留，但服务/任务处于停止状态。确认当前目录仍是 6.0、无需继续回退后，可恢复当前程序：

```bash
systemctl start jwb-cloud
systemctl start jwb-backup.timer jwb-maintenance.timer jwb-ops.timer
curl -fsS http://127.0.0.1:8895/bank/api/health
```

数据库恢复属于单独的灾难恢复流程，会丢失备份时间之后的数据，必须先确认备份时间和影响；不要把程序回退与数据库覆盖混为一谈。

## 8. 浏览器自动化和验证范围

本包实际通过：75 项 Python 业务/安全/升级器测试；320、375、390、768、1024、1440 六种宽度的 DOM 原生事件检查；管理员 9 页中英文检查；退款后年度 PDF 已生成并渲染检查。DOM 测试覆盖草稿、服务中心、偏好默认值、敏感信息清理、展示模式、MFA 界面、后台操作入口等，不能代替真实浏览器排版测试。

**Playwright 配置已提供，但当前环境没有执行真实浏览器回归，也没有生成/审核视觉基线。** 请在开发机或 CI 中运行，不要将测试服务部署到公网服务器：

```bash
python3 -m venv .test-venv
.test-venv/bin/pip install -r requirements.txt
cd browser-tests
npm install
npx playwright install --with-deps chromium firefox webkit
JWB_TEST_PYTHON=../.test-venv/bin/python npm test -- --grep-invert "visual baseline"
JWB_TEST_PYTHON=../.test-venv/bin/python npm run snapshots
```

使用 Linux/macOS shell；Windows 可在 WSL 运行。测试自动启动仅监听 127.0.0.1:8896 的临时数据库服务，使用合成账户、内存邮件与固定汇率，不连线上账户。`server.py` 的测试种子接口仅在测试脚本中，正式 app 不含该接口。

首次生成截图后人工查看五类设备/浏览器的图片，确认后提交 `browser-tests/system.spec.cjs-snapshots/`；以后的 `npm test` 对照这些基线。GitHub Actions 配置在缺少基线时只运行功能测试并提示，不会假装已做视觉比较。项目未连接 GitHub 时这份配置不会自动运行。

## 提醒

本系统始终是模拟体验，退款、资金、授信、证书签名图样和印章均为演示用途，不提供真实银行服务。此次交付是经过上述本地检查的代码与部署工具；服务器安装、systemd 切换与真实设备验收需按本文在你的环境完成。
