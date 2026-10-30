# Jasa · JWB 银行模拟体验

基于 Python、Flask 和 SQLite 的银行业务模拟项目，提供卡片展示、模拟账户、账单、积分和管理后台。

- 网站：[jasa.hk/bank](https://jasa.hk/bank/)
- 源码版本：6.0.1（以 `releases.json` 为准）
- 技术栈：Python 3.11 / 3.12、Flask、SQLite、原生 JavaScript、Nginx

## 功能

- 中英文卡片展示与比较、账户注册登录及会话管理。
- 模拟多币种余额、换汇、消费、还款、积分及持卡权益。
- 月度账单、PDF 报表、只读管理查询和操作审计。
- 可选二次验证、备份恢复与运行监控。

所有资金、卡片、授信及交易均用于模拟，不提供真实银行或支付服务。

## 开始使用

完整安装、环境变量、数据库初始化和 Nginx 配置见 [部署与维护指南](DEPLOYMENT.md)。

- [6.0 升级与长期运行说明](UPGRADE-6.0-长期运行与完整流程.md)
- [环境配置模板](.env.example)
- [版本记录](releases.json)
- [Python 依赖](requirements.txt)

## 源码结构

| 路径 | 用途 |
| --- | --- |
| `app.py`、`*_api.py` | 应用入口和接口 |
| `domain.py`、`suite.py`、`growth.py` | 模拟业务逻辑 |
| `static/` | 页面、样式和前端脚本 |
| `deploy/` | Nginx、服务与维护任务 |
| `tests/`、`browser-tests/` | 后端及浏览器回归测试 |
| `fonts/` | PDF 所需字体；授权见对应字体许可文件 |

## 数据与配置

仓库只保存程序和必要静态资源，不包含实际账户、交易记录、数据库、真实 `.env`、密钥或备份。运行时数据由部署者自行保管。

## 验证

安装依赖后，在项目根目录执行：

```bash
python -m unittest discover -s tests -v
```

浏览器测试配置位于 `browser-tests/`，GitHub Actions 工作流位于 `.github/workflows/`。线上邮件、域名及服务器配置仍需在实际环境验收。

## 许可

字体和第三方组件遵循各自的许可。此仓库暂未为项目自有源码指定开源许可证。
