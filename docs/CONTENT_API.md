# 博客内容接口文档

本站是 Hugo 静态网站，没有运行时 HTTP 后端接口。这里的“接口”指数据文件、Markdown 内容和静态资源之间的稳定约定。修改数据后运行 Hugo，模板会读取这些接口并生成页面。

## 1. 目录总览

| 功能 | 数据或内容 | 图片目录 | 渲染模板 |
| --- | --- | --- | --- |
| 个人信息 | `data/profile.yaml` | `static/images/` | `header.html`、`home-sidebar.html`、`hero.html`、`home-rail.html`、`footer.html` |
| 每日一景 | `content/photos/*/index.md` | 与 `index.md` 同目录 | `daily-scene.html`、`photos/list.html`、`single.html` |
| 周报 | `content/weekly/*.md` | 可选 `static/images/` | `weekly.html`、`weekly/list.html`、`single.html` |
| 空状态风景配图 | `data/daily.yaml` | `static/images/daily/` | `daily-scene.html` |
| 博客文章 | `content/posts/*.md` | `static/images/posts/` | `posts.html`、`list.html`、`single.html` |
| 项目经历 | `data/profile.yaml` 的 `projects` | 可选 `static/images/projects/` | `projects.html` |
| 技能标签 | `data/profile.yaml` 的 `skills` | 无 | `home-sidebar.html`、`skills.html` |
| 友情链接 | `data/friends.yaml` | `static/images/friends/` | `home-rail.html`、`friends.html` |
| 关于页面 | `content/about.md` | 可选 `static/images/about/` | `single.html` |
| 首页导航顺序 | `layouts/partials/home-sidebar.html` | 无 | `home-sidebar.html` |
| 浏览器图标 | 无 | `static/images/favicon.png`、`static/images/apple-touch-icon.png` | `head.html` |
| 视频背景 | 无 | `static/media/background.mp4` | `ambient-video.html` |

所有静态资源路径都相对于 `static/`。例如配置中的 `images/profile.jpg` 对应磁盘文件 `static/images/profile.jpg`。

## 2. 个人信息接口

文件：`data/profile.yaml`

### 基础字段

```yaml
name: 风间惟花
role: AI Agent 开发者 / 全栈开发 / 架构设计
tagline: 长叹息以掩涕兮，哀民生之多艰。
location: 克拉玛依市 / 东北大学秦皇岛分校
email: 202412724@stu.neuq.edu.cn
qq: "2198762717"
avatar: images/profile.jpg
hero_art: images/fox-girl-background-v2.webp
template: images/template.jpg
```

| 字段 | 必填 | 用途 | 修改方法 |
| --- | --- | --- | --- |
| `name` | 是 | 昵称、头像旁署名、页面品牌 | 直接修改字符串 |
| `role` | 是 | 职业说明 | 使用 `/` 分隔多个身份 |
| `tagline` | 是 | 首页签名和 About Me 签名 | 直接修改字符串 |
| `location` | 是 | 右栏所在地 | 直接修改字符串 |
| `email` | 是 | 左栏、右栏和底栏邮箱链接 | 填写完整邮箱，不要添加 `mailto:` |
| `qq` | 是 | 左栏、右栏和底栏 QQ | 必须加引号，防止被 YAML 当数字处理 |
| `avatar` | 是 | 导航栏、首页和浏览器图标的头像来源 | 图片放进 `static/images/` 后填写相对路径；更换后同步重新生成 favicon |
| `hero_art` | 是 | 首页狐狸娘背景 | 建议使用 16:9、宽度至少 1600px 的图片 |
| `template` | 否 | 设计参考图路径 | 不直接显示在页面中 |

### 添加技能

在 `skills` 数组末尾新增一行：

```yaml
skills:
  - Python
  - Rust
```

左栏只显示前 9 项，完整技能组件会显示所有项目。调整顺序时直接移动数组行。

### 添加首页关注方向

在 `highlights` 数组中添加内容：

```yaml
highlights:
  - AI Agent 开发
  - 新的研究方向
```

首页封面底部显示前 4 项。

### 添加项目经历

在 `projects` 数组末尾追加完整对象：

```yaml
projects:
  - title: 项目名称
    period: 2026.07 - 至今
    role: 负责人 / 全栈开发
    summary: 一句话说明项目解决的问题和本人工作。
    outcomes:
      - 成果一
      - 成果二
```

字段均为必填。项目按文件中的顺序展示；要调整顺序，移动整个对象。每条成果以 `-` 开头。

### 修改教育和奖项

教育信息位于 `education`：

```yaml
education:
  school: 学校名称
  major: 专业名称
  period: 2024.09 - 至今
  courses: 课程一、课程二
```

奖项位于 `awards`，添加方法与技能相同：

```yaml
awards:
  - 新奖项名称
```

## 3. 每日一景接口

每次记录放在 `content/photos/日期-名称/`，Markdown 和图片放在同一个文件夹。新建草稿：

```bash
python3 scripts/new-content.py photo evening-walk --title "傍晚散步"
```

例如：

```text
content/photos/2026-10-30-evening-walk/
├── index.md
├── sky.jpg
└── street.jpg
```

`index.md` 格式：

```markdown
---
title: "傍晚散步"
date: "2026-10-30T00:00:00+08:00"
draft: false
summary: "下班后的一小段散步时光。"
cover: "sky.jpg"
cover_alt: "落日下的天空"
---

今天的记录。

![落日下的天空](sky.jpg)
![街边的树](street.jpg)
```

| 字段 | 用途 |
| --- | --- |
| `title` | 列表和详情标题 |
| `date` | 记录所属日期，用于排序和近七天筛选 |
| `draft` | `true` 时不发布，生成命令默认创建草稿 |
| `summary` | 首页和归档摘要 |
| `cover` | 同文件夹中的封面文件名，留空使用按文件名排序的第一张图片 |
| `cover_alt` | 封面替代文本，留空使用标题 |

首页右栏按北京时间展示今天及此前六天的封面，五秒轮播，支持前后切换和暂停。七天内没有新照片时展示最近一次；每分钟重新检查日期，跨天无需重新构建。归档 `/photos/` 保留全部已发布记录。

照片需要在正文中用 Markdown 引用才会显示在详情中。渲染模板先查找同文件夹的图片资源，再兼容原有 `static/` 路径；原有博客的图片写法保持可用。

未发布任何带封面的照片记录时，保留 `data/daily.yaml` 中的 `image`、`alt`、`caption` 作为空状态配图，`label` 为旧版字段，不参与轮播日期判断。原有配图仍位于 `static/images/daily/`，与封面 `profile.yaml` 的 `hero_art` 继续解耦。

## 4. 博客文章接口

文章目录：`content/posts/`

新建文章：

```bash
hugo new posts/my-new-post.md
```

文章格式：

```markdown
---
title: "文章标题"
date: 2026-07-13
tags: ["AI Agent", "Hugo"]
summary: "显示在首页文章卡片中的摘要。"
draft: false
---

这里开始写正文。

## 二级标题

正文支持列表、表格、引用、代码块、图片和链接。
```

| 字段 | 必填 | 用途 |
| --- | --- | --- |
| `title` | 是 | 文章标题 |
| `date` | 是 | 排序和显示日期，格式为 `YYYY-MM-DD` |
| `tags` | 建议 | 标签数组 |
| `summary` | 是 | 首页和列表页摘要 |
| `draft` | 否 | `true` 时生产构建不会发布 |

首页文章按日期倒序显示前 3 篇。全部文章位于 `/posts/`。

### Markdown 渲染能力

Goldmark 已启用标题 ID、表格、任务列表、定义列表、脚注、删除线、链接识别和排版替换。正文样式覆盖：

- `h2` 到 `h6` 标题与标题锚点；
- 普通、嵌套、有序和任务列表；
- 引用、行内代码、代码高亮和复制按钮；
- 横向溢出表格及细滚动条；
- 图片、说明文字、脚注、分隔线和键帽。

列表项中包含段落时，模板会压缩段落间距；任务列表会隐藏普通花瓣标记，避免重复占位。Markdown 组件使用 `6px` 或 `8px` 圆角，不受全站 `--corner: 2px` 限制。

### 在文章中添加图片

1. 图片放入 `static/images/posts/`。
2. Markdown 中引用：

```markdown
![图片说明](/images/posts/example.jpg "可选图片标题")
```

本站部署在用户主页根路径，Hugo 渲染模板会根据 `baseURL` 自动生成 `/images/...` 路径。

## 5. 友情链接接口

文件：`data/friends.yaml`

每个链接包含 4 个必填字段和 1 个可选头像字段：

```yaml
- name: 站点名称
  url: https://example.com/
  avatar: images/friends/example.webp
  description: 站点简介。
  tag: Blog
```

添加步骤：

1. 在文件末尾追加上述对象。
2. 好友头像放入 `static/images/friends/`，`avatar` 填写不含 `static/` 的相对路径；未填写时显示名称首字。
3. `url` 必须包含 `https://`。
4. `tag` 建议使用 `Blog`、`Code`、`Site` 或 `Campus`。
5. 首页右栏按 YAML 顺序展示。

建议将头像转换为 `96x96 WebP`，页面显示时固定裁剪为圆形。头像加载失败或未填写时，模板显示名称首字作为占位，不会破坏列表布局。

点击时会立即播放 360ms 反馈动画，并按浏览器原生方式在新标签页打开；`Ctrl/Cmd + 点击` 等组合操作也保持原生行为。

## 6. 导航与首页顺序接口

左侧导航文件：`layouts/partials/home-sidebar.html`

中间内容顺序文件：`layouts/index.html`

当前顺序：

```text
左栏个人导航 | 中栏：封面 -> 最近文章 -> 项目经历 -> 最近周报 | 右栏：每日一景 -> About Me -> 友情链接
```

中栏每个模块对应一个 partial：

```go-html-template
{{ partial "hero.html" . }}
{{ partial "posts.html" . }}
{{ partial "projects.html" . }}
{{ partial "weekly.html" . }}
```

调整模块顺序时移动整行，同时更新 `posts.html`、`projects.html` 标题前的章节编号。左栏锚点必须与模块的 `id` 一致：`#posts`、`#projects`、`#friends`、`#about`、`#weekly`、`#daily-scene`。

## 7. 页面样式接口

主样式文件：`assets/css/main.css`

常用变量位于文件顶部：

```css
:root {
  --paper: #fffafd;
  --canvas: #fff0f6;
  --sakura: #ff7eb6;
  --vermilion: #c93676;
  --line: #4c2944;
  --corner: 2px;
}
```

修改颜色优先调整变量，不要逐个替换组件颜色。全站普通方框使用 `--corner`；Markdown 阅读组件单独使用 `--markdown-radius` 和 `--markdown-radius-small`。首页模板样式位于 `/* Sakura dashboard home */` 注释之后。

首页遮罩动画由 `layouts/partials/site-intro.html` 提供，对应样式名称为 `.sakura-intro`。全页和封面樱花数量分别在 `layouts/index.html` 与 `layouts/partials/hero.html` 的 `seq` 数值中调整。动画必须同步保留 `prefers-reduced-motion` 规则。

视频背景位于 `static/media/background.mp4`，模板为 `layouts/partials/ambient-video.html`。首页自动播放；文章和其他内页默认只加载静态 poster，用户点击播放按钮后才加载视频，以减少滚动卡顿。替换时保持文件名不变；建议使用 H.264 编码、MP4 容器、无音轨或静音内容，文件尽量控制在 5MB 内。页面工具位于 `layouts/partials/site-tools.html`，包含阅读进度、背景播放控制、返回顶部、本地时间和代码复制；滚动更新通过 `requestAnimationFrame` 合并。页面下方时钟按访问者设备本地时区显示 24 小时制 `HH:mm:ss`，每秒更新，标签页恢复可见时立即校准。

## 8. 本地验证接口

开发预览：

```bash
hugo server -D
```

生产构建：

```bash
hugo --gc --minify --cleanDestinationDir --panicOnWarning
```

回归测试（需要 Node.js、Python 3 和 Hugo；缺少 Hugo 时封面测试会跳过）：

```bash
node tests/daily-scene.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

常见问题：

- 图片不显示：每日一景的图片应放在 `index.md` 同目录；其他静态图片放在 `static/`，配置路径不要写 `static/` 前缀。
- GitHub Pages 路径错误：确认 `baseURL` 为 `https://zxpage.online/`，`static/CNAME` 与 Pages 设置均使用 `zxpage.online`；内部链接和模板图片应使用 `relURL`，Markdown 图片由渲染模板处理。
- 新文章不显示：检查 `draft` 是否为 `true`，日期是否有效，文件是否在 `content/posts/`。
- YAML 构建失败：检查缩进；数组项使用两个空格缩进并以 `-` 开头。

## 9. GitHub Pages 发布接口

工作流：`.github/workflows/hugo.yml`

发布流程：

1. 提交并推送源码分支 `codex/sakura-template-layout`。工作流仅允许此分支发布，手动运行也需选择它。
2. GitHub Actions 执行 Hugo 生产构建及回归测试；任一步失败都会停止发布。
3. 构建结果发布到 `gh-pages` 分支。
4. GitHub `Settings -> Pages` 保持 `Deploy from a branch`、`gh-pages`、`/ (root)`。
5. 配置自定义域名 `zxpage.online`、DNS 和 HTTPS，等待部署完成后访问 `https://zxpage.online/` 或 `https://www.zxpage.online/`。DNS 记录见 README。

不要手工修改 `public/`，它是构建产物并已被 `.gitignore` 忽略。

## 10. 周报接口

周报放在 `content/weekly/`，按周一日期命名，新建命令为：

```bash
python3 scripts/new-content.py weekly
python3 scripts/new-content.py weekly --date 2026-10-30
```

第二条命令生成 `content/weekly/2026-10-26.md`，标题涵盖周一至周日。同一周只创建一次，重复执行保留原文。模板包含工作成果、学习记录、健身日记、问题与复盘、下周计划，可以按日期补写学习和运动内容。

`title`、`date`、`summary`、`draft` 字段与博客含义一致。正式发布前将 `draft` 改为 `false`；Hugo 构建后会自动生成 `/weekly/` 列表和首页最近三篇。较长周报沿用现有阅读布局与文章目录，文章之间可以前后切换。

完整操作说明见 [内容维护指南](../CONTENT_GUIDE.md)。自动收录发生在构建时，新增内容仍需发布；命令不包含定时生成或自动推送。
