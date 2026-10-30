# 风间惟花个人博客

这是一个采用樱花布局的 Hugo 个人博客，主地址为 [https://zxpage.online/](https://zxpage.online/)，同时支持 [https://www.zxpage.online/](https://www.zxpage.online/)。博客首页显示在根路径 `/`，文章、周报和每日一景分别位于 `/posts/`、`/weekly/` 和 `/photos/`。

## 首页功能

- 中栏依次展示个人封面、最近文章、项目经历、所获奖项和最近周报。
- 左栏提供导航与技能标签，点击“奖项”可直接跳转到奖项卡片。
- 右栏展示每日一景、个人简介和友情链接。
- 页面适配手机和桌面；下方时钟显示本地时、分、秒，每秒更新。

## 内容目录

结构按后续维护拆分：

- `data/profile.yaml`：首页个人信息、技能、项目经历和所获奖项。
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

安装 Hugo Extended 0.131.0、Python 3 和 Node.js（运行回归测试用），在源码分支工作：

```bash
git clone --branch codex/sakura-template-layout https://gitcode.com/2403_88363745/my-blog.git
cd my-blog
```

```bash
hugo server -D
```

打开 `http://localhost:1313/`；`-D` 会包含草稿。页面下方时钟按访问者设备的本地时区显示 `HH:mm:ss`，每秒更新。

生产构建与路径检查：

```bash
hugo --gc --minify --cleanDestinationDir --panicOnWarning
```

提交前运行回归测试（Python 测试中的封面验证需要 Hugo）：

```bash
node tests/daily-scene.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

测试覆盖北京时间的七天照片窗口、跨年周报生成、重复文件保护和特殊文件名的封面查找。

## 新增文章

```bash
hugo new posts/my-new-post.md
```

文章由 Hugo Goldmark 渲染，支持标题锚点、列表、任务列表、定义列表、表格、引用、代码高亮、图片说明和脚注。具体格式见 `docs/CONTENT_API.md`。

## 所获奖项

编辑 `data/profile.yaml` 中的 `awards` 列表，每行填写一项奖项：

```yaml
awards:
  - 2026 赛事名称 全国二等奖
  - 2025 另一赛事名称 省级一等奖
```

奖项按配置顺序展示，相同文本只显示一次；列表为空或未配置时显示“奖项记录整理中”。修改后重新构建发布即可，无需修改模板。

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

- 修改昵称、签名、头像、项目和奖项：编辑 `data/profile.yaml`；奖项填写在 `awards` 列表中，首页项目经历后自动展示。
- 修改浏览器标签图标：替换 `static/images/favicon.png` 和 `static/images/apple-touch-icon.png`。
- 添加友情链接：将头像放进 `static/images/friends/`，再向 `data/friends.yaml` 追加对象。
- 添加每日一景：使用 `python3 scripts/new-content.py photo 名称`，将图片放入生成的文件夹并编辑 `index.md`。
- 替换背景视频：覆盖 `static/media/background.mp4`，保留 MP4/H.264 格式。

## 服务器部署

按 [服务器部署指南](DEPLOYMENT.md) 操作：在 Ubuntu 服务器上拉取代码，用 Hugo 构建，再由 Nginx 托管并配置 HTTPS。以后运行 `git pull --ff-only`、重新构建并同步网站文件即可更新。

主域名为 `zxpage.online`，同时支持 `www.zxpage.online`，网站显示在域名根路径 `/`。

已按指南完成首次部署后，在服务器运行以下命令更新网站：

```bash
set -e
cd ~/my-blog
git pull --ff-only
hugo --gc --minify --panicOnWarning --destination dist-server --cleanDestinationDir
test -f dist-server/index.html
sudo rsync -av --delete --chmod=D755,F644 dist-server/ /var/www/myblog/html/
```

`/var/www/myblog/html/` 应是专用网站目录，`--delete` 会清理其中过期的文件。更新静态文件无需重启 Nginx。
