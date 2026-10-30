# 参与 Jasa

感谢你帮助改进项目。先阅读 [项目首页](README.md)、[使用支持](SUPPORT.md) 和 [安全报告说明](SECURITY.md)。

## 反馈与修改

1. 在 [Issues](https://github.com/Jasame/Jasa/issues) 搜索已有反馈；普通问题使用 Bug 或功能建议模板。
2. 从最新 `main` 创建自己的功能分支。一次提交集中解决一个问题，避免混入格式重写。
3. 修改前先在独立开发环境复现问题，补充与行为相关的回归检查。
4. 发起 Pull Request，说明问题、行为变化、验证结果与部署影响。未验证的部分请写明。

## 本地检查

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

浏览器检查（需要 Node.js，并已安装 Python 依赖）：

```bash
cd browser-tests
npm install
npx playwright install --with-deps chromium firefox webkit
npm test -- --grep-invert "visual baseline"
```

截图基线未入库时只运行功能回归；新增基线需要人工审核，不要直接把未经检查的截图当作正确结果。

## 数据与内容

- 使用临时数据库和虚构账号。不要把线上数据用于 Issue、测试或截图。
- 不提交实际配置、密钥、Cookie、数据库、录音、备份及包含个人信息的日志。
- 新增教学内容、字体或第三方资源时说明来源和再分发许可。
- 数据库结构、环境变量或部署方式有变化时，同步更新文档并说明兼容与回退方式。

## 许可

本项目自有源码尚未指定开源许可证。字体及第三方组件保留各自许可；在需要再分发或授权使用前，请先与维护者明确权限。
