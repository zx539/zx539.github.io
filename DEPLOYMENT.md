# 服务器部署

以下命令全部在 Ubuntu 服务器上执行：拉取代码 → Hugo 构建 → Nginx 托管。

## 1. 域名与端口

- `zxpage.online`：`@` 的 A 记录指向服务器公网 IP。
- `www.zxpage.online`：CNAME 记录指向 `zxpage.online`。
- 云服务器安全组放行 TCP 80、443，保留实际使用的 SSH 端口；启用了系统防火墙时也需放行。

## 2. 安装工具并拉取代码

```bash
sudo apt update
sudo apt install -y git hugo nginx rsync certbot python3-certbot-nginx
sudo systemctl enable --now nginx
hugo version
```

项目已验证 Hugo Extended 0.131.0。若系统软件源版本无法构建，按 [Hugo 安装说明](https://gohugo.io/installation/) 安装该版本。

首次拉取（私有仓库需要先配置 Git 平台的访问权限）：

```bash
git clone --branch codex/sakura-template-layout https://gitcode.com/2403_88363745/my-blog.git ~/my-blog
cd ~/my-blog
```

如果已经有 `~/my-blog`，跳过克隆，直接进入该目录。仓库地址或源码分支有变化时，替换成实际值。

## 3. 构建并发布

确认 `hugo.toml` 中为 `baseURL = "https://zxpage.online/"`，然后运行：

```bash
set -e
cd ~/my-blog
hugo --gc --minify --panicOnWarning --destination dist-server --cleanDestinationDir
test -f dist-server/index.html
sudo mkdir -p /var/www/myblog/html
sudo chmod 755 /var/www/myblog /var/www/myblog/html
sudo rsync -av --delete --chmod=D755,F644 dist-server/ /var/www/myblog/html/
```

`/var/www/myblog/html/` 专门存放生成的网站文件，`--delete` 会移除该目录中过期的文件。正式发布不加 `-D`；要发布的 Markdown 应设为 `draft: false`。

## 4. 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/myblog
```

首次部署时写入以下配置。如果之前按旧文档配置过，将网站根目录改为这里的 `/var/www/myblog/html`：

```nginx
server {
    listen 80;
    server_name zxpage.online www.zxpage.online;
    root /var/www/myblog/html;
    index index.html;
    charset utf-8;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/myblog /etc/nginx/sites-enabled/myblog
sudo nginx -t && sudo systemctl reload nginx
```

若软链接已经存在，跳过 `ln -s`。检查失败时先修复配置，再重新加载。

## 5. 启用 HTTPS

确认两个域名都已解析到服务器，公网能访问 80 端口，再执行：

```bash
sudo certbot --nginx -d zxpage.online -d www.zxpage.online --redirect
sudo certbot renew --dry-run
```

按提示完成申请，然后访问：

- https://zxpage.online/
- https://www.zxpage.online/

首页、文章、周报、每日一景的图片和样式应正常显示。

## 6. 以后更新

将修改推送到 Git 仓库后，在服务器运行：

```bash
set -e
cd ~/my-blog
git pull --ff-only
hugo --gc --minify --panicOnWarning --destination dist-server --cleanDestinationDir
test -f dist-server/index.html
sudo rsync -av --delete --chmod=D755,F644 dist-server/ /var/www/myblog/html/
```

更新静态文件无需重启 Nginx。每次拉取后都要重新构建和发布。
