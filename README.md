# 张迅个人博客

这是一个 Hugo 个人博客站点，主地址为 [https://zxpage.online/](https://zxpage.online/)，同时支持 [https://www.zxpage.online/](https://www.zxpage.online/)。博客首页直接显示在根路径 `/`，博客文章、周报和每日一景分别位于 `/posts/`、`/weekly/` 和 `/photos/`。

结构按后续维护拆分：

- `data/profile.yaml`：首页个人信息、技能、项目经历。
- `content/posts/`：博客文章，新增 Markdown 文件即可。
- `content/weekly/`：周报，记录工作、学习、健身与下周计划。
- `content/photos/`：每日一景，每次记录的 Markdown 和图片放在同一文件夹。
- `content/about.md`、`content/resume.md`：固定页面内容。
- `layouts/partials/`：页面模块组件。
- `assets/css/main.css`：卡通动漫风格样式。
- `static/images/`、`static/files/`：图片和简历 PDF。

## 本地预览

```bash
hugo server -D
```

## 新增文章

```bash
hugo new posts/my-new-post.md
```

## 周报与每日一景

```bash
python3 scripts/new-content.py weekly
python3 scripts/new-content.py photo evening-walk --title "傍晚散步"
python3 scripts/new-content.py post my-new-post --title "项目复盘"
```

命令生成 Markdown 草稿，填写后将 `draft` 改为 `false`，构建发布时自动收录。首页展示最近三篇周报，以及近七天的“每日一景”封面轮播。

完整目录约定、照片添加方法和发布流程见 [内容维护指南](CONTENT_GUIDE.md)。

## GitHub Pages 部署

本仓库名为 `zx539.github.io`，通过 GitHub Pages 绑定自定义域名 `zxpage.online`。`www.zxpage.online` 作为另一个访问入口，由 GitHub Pages 重定向到主域名；两个地址都不带 `/MyBlog/` 或仓库名路径。

`hugo.toml` 已配置：

```toml
baseURL = "https://zxpage.online/"
```

1. 将代码推送到本仓库的 `main` 或 `master` 分支。
2. 等待 `Deploy Hugo site to Pages` 工作流成功，生成或更新 `gh-pages` 分支。
3. 在仓库 `Settings -> Pages` 中，选择 `Deploy from a branch`。
4. 分支选择 `gh-pages`，目录选择 `/ (root)`，保存设置。
5. 在 `Custom domain` 中填写 `zxpage.online` 并保存。仓库中的 `static/CNAME` 会随 Hugo 构建复制到发布目录，保存这个域名绑定。
6. 在域名服务商处配置下面的 DNS 记录，等待 GitHub Pages 的 DNS 检查通过。
7. 等待证书签发后勾选 `Enforce HTTPS`，检查 `https://zxpage.online/` 和 `https://www.zxpage.online/` 都可以访问。

GitHub Pages 托管时使用以下 DNS 记录；`@` 表示 `zxpage.online`：

| 类型 | 主机记录 | 记录值 |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `zx539.github.io` |

`www` 的 CNAME 记录值只填主机名，不带 `https://` 或路径。若已有指向旧服务器的 A、AAAA 或 CNAME 记录，需要同步移除或修改，避免部分访问仍进入旧站点。

工作流使用 `hugo --minify`，直接读取 `hugo.toml` 中的地址。后续更换域名时，同步更新 `hugo.toml`、`static/CNAME`、Pages 设置和 DNS，再重新发布。

## 自有服务器部署

使用 Hugo 构建静态文件并通过 Nginx 托管，具体步骤见 [自有服务器部署指南](DEPLOYMENT.md)，包括域名、HTTPS、日常更新和版本回退。

自有服务器托管时，`@` 的 A 记录应指向自己的服务器公网 IP，`www` 可以通过 CNAME 指向 `zxpage.online`。Nginx 同时接收这两个域名，HTTPS 证书也需要包含两者；站点 `baseURL` 保持 `https://zxpage.online/`。

DNS 应按实际托管位置选择一套配置：上表用于 GitHub Pages，自有服务器请使用服务器 IP。
