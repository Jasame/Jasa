# 三批综合升级：账单、权益、分析、通知、管理与演示

适用于已部署 https://jasa.hk/bank/ 并已完成上一轮管理员后台更新的网站。应用目录 `/www/wwwroot/jwb-cloud`、运行用户 `www`、服务名 `jwb-cloud` 保持不变。

本轮需要更新 Python 依赖、上传 PDF 字体并新增维护定时器。**不要只按上一轮的 9 文件清单覆盖。** 不修改 Nginx、端口、域名、SMTP 密码或 APP_SECRET，不重建账户或数据库。

## 已实现的三批功能

| 批次 | 功能 |
| --- | --- |
| 第一批 | 北京时间月度账单、账单日/还款间隔设置、已出账与未出账、部分还款、月度 PDF；权益额度/周期/券使用记录/欢迎奖励进度；三卡比较和消费偏好推荐 |
| 第二批 | 按月/商户/类别/卡片的消费分析、积分与年费估值对照、年度 PDF；站内通知、已读状态和到期提醒；管理员停用/恢复账户、撤销会话、调整模拟 USD/JR、修改注册和模拟审批规则 |
| 第三批 | 旅行换汇、餐饮权益、第一张卡三个独立演示场景；步骤回看和重置；表单草稿保留、加载占位、空状态、页面与进度动效、焦点样式及减少动态效果支持 |

## 业务规则与历史兼容

### 账单与还款

- 每个账户默认每月 **20 日** 出账、出账后 **20 天** 还款。可在“月度账单”中调整账单日 1–28、还款间隔 7–28 天。按北京时间账单日结束后结算；设置修改只影响未来结算，不修改已经生成的账单或还款日。
- 已出账待还 + 未出账 = 当前卡片欠款。USD 或 JR 还款、权益现金抵扣优先分配至最早欠款，避免跨账单重复计算。JR 不足时仅抵扣可用积分对应的金额；1 JR = 0.01 模拟 USD。
- 已出账单保存原始金额和当期明细。PDF 分开显示“出账时余额”和“下载时尚未结清金额”。页面列最近 120 份，已保存历史不因前台展示数量被删除。
- 首次升级前的既有欠款作为“升级期初欠款”接入，不补造旧月账单。之后到达第一个真实账单日才生成第一份账单。
- 无自动真实扣款、逾期利息、罚金、征信上报或最低还款贷款规则。这里只模拟账单和欠款分配。
- 年费沿用原模型：签发和升级时收取模拟年费/差额。本轮没有加入自动续年年费扣收；报告统计已经发生的费用，比较页则按标示年费做年度估算。

### 权益和分析

- 现金抵扣按当前卡种在引擎中实际支持的类别、单笔上限和年度额度执行，与旧账务一致。周期按原始开卡周年更新；变更卡种不清空本周期已经用掉的额度或券次数。服务器时钟回退也不会倒退周期来重新发放权益。
- 同行伴侣、免房、休息室或礼遇是明确标注的演示使用记录，不是真实预订、保险或兑换服务。不同卡种的演示券有一次/周期或不限次数的规则；使用需填写模拟说明，不提交真实订单。
- 消费分析从上一轮管理员后台起已经完整保存的业务中补录可确认的数据，之后持续记录。升级前缺失的交易资料不编造。年费、现金抵扣、常规积分和欢迎奖励分别统计。
- 比较页只按输入的每月模拟预算、实际积分倍率和标示年费计算常规净积分估值，不计欢迎奖励、实际报销或分笔取整影响，不承诺审批通过或报销额度用满。

### 通知、管理和隔离

- 通知为**站内通知**，不额外发送邮件。记录发卡/拒绝、消费、还款、入金、换汇、权益使用、账单生成、临近还款日、权益/欢迎奖励窗口到期等。关闭页面时由维护任务检查，活跃页面也会在读取账户时检查。
- 管理操作均需当前管理员密码、6–200 字的原因、CSRF 和幂等键。USD 单次调整最多正负 100 万，最多两位小数；JR 单次最多正负 100 万整数；调整后余额不得为负或超过 10 亿。
- USD/JR 调整写入账务、后台业务记录和审计。停用只阻止登录并撤销会话，不删除用户或资金；恢复需重新登录。不能停用自己，必须保留至少一个可用管理员。已撤销会话也不能在等待外部汇率后继续提交资金操作。
- 账单、后台历史和通知不会因为“重置模拟体验”被删掉；当前欠款会清零，旧账单当前未结清金额也变成零。
- 独立演示地址 **https://jasa.hk/bank/demo/**。其 API 只运行预设场景，不接受任意资金命令，不读取或修改账户，不保存用户/账务、不发送邮件。固定展示参考 1 USD = 7 CNY，不是真实汇率。看步骤快照不会重复扣款。它只写防滥用请求计数。
- 表单草稿仅在本页内存中保留，不保存在 localStorage；退出账户会清除。密码、邮箱换绑验证码不进入草稿。比较预算也会在退出时还原默认值。

## 1. 更新前备份

宝塔终端执行：

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py backup "/www/backup/jwb-cloud/before-suite-$(date +%Y%m%d-%H%M%S).sqlite3"
```

确认 `Verified backup saved` 与校验通过再继续。另存现有程序文件副本便于回退；不要公开 `.env`。已有父目录 ACL 和备份子目录 `www:www / 700` 保持原样。

## 2. 暂停服务和备份定时器

```bash
systemctl stop jwb-backup.timer
systemctl stop jwb-cloud
```

这是为避免更新一半的代码被新任务加载。如果以前已安装本轮维护定时器，也先暂停 `jwb-maintenance.timer`；首次安装无需执行这个额外停止命令。

## 3. 上传更新文件

解压最新版部署包，在宝塔文件管理进入 `/www/wwwroot/jwb-cloud`。

覆盖/新增下列根目录文件：

```text
app.py
domain.py
records.py
admin_api.py
suite.py
suite_api.py
reports.py
manage.py
requirements.txt
```

将包内 **`static/` 整个文件夹内容**同步覆盖到服务器现有 `static/` 中。本轮新增 `suite.js`、`suite.css`、`demo.html`、`demo.js`，也更新了主页面、主脚本、后台脚本/样式与共享字体，必须一并同步。

新增 **`fonts/` 文件夹**，里面的 `JWB-NotoSC.ttf` 约 10.6 MB，为服务端 PDF 字体，不能遗漏或上传成压缩文件。

再上传这两份新任务文件到现有 `deploy/`：

```text
deploy/jwb-maintenance.service
deploy/jwb-maintenance.timer
```

同步本说明、README、FONT-LICENSE 文件及 tests 便于维护。**保留服务器现有 `.env`、`data/`、`.venv/`、`gunicorn.conf.py`。不要在项目里面再套一层 jwb-cloud，也不要覆盖已有备份服务配置。**

## 4. 安装新增依赖，检查字体与数据库

```bash
cd /www/wwwroot/jwb-cloud
.venv/bin/pip install --no-cache-dir -r requirements.txt
chown www:www app.py domain.py records.py admin_api.py suite.py suite_api.py reports.py manage.py requirements.txt
chown -R www:www static fonts
sudo -u www .venv/bin/python -c "from reportlab.pdfbase.ttfonts import TTFont; TTFont('JWBCheck', 'fonts/JWB-NotoSC.ttf'); print('PDF font OK')"
sudo -u www .venv/bin/python manage.py maintenance
```

必须确认安装成功、输出 **`PDF font OK`**，并出现 **`Accounts processed: ...`** 后继续。依赖新增 `reportlab==4.4.9`（及其依赖）。不需要在服务器安装字体制作工具。

新增表自动创建，不运行 create-user，不删库、不换密钥。首次会补录可确认的分析事实并接入现有欠款；不会补造旧账单。

## 5. 启动应用和每小时维护任务

```bash
systemctl start jwb-cloud
systemctl status jwb-cloud --no-pager -l
```

看到 `active (running)` 后：

```bash
cd /www/wwwroot/jwb-cloud
cp deploy/jwb-maintenance.service /etc/systemd/system/jwb-maintenance.service
cp deploy/jwb-maintenance.timer /etc/systemd/system/jwb-maintenance.timer
systemctl daemon-reload
systemctl start jwb-maintenance.service
systemctl status jwb-maintenance.service --no-pager -l
```

这是一次性维护进程，结束后 `inactive (dead)` 正常，关键是 `0/SUCCESS`。检查成功后：

```bash
systemctl enable --now jwb-maintenance.timer
systemctl start jwb-backup.timer
systemctl list-timers --all jwb-maintenance.timer jwb-backup.timer --no-pager
```

维护任务每小时检查一次账单和权益，并可在关机错过后补执行；账单归属仍按准确的北京时间边界计算。活跃账户访问时也会检查，不必等到下一小时。原每日备份保持原设置，无需重复创建宝塔计划任务。

## 6. 网站验收

打开 https://jasa.hk/bank/ 按 Ctrl+F5，手机端关闭旧标签页再重新打开，检查：

1. 首页六卡扇形展示仍正常，“卡片比较与推荐”能按预算计算且最多选三卡。
2. 登录后能看到“月度账单、权益中心、消费分析、通知”。既有余额/卡片/积分保持正确，旧欠款出现在未出账中。
3. 一笔模拟消费后，欠款、积分、权益、分析和通知一致。模拟还款按欠款范围处理。
4. 月账单需到达第一个实际账单日才出现。不要改服务器时间催出账；可立即下载已有年度分析报告，或在隔离演示中体验完整流程。
5. 权益中心填写 DEMO 使用说明后记录演示券使用；冻结卡使用会被拒绝，单次券不能重复使用。
6. 在后台用户详情查看管理按钮；使用你确实需要调整的测试账户验证原因、密码和审计，避免随意调整其他访客账户。测试停用后确认不能登录，恢复后原数据仍在。
7. 打开 https://jasa.hk/bank/demo/ ，未登录也可体验预设场景；返回主账户确认数据不受影响。
8. 检查中英文、手机/平板/电脑的导航、弹窗和表格；表格在自身容器滚动。检查减少动态效果偏好。

最后再生成一次升级后备份：

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py backup-daily /www/backup/jwb-cloud --keep 14
```

## 出错时

```bash
journalctl -u jwb-cloud -n 100 --no-pager -l
journalctl -u jwb-maintenance.service -n 60 --no-pager -l
```

缺少 reportlab：检查依赖是否装进项目 `.venv`。PDF 字体找不到：检查 `fonts/JWB-NotoSC.ttf` 路径、大小及 www 读取权限。新页面空白/脚本 404：检查整个 static 是否同步，强制刷新。

若需要回退程序，先暂停应用和维护定时器，恢复旧程序副本后启动，并恢复原备份定时器。新增数据表不会自动删除。若还要回退数据，按原备份恢复说明先验证、停服并保留当前副本；恢复会回退用户操作，不要直接复制运行中的 SQLite 或混用 WAL 文件。

## 验证范围与当前边界

57 项 Python 自动化测试通过，覆盖原功能和本轮账单分桶/部分还款、跨期幂等、周年权益、查询隔离、PDF 权限、通知归属、管理员密码/原因/并发幂等/停用/恢复/会话撤销、规则修改以及预设演示不污染账户。测试使用内存邮件和固定汇率，不发真实邮件。

DOM 交互检查覆盖新用户页面、中英文、对比选择、草稿保留及退出清除、通知已读、管理员操作表单、独立演示步骤与恶意文本转义。PDF 样本已渲染检查分页、中文和表格。当前环境未提供真实浏览器预览，本轮未完成实际设备视觉验收，请按上述步骤检查。

本次没有接入真实银行、支付、酒店、航司、保险或征信服务。已有真实 SMTP 验证码服务和参考汇率服务继续沿用；演示固定汇率不会替换登录账户的参考汇率来源。
