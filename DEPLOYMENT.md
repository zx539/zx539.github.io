# 将博客部署到自己的服务器

这个项目是 **Hugo 静态博客**：Hugo 将 Markdown、模板和样式构建成 HTML、CSS、图片等文件，再由 Nginx 对外提供访问。服务器不需要 Node.js、数据库，也不需要一直运行 Hugo。

本文采用「本地构建 → SSH 上传 → Nginx 托管」的方式，以 **Ubuntu 24.04 LTS 服务器**为例。其他系统可以沿用部署思路，但软件安装命令和 Nginx 配置目录需要对应调整。

## 1. 准备服务器和域名

需要准备：

- 一台可以通过 SSH 登录的 Linux 服务器。
- 一个有 `sudo` 权限的普通账户，本文用 `deploy` 表示；如果已有这样的账户，可以直接使用。
- 主域名 `zxpage.online` 和备用入口 `www.zxpage.online`：为 `@` 添加 A 记录指向服务器公网 IPv4 地址，为 `www` 添加 CNAME 记录指向 `zxpage.online`。只有在服务器确实支持 IPv6 时才添加 AAAA 记录。
- 在云服务器安全组中放行 TCP 80（HTTP）、443（HTTPS）及实际使用的 SSH 端口。服务器本机防火墙也需要允许这些端口。

下文已使用实际域名 `zxpage.online` 和 `www.zxpage.online`；`203.0.113.10`、`deploy` 仍是示例，执行前替换为实际服务器 IP 和账户。示例假设 SSH 使用默认的 22 端口。自有服务器托管时不要使用 README 中 GitHub Pages 的 A 记录地址。

如果服务器位于中国大陆，使用域名公开提供网站访问通常需要先完成 ICP 备案，并遵守服务商的接入要求。

## 2. 本地安装 Hugo 并构建

### 安装 Hugo

在存放此仓库的开发电脑上安装 Hugo 和回归测试工具。Ubuntu/Debian 可以运行：

```bash
sudo apt update
sudo apt install -y hugo rsync openssh-client python3 nodejs
hugo version
```

其他系统的安装方式见 [Hugo 安装说明](https://gohugo.io/installation/)。本项目 GitHub Actions 固定使用已验证的 Hugo Extended 0.131.0，本地也建议安装相同版本；若软件源提供其他版本，按官方安装说明获取 0.131.0。升级 Hugo 时应同时更新 CI 版本并通过生产构建和回归测试。当前样式为普通 CSS，没有额外的 npm 安装步骤。

### 配置网站地址

项目目前在 `hugo.toml` 中配置的是：

```toml
baseURL = "https://zxpage.online/"
```

自有服务器同样直接部署在域名根目录，因此保持这个主地址即可：

```toml
baseURL = "https://zxpage.online/"
```

注意结尾的 `/`。当前 GitHub Pages 也使用根域名，不需要 `/MyBlog/` 这样的子路径。这个地址会影响资源链接、RSS 和 sitemap。

后面的构建命令显式指定相同的 `--baseURL`。如果将来更换主域名，需要同步更新配置和命令中的地址；命令行参数优先于配置文件。

### 构建正式站点

首次获取源码时，明确使用维护分支：

```bash
git clone --branch codex/sakura-template-layout https://github.com/zx539/zx539.github.io.git
cd zx539.github.io
```

已有仓库应先保存本地修改，再切换到 `codex/sakura-template-layout` 并运行 `git pull --ff-only`。不要使用仅保存构建产物的 `gh-pages` 分支作为源码。

在仓库根目录运行：

```bash
node tests/daily-scene.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
hugo --gc --minify --panicOnWarning --baseURL "https://zxpage.online/" --destination dist-server --cleanDestinationDir
test -f dist-server/index.html
```

`dist-server/` 是本次生成的部署目录，必须专用于构建输出；`--cleanDestinationDir` 会清理其中不属于本次构建的文件。该目录不要提交到 Git，建议在本地 `.git/info/exclude` 中添加一行 `dist-server/`，或将其加入项目 `.gitignore`。

这里单独生成 `dist-server/`，是因为仓库中现有的 `public/` 包含历史构建产物，可能仍引用 GitHub Pages 地址。不要直接上传已有的 `public/`，每次都重新构建。

正式构建不加 `-D`，因此标记为 `draft: true` 的文章不会发布。需要发布的文章应改为 `draft: false`；未来日期的文章默认也不会生成。

本地预览可以另开终端运行：

```bash
hugo server --baseURL "http://localhost:1313/"
```

打开终端提示的本地地址检查页面，完成后按 `Ctrl+C` 退出。

## 3. 服务器安装 Nginx

以下命令在服务器上运行。先从本地登录：

```bash
ssh deploy@203.0.113.10
```

安装服务及上传所需工具：

```bash
sudo apt update
sudo apt install -y nginx rsync
sudo systemctl enable --now nginx
```

如果使用 UFW，先允许实际的 SSH 端口，再允许网站端口：

```bash
sudo ufw allow 22/tcp
sudo ufw allow 'Nginx Full'
sudo ufw status
```

如果 SSH 不是 22 端口，先替换第一条命令中的端口。这里的命令不会主动启用原本未开启的 UFW；云平台安全组仍需单独放行。

创建发布目录，并将所有者设置为当前 SSH 登录用户：

```bash
sudo mkdir -p /var/www/myblog/releases
sudo chown -R "$(id -un):$(id -gn)" /var/www/myblog
sudo chmod 755 /var/www/myblog /var/www/myblog/releases
```

## 4. 上传第一次构建结果

回到**本地电脑的仓库根目录**，运行：

```bash
rsync -avz --chmod=D755,F644 dist-server/ deploy@203.0.113.10:/var/www/myblog/releases/initial/
```

`dist-server/` 末尾的斜杠表示上传目录内的文件。目标 `initial/` 必须是尚未对外使用的新发布目录。

在**服务器**上检查首页并设置当前版本：

```bash
test -f /var/www/myblog/releases/initial/index.html
ln -s /var/www/myblog/releases/initial /var/www/myblog/current
```

第一次部署时 `current` 应不存在。如果已经部署过，请使用后文的版本切换方式。

## 5. 配置 Nginx

在**服务器**上创建 `/etc/nginx/sites-available/myblog`：

```bash
sudo nano /etc/nginx/sites-available/myblog
```

粘贴以下配置，同时接收两个域名：

```nginx
server {
    listen 80;
    server_name zxpage.online www.zxpage.online;

    root /var/www/myblog/current;
    index index.html;
    charset utf-8;

    location / {
        try_files $uri $uri/ =404;
    }

    # Hugo 的指纹 CSS 文件名会随内容改变，可以长期缓存。
    location ~* ^/css/.+\.[a-f0-9]{32,}\.css$ {
        try_files $uri =404;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

这是普通静态网站，不需要代理到 Hugo 的 1313 端口。文章页面由 Hugo 输出为目录中的 `index.html`，因此可以直接访问 `/posts/文章名/`。

启用配置并检查：

```bash
sudo ln -s /etc/nginx/sites-available/myblog /etc/nginx/sites-enabled/myblog
sudo nginx -t
```

只有 `nginx -t` 成功后才重新加载：

```bash
sudo systemctl reload nginx
curl -I -H 'Host: zxpage.online' http://127.0.0.1/
```

应返回 `200 OK`。默认站点可以保留，Nginx 会根据域名匹配这里的 `server_name`。使用 IP 地址直接访问时可能显示默认欢迎页，要访问博客请使用域名，或按上面的方式设置 Host 请求头。

目前生成文件使用的是最终 HTTPS 地址，请继续配置证书后再做完整的浏览器检查。

## 6. 配置 HTTPS

先确认两个域名均已解析到这台服务器，公网可以通过 80 端口访问。以下示例使用 Certbot 的 Nginx 插件申请 Let's Encrypt 证书：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d zxpage.online -d www.zxpage.online --redirect
```

按提示填写邮箱并同意服务条款。Certbot 会修改 Nginx 配置，启用 HTTPS 并将 HTTP 请求重定向到 HTTPS。

检查自动续期：

```bash
sudo systemctl status certbot.timer --no-pager
sudo certbot renew --dry-run
```

正常情况下 Ubuntu 软件包会安排自动续期。若定时器未启用，应检查安装状态并启用它；证书续期使用的 HTTP 验证仍需要公网能够访问 80 端口。

完成后，在浏览器打开 `https://zxpage.online/` 和 `https://www.zxpage.online/`，检查：

- 首页、关于页、文章列表、周报和每日一景都能打开，刷新详情页面也正常。
- CSS、头像、每日一景轮播和图文详情中的图片正常显示。
- 页面下方的时钟显示时、分、秒并每秒更新；它使用访问者设备本地时区，每日一景的日期筛选使用北京时间。
- 页面中的内部链接使用当前域名根路径，不再带旧的 `/MyBlog/`。
- `https://zxpage.online/index.xml` 和 `https://zxpage.online/sitemap.xml` 可以访问。

## 7. 以后发布新文章或修改页面

每次先在本地修改源文件，例如 `content/posts/` 中的文章、`data/profile.yaml` 中的个人信息，或 `assets/css/main.css` 中的样式。

然后在**本地仓库根目录**执行下面这一组命令；它会生成新的发布目录，上传成功后再切换线上版本：

```bash
set -e

node tests/daily-scene.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
hugo --gc --minify --panicOnWarning --baseURL "https://zxpage.online/" --destination dist-server --cleanDestinationDir
test -f dist-server/index.html

release_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
rsync -avz --chmod=D755,F644 dist-server/ "deploy@203.0.113.10:/var/www/myblog/releases/$release_id/"

ssh deploy@203.0.113.10 "set -e; test -f /var/www/myblog/releases/$release_id/index.html; ln -s /var/www/myblog/releases/$release_id /var/www/myblog/current-next-$release_id; mv -Tf /var/www/myblog/current-next-$release_id /var/www/myblog/current"

curl --fail --silent --show-error --head https://zxpage.online/
```

上述脚本适合在 Bash 中执行。`set -e` 使构建或上传失败时停止，避免继续切换版本。`release_id` 自动生成，仅包含时间、数字和连字符。

每次上传到新目录，再用同一文件系统内的 `mv -Tf` 原子替换 `current` 符号链接。Nginx 不需要重启；新请求会读取新的版本。旧目录保留，便于回退。多个人发布时应串行执行，避免同时切换版本。

### 回退到上一个版本

在**服务器**上先查看当前版本和历史目录：

```bash
readlink -f /var/www/myblog/current
ls -1 /var/www/myblog/releases
```

例如要回到第一次部署的版本，执行：

```bash
set -e
test -f /var/www/myblog/releases/initial/index.html
rollback_link="/var/www/myblog/current-rollback-$$"
ln -s /var/www/myblog/releases/initial "$rollback_link"
mv -Tf "$rollback_link" /var/www/myblog/current
```

回退其他版本时，将 `initial` 替换为对应目录名。定期清理确认不再需要的历史目录以节省空间，但不要删除 `current` 指向的目录，并保留近期可用版本。

## 8. 和现有 GitHub Pages 配置的关系

仓库中的 `.github/workflows/hugo.yml` 仅在推送 `codex/sakura-template-layout` 时自动运行，手动运行也仅允许该分支发布。工作流在构建和回归测试全部通过后发布到 `gh-pages`，构建命令为：

```bash
hugo --gc --minify --cleanDestinationDir --panicOnWarning
```

因此需要注意：

- 这份工作流只部署 GitHub Pages，**不会自动更新自己的服务器**。
- 工作流直接读取 `hugo.toml` 的 `baseURL`，当前主地址为 `https://zxpage.online/`；`static/CNAME` 为 GitHub Pages 保存相同域名。自有服务器通过 Nginx 的 `server_name` 接收域名，不依赖 CNAME 文件。
- 一个域名的 DNS 应指向实际托管位置。若保留两个不同地址的站点，为各自地址分别构建；切换到自有服务器时，将 DNS 改为服务器 IP，并更新 `www` 记录。
- 完全迁移到自己的服务器后，可以在 GitHub 仓库的 Actions 页面禁用这份工作流；服务器更新按第 7 节执行。

如果以后需要「推送代码后自动部署服务器」，可以再增加 SSH 发布的 CI 工作流，并配置专用部署账户和仓库 Secrets。本文的手动部署不需要将服务器密码或私钥放进仓库。

## 9. 常见问题

### 域名打不开或 HTTPS 申请失败

检查 DNS 的 A/AAAA 记录、安全组、本机防火墙，以及 Nginx 是否运行。错误的 AAAA 记录可能导致部分客户端和证书验证访问到错误的 IPv6 地址。如果域名经过 CDN 代理，应确认它能将证书验证请求正确转发到源站。

```bash
sudo systemctl status nginx --no-pager
sudo nginx -t
sudo tail -n 50 /var/log/nginx/error.log
```

### 首页没有样式、图片 404，或者链接带着 `/MyBlog/`

检查是否用实际域名作为 `--baseURL` 重新构建，以及是否上传了最新的 `dist-server/`。不要上传仓库里已有的旧 `public/`。

### 返回 403

确认 `/var/www/myblog/current/index.html` 存在，Nginx 账户能读取文件，并能穿过整个目录路径。本文用目录 `755`、文件 `644` 的权限解决静态文件读取问题。

### 返回 404

确认请求路径确实有对应构建产物。文章未生成时，检查 `draft` 状态和文章日期。Nginx 应使用上面的 `try_files` 配置，不需要将所有请求重写到首页。

### 中文字体加载慢

`layouts/partials/head.html` 目前从 Google Fonts 加载字体。网络无法访问 Google Fonts 时会使用 CSS 中配置的备用字体；如果需要消除这项外部依赖，可以将有授权的字体文件放入 `static/fonts/`，通过本地 `@font-face` 加载并移除 Google Fonts 链接。

### 是否要把源代码全部上传到网站目录？

只上传生成后的 `dist-server/` 内容。源码、Git 历史和开发配置留在开发电脑或代码仓库，Nginx 的根目录只指向构建产物。请另外保存源码和图片等原始资料，服务器上的静态产物不能替代源代码备份。

### 能否只用服务器 IP？

可以临时用 `http://服务器IP/` 作为 `baseURL` 构建，并将 Nginx 的 `server_name` 改为这个 IP 来验证 HTTP 部署。此时跳过本文基于域名的证书步骤；正式使用建议配置域名，再按最终 HTTPS 地址重新构建。
