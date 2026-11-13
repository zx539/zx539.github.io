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

## 6. GitCode 推送后自动更新

配置完成后，推送到 GitCode 的 `codex/sakura-template-layout` 分支会自动触发：服务器拉取代码 → Hugo 构建 → 发布到 `/var/www/myblog/html/`，无需再登录服务器执行更新命令。其他分支、标签和删除分支的事件会被忽略。

### 6.1 准备服务器权限

先把本次新增的 `scripts/deploy.sh`、`scripts/gitcode-webhook.py` 和 `deploy/` 配置文件提交并推送到 GitCode，再在服务器的普通用户账号下更新仓库。以下配置使用这个账号运行服务；不要在 root 登录会话中直接照抄。

```bash
cd ~/my-blog
git pull --ff-only https://gitcode.com/2403_88363745/my-blog.git codex/sakura-template-layout
git remote get-url gitcode >/dev/null 2>&1 || git remote add gitcode https://gitcode.com/2403_88363745/my-blog.git
sudo apt install -y python3 git hugo rsync util-linux

MYBLOG_USER="$(id -un)"
MYBLOG_GROUP="$(id -gn)"
sudo mkdir -p /var/www/myblog/html
sudo chown -R "$MYBLOG_USER:$MYBLOG_GROUP" /var/www/myblog/html
sudo chmod 755 /var/www/myblog /var/www/myblog/html
sudo install -d -o "$MYBLOG_USER" -g "$MYBLOG_GROUP" -m 755 /var/log/myblog
sudo install -d -m 700 /etc/myblog
```

网站目录必须专用于此博客，发布脚本会删除里面的旧文件。服务使用普通账号发布，不需要 sudo 权限。仓库应由此账号持有，并保持工作区干净；脚本遇到本地修改或无法快进的分支会退出，不会强制覆盖。Hugo 版本要求同前文。

确认 GitCode 可免交互拉取：

```bash
GIT_TERMINAL_PROMPT=0 git fetch gitcode refs/heads/codex/sakura-template-layout
```

公开仓库可以用 HTTPS。私有仓库应为运行服务的账号配置有读取权限的 SSH 密钥，并将 `gitcode` remote 改为 SSH 地址；先手动连通、确认 GitCode 主机指纹，再启动服务。服务的环境变量中不要填写 GitCode 账号密码。

### 6.2 配置环境变量和 systemd

执行下面的完整代码块。它会先检查部署文件，任一步失败都会停止；服务文件先写入临时文件，确认成功后才安装，避免模板缺失时产生空的 systemd 服务文件：

```bash
(
set -euo pipefail
cd ~/my-blog
test -s deploy/gitcode-webhook.service.example
test -s scripts/gitcode-webhook.py
test -s scripts/deploy.sh
MYBLOG_USER="$(id -un)"
MYBLOG_GROUP="$(id -gn)"
MYBLOG_REPO="$(pwd -P)"
MYBLOG_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

sudo tee /etc/myblog/gitcode-webhook.env >/dev/null <<EOF
WEBHOOK_HOST=127.0.0.1
WEBHOOK_PORT=9001
WEBHOOK_SECRET=$MYBLOG_SECRET
REPO_DIR=$MYBLOG_REPO
DEPLOY_SCRIPT=$MYBLOG_REPO/scripts/deploy.sh
DEPLOY_LOG=/var/log/myblog/deploy.log
DEPLOY_REMOTE=gitcode
DEPLOY_BRANCH=codex/sakura-template-layout
DEPLOY_DIR=/var/www/myblog/html
EOF
sudo chmod 600 /etc/myblog/gitcode-webhook.env
unset MYBLOG_SECRET

MYBLOG_UNIT="$(mktemp)"
trap 'rm -f -- "$MYBLOG_UNIT"' EXIT
sed -e "s|User=deploy|User=$MYBLOG_USER|" \
    -e "s|Group=deploy|Group=$MYBLOG_GROUP|" \
    -e "s|/home/deploy/my-blog|$MYBLOG_REPO|g" \
    deploy/gitcode-webhook.service.example > "$MYBLOG_UNIT"
test -s "$MYBLOG_UNIT"
sudo systemctl unmask myblog-webhook.service
sudo install -m 644 "$MYBLOG_UNIT" /etc/systemd/system/myblog-webhook.service
sudo systemctl daemon-reload
sudo systemctl enable --now myblog-webhook
sudo systemctl status myblog-webhook --no-pager
curl --fail --retry 5 --retry-connrefused --retry-delay 1 http://127.0.0.1:9001/health
)
```

最后应返回 `{"ok": true}`。这是服务存活检查，不会触发构建或发布。首次安装后，可按第 6.5 节手动部署一次；完成第 6.4 节配置后，新的 GitCode 推送才会自动触发部署。新文章也必须先提交并推送到目标分支，服务器才能获取。

路径含空格时，需要为环境文件里的路径加双引号，并按实际路径调整 systemd 的 `ExecStart`。

如果旧命令报 `sed: can't read ...`，说明服务器的当前目录或分支不对，或尚未拉取包含部署文件的提交。先进入 `~/my-blog`，确认 `git branch --show-current` 为 `codex/sakura-template-layout`，再从 GitCode 拉取更新并检查模板确实存在。模板缺失时不要继续安装。

如果还报 `Unit ... is masked`，可能是旧管道在 `sed` 失败后生成了空文件，或服务被手动屏蔽。上面的 `unmask` 和 `install` 会解除屏蔽并安装有效服务文件。如果之前已经设置了 GitCode WebHook 密钥，修复时保留原环境文件，只执行从 `MYBLOG_USER`、`MYBLOG_GROUP`、`MYBLOG_REPO` 定义及 `MYBLOG_UNIT` 开始的服务安装步骤，避免重新生成密钥。

### 6.3 让 Nginx 转发 WebHook

在 Certbot 配置的 **HTTPS 站点 `server` 块**里加入下面的 `location`（与现有 `location /` 同级）：

```nginx
location = /gitcode-webhook {
    client_max_body_size 1m;
    proxy_pass http://127.0.0.1:9001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_connect_timeout 5s;
    proxy_read_timeout 20s;
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

9001 端口只监听本机，不用在安全组中开放。GitCode 通过已有的 HTTPS 443 端口访问。

### 6.4 在 GitCode 创建 WebHook

打开仓库的「项目设置 → WebHook → 新建 WebHook」：

- URL：`https://zxpage.online/gitcode-webhook`
- WebHook 密码/签名密钥：填写 `/etc/myblog/gitcode-webhook.env` 中 `WEBHOOK_SECRET=` 后面的值（可用 `sudo cat /etc/myblog/gitcode-webhook.env` 查看）。支持密码或 SHA-256 签名两种模式。
- POST 请求内容类型：`application/json`。
- 事件类型：仅勾选推送事件（Push Events），保存并激活。

GitCode 官方说明：[WebHook 配置](https://docs.gitcode.com/docs/help/home/org_project/webhook/webhook-first)。脚本校验官方的 `X-GitCode-Token` 或 `X-GitCode-Signature-256` 请求头；每个仓库使用独立密钥。

推送一次实际提交验证自动部署：

```bash
git push gitcode codex/sakura-template-layout
```

WebHook 请求返回 HTTP 202、`deployment: queued` 代表已接受任务；发布是否成功需要看部署日志。平台的测试请求只有在包含目标分支的 `ref` 时才会触发发布，其他测试请求会返回 `ignored`。

### 6.5 查看日志和手动重试

在服务器运行：

```bash
sudo journalctl -u myblog-webhook -n 50 --no-pager
tail -n 100 /var/log/myblog/deploy.log
```

部署日志出现 `deployment complete` 后，访问网站查看更新。构建失败时保留当前网站；连续推送会合并排队，正在构建时的新推送会再拉取一次最新代码。发布静态文件无需重启 Nginx。

修复 Hugo、Git 权限或其他报错后，可手动重试：

```bash
cd ~/my-blog
DEPLOY_REMOTE=gitcode bash scripts/deploy.sh
```

默认使用上面的源码分支和网站目录；可通过 `DEPLOY_BRANCH`、`DEPLOY_DIR`、`HUGO_BIN` 覆盖。修改服务环境文件或 WebHook 服务代码后，运行 `sudo systemctl restart myblog-webhook`。不要在服务器源码仓库中直接编辑内容，应在本地修改后推送到 GitCode。
