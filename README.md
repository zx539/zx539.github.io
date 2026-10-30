# 风间惟花个人博客

这是一个采用樱花布局的 Hugo 个人博客，主地址为 [https://zxpage.online/](https://zxpage.online/)，同时支持 [https://www.zxpage.online/](https://www.zxpage.online/)。博客首页显示在根路径 `/`，文章、周报和每日一景分别位于 `/posts/`、`/weekly/` 和 `/photos/`。

结构按后续维护拆分：

- `data/profile.yaml`：首页个人信息、技能、项目经历。
- `content/posts/`：博客文章，新增 Markdown 文件即可。
- `content/weekly/`：每周工作、学习、健身与复盘，首页展示最近三篇。
- `content/photos/`：每日一景，每次记录的 Markdown 和照片放在同一文件夹。
- `content/about.md`：个人介绍页面。
- `layouts/partials/`：页面模块组件。
- `assets/css/main.css`：卡通动漫风格样式。
- `static/images/`：头像、favicon、背景图等图片资源。
- `data/daily.yaml`、`static/images/daily/`：尚未发布照片记录时使用的原有风景配图。
- `data/friends.yaml`、`static/images/friends/`：友情链接信息与本地头像。
- `docs/CONTENT_API.md`：所有内容模块的字段和更新方法。

## 本地预览

```bash
hugo server -D
```

生产构建与路径检查：

```bash
hugo --gc --minify --cleanDestinationDir --panicOnWarning
```

## 新增文章

```bash
hugo new posts/my-new-post.md
```

文章由 Hugo Goldmark 渲染，支持标题锚点、列表、任务列表、定义列表、表格、引用、代码高亮、图片说明和脚注。具体格式见 `docs/CONTENT_API.md`。

## 周报与每日一景

在仓库根目录运行以下命令，使用 Python 3 即可生成 Markdown 草稿：

```bash
python3 scripts/new-content.py weekly
python3 scripts/new-content.py photo evening-walk --title "傍晚散步"
python3 scripts/new-content.py post my-new-post --title "项目复盘"
```

周报按周一至周日组织，文件名使用周一的日期；同一周继续编辑同一个文件。模板包含工作成果、学习记录、健身日记、问题与复盘、下周计划。

首页右栏保留“每日一景”区域，轮播北京时间今天及此前六天的照片记录封面，每五秒切换，可手动切换、暂停和查看完整图文；七天内没有新照片时回顾最近一次记录。

填写内容、放入照片后，将 `draft` 改为 `false`，构建发布时自动收录，不需要手动修改首页清单。详细方法见 [内容维护指南](CONTENT_GUIDE.md)。

## 常用内容更新

- 修改昵称、签名、头像和项目：编辑 `data/profile.yaml`。
- 修改浏览器标签图标：替换 `static/images/favicon.png` 和 `static/images/apple-touch-icon.png`。
- 添加友情链接：将头像放进 `static/images/friends/`，再向 `data/friends.yaml` 追加对象。
- 添加每日一景：使用 `python3 scripts/new-content.py photo 名称`，将图片放入生成的文件夹并编辑 `index.md`。
- 替换背景视频：覆盖 `static/media/background.mp4`，保留 MP4/H.264 格式。

## GitHub Pages 部署

当前开发分支为 `codex/sakura-template-layout`，工作流已监听该分支；推送后会自动构建并更新 `gh-pages`。

1. 确认 `hugo.toml` 中的 `baseURL` 为 `https://zxpage.online/`，`static/CNAME` 内容为 `zxpage.online`。
2. 推送代码，在 `Actions` 页面等待 `Deploy Hugo site to Pages` 工作流完成。
3. 首次部署时，进入 `Settings -> Pages`，将 Source 设为 `Deploy from a branch`，Branch 选择 `gh-pages`，目录选择 `/ (root)`。
4. 在 `Custom domain` 中填写 `zxpage.online` 并保存，配置下表中的 DNS 记录。
5. DNS 检查和证书签发完成后勾选 `Enforce HTTPS`，检查两个域名都能访问；GitHub Pages 会将 `www.zxpage.online` 重定向到主域名。

GitHub Pages 托管使用以下记录：

| 类型 | 主机记录 | 记录值 |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `zx539.github.io` |

工作流直接读取 `hugo.toml`，不再通过命令行写死地址。更换域名时，同步更新配置、`static/CNAME`、Pages 设置和 DNS。

## 自有服务器部署

Nginx、HTTPS、发布更新和回退步骤见 [自有服务器部署指南](DEPLOYMENT.md)。自有服务器托管时，`@` 的 A 记录指向服务器公网 IP，`www` 可通过 CNAME 指向 `zxpage.online`，并为两个域名申请证书。DNS 应按实际托管位置选择配置。
