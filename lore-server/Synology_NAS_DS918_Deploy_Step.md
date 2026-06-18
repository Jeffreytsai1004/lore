# 在 Synology NAS DS918+ 上部署 Lore Server（Docker）

本指南介绍如何在 Synology DS918+ 上以 Docker 容器方式部署 **Lore Server**（`loreserver`），
让您的局域网内拥有一个持久化、集中式的 Lore 远程仓库。

流程参考官方 [Deploy a local Lore Server][deploy-guide] 指南，并针对 Synology DSM 环境做了适配。

## 最终效果

- 一个 `lore-server` 容器在 DS918+ 上运行，开机自启。
- 持久化存储数据保存在 `/volume1/docker/lore/data`。
- gRPC（TCP 41337）、QUIC（UDP 41337）、HTTP 健康检查（TCP 41339）端口在 NAS 上开放。

---

## 1. 了解硬件限制

DS918+ 搭载 Intel Celeron J3455（4 核，最高 8 GB 内存），**运行** `loreserver` 绰绰有余——
但**编译**容器镜像需要完整的 Rust 工具链，链接阶段内存占用可能高达数 GB。
因此：在台式机或 CI 机器上编译镜像，再传输到 NAS。

| 操作 | 在哪里执行 |
|---|---|
| `docker build` | 台式机 / 编译机器（Linux amd64） |
| `docker run` / Compose | Synology DS918+ |

---

## 2. 准备工作

### 编译机器上

- 安装了 BuildKit 的 Docker（`docker buildx`）。
- Git（用于克隆 Lore 仓库）。
- 至少 8 GB 空闲内存（Rust 编译需要）。
- 能访问 NAS（用于传输编译好的镜像）。

### Synology DS918+ 上

- **DSM 7.2 或更高版本**（低版本也可用，但 Container Manager 界面不同）。
- **Container Manager**（DSM 的 Docker 套件——从套件中心安装）。
- 已启用 SSH（**控制面板 → 终端机和 SNMP → 启用 SSH 功能**）。
- `/volume1` 上有足够的磁盘空间，建议至少预留 50 GB。
- 端口 **41337**（TCP + UDP）和 **41339**（TCP）未被其他服务占用。

---

## 3. 获取容器镜像

编译 Rust 项目对内存要求较高。以下是四种编译方式，**任选其一**即可——选完直接跳到对应步骤继续。

| 方式 | 编译在哪里 | 需要传输到 NAS | 适合场景 |
|---|---|---|---|
| [A — Linux amd64 机器](#方式-a--在-linux-amd64-机器上编译推荐) | 独立 Linux 机器 | 是（第 4 节） | 有 Linux 服务器或云主机 |
| [B — GitHub Actions](#方式-b--github-actions-免费编译推荐) | GitHub 云端 | 否（镜像仓库直拉） | **无 Linux 机器，最省心** |
| [C — DS918+ 直接编译](#方式-c--直接在-ds918-上编译) | NAS 本地 | 否 | 不想依赖外部机器 |
| [D — Windows Docker Desktop](#方式-d--windows-docker-desktop-hyper-v-后端) | 本机 Windows | 是（第 4 节） | Windows 专业版/企业版 |

---

### 方式 A — 在 Linux amd64 机器上编译（推荐）

适用于有 Linux 物理机、云主机（EC2、轻量云等）或 macOS 的用户。

#### A.1 克隆仓库

```bash
git clone https://github.com/EpicGames/lore.git
cd lore
```

#### A.2 编译镜像

```bash
docker build --platform linux/amd64 -f lore-server/Dockerfile -t lore-server .
```

> **为什么要加 `--platform linux/amd64`？** DS918+ 是 x86_64 架构。如果编译机器
> 也是 x86_64，加上这个参数也没副作用；如果是 Apple Silicon（Arm Mac），则必须加——
> `.cargo/config.toml` 中的 `linux/arm64` 目标是为 AWS Graviton3 调优的，
> 无法在 Apple Silicon 或 DS918+ 上运行。

编译耗时：现代台式机大约 10–25 分钟。

#### A.3 验证镜像

```bash
docker image ls lore-server:latest
```

#### A.4 导出镜像

```bash
docker save lore-server:latest -o lore-server.tar
```

> 继续 → [第 4 节：传输镜像到 NAS](#4-将镜像传输到-synology-nas)

---

### 方式 B — GitHub Actions 免费编译（推荐）

白嫖 GitHub 的服务器编译，NAS 直接从 GitHub Container Registry 拉取镜像。
无需任何本地 Linux 环境，只需一个 GitHub 账号。

GitHub Actions 每月免费 2000 分钟，单次编译约 15 分钟，个人使用完全够。

#### B.1 Fork 仓库并创建 Workflow

Fork [EpicGames/lore](https://github.com/EpicGames/lore) 到你的 GitHub 账号，
然后在仓库中创建 `.github/workflows/build.yml`：

```yaml
name: Build lore-server image
on:
  push:
    branches: [main]
  workflow_dispatch:  # 允许在 GitHub 网页上手动触发
env:
  REGISTRY: ghcr.io
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      # 新增步骤：把仓库名转小写存入环境变量
      - name: Convert repo name to lowercase
        id: lowercase_repo
        run: echo "REPO_LOWER=$(echo ${{ github.repository }} | tr '[:upper:]' '[:lower:'])" >> $GITHUB_ENV

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          file: lore-server/Dockerfile
          platforms: linux/amd64
          push: true
          # 使用转换后的小写仓库名
          tags: ${{ env.REGISTRY }}/${{ env.REPO_LOWER }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> 使用了 `docker/build-push-action` 内置的 GitHub Actions 缓存——第二次编译会复用
> 之前的 Rust 依赖和 target 缓存，耗时降至 3–5 分钟。

#### B.2 触发编译

提交并推送 `build.yml` 后，编译会自动开始。也可以在仓库页面的 **Actions** 标签中
手动点击 **Run workflow** 触发。

#### B.3 在 NAS 上拉取镜像

编译完成后（Actions 页面显示绿色 ✓），SSH 到 NAS：

```bash
# 登录 GitHub Container Registry（需要先创建 Personal Access Token）
echo "你的GitHub_TOKEN" | sudo docker login ghcr.io -u 你的GitHub用户名 --password-stdin

# 拉取镜像
sudo docker pull ghcr.io/你的GitHub用户名/lore:latest

# 打上本地标签（lore.yaml 里引用的名字）
sudo docker tag ghcr.io/你的GitHub用户名/lore:latest lore-server:latest
```

> 创建 GitHub Token：**GitHub → Settings → Developer settings → Personal access
> tokens (classic)** → 勾选 `read:packages` → 生成后复制。

> 直接跳到 → [第 5 节：配置 NAS](#5-配置-nas)

---

### 方式 C — 直接在 DS918+ 上编译

NAS 本地编译，省去传输步骤。缺点是慢（J3455 4 核），且链接阶段可能触发 OOM。

#### C.1 克隆仓库

```bash
cd /volume1/docker
git clone https://github.com/EpicGames/lore.git
cd lore
```

#### C.2 编译镜像

```bash
docker build --platform linux/amd64 -f lore-server/Dockerfile -t lore-server .
```

如果遇到内存不足（OOM），可以在 Container Manager 中给 Docker 增加 swap，
或者限制 Rust 并行度——但需要修改 Dockerfile 中的 `cargo build` 行，加上
`--jobs 2` 参数后再编译。

编译耗时：预计 45–90 分钟，取决于 NAS 负载。

> 直接跳到 → [第 5 节：配置 NAS](#5-配置-nas)（无需传输）

---

### 方式 D — Windows Docker Desktop（Hyper-V 后端）

如果你的 Windows 是专业版/企业版，可以不用 WSL2，改用 Hyper-V 后端运行 Docker。

#### D.1 启用 Hyper-V

**控制面板 → 程序和功能 → 启用或关闭 Windows 功能** → 勾选 **Hyper-V** → 确定 → 重启。

> CPU 必须开启虚拟化（VT-x），在 BIOS 中确认。

#### D.2 安装 Docker Desktop

从 [docker.com](https://www.docker.com/products/docker-desktop/) 下载安装。
安装时**选择 Hyper-V 后端**（而非 WSL2 backend）。

#### D.3 编译并导出

打开 PowerShell：

```powershell
git clone https://github.com/EpicGames/lore.git
cd lore
docker build --platform linux/amd64 -f lore-server/Dockerfile -t lore-server .
docker save lore-server:latest -o lore-server.tar
```

> 继续 → [第 4 节：传输镜像到 NAS](#4-将镜像传输到-synology-nas)

---

## 4. 将镜像传输到 Synology NAS

> 仅**方式 A** 和**方式 D** 需要此步骤。方式 B（GitHub Actions）直接拉取，方式 C（NAS 编译）镜像已在本地。

### 方式一 — SCP（推荐）

```bash
scp lore-server.tar your-user@your-nas-ip:/volume1/docker/
```

### 方式二 — U 盘

将 `lore-server.tar` 拷贝到 U 盘，插入 NAS，在 File Station 中将其移动到
`/volume1/docker/`。

---

## 5. 配置 NAS

SSH 登录 NAS。（也可以使用 **Container Manager → 项目**，然后跳到 5.2。）

### 5.1 创建目录结构

```bash
sudo mkdir -p /volume1/docker/lore/data
```

这是唯一的必建目录——存放不可变存储和可变存储的数据。

如果后续要使用持久化证书（步骤 5.4），还需创建：

```bash
sudo mkdir -p /volume1/docker/lore/certs
```

### 5.2 加载镜像

```bash
sudo docker load -i /volume1/docker/lore-server.tar
```

确认镜像已加载：

```bash
sudo docker image ls lore-server:latest
```

### 5.3 复制 Compose 文件

将与本指南同目录的 `lore.yaml` 放到 NAS 上：

```bash
scp lore.yaml your-user@your-nas-ip:/volume1/docker/lore/
```

### 5.4（可选）持久化 TLS 证书

默认情况下，服务器在每次启动时生成临时的自签名证书——能用，
但容器每次重启后客户端会看到不同的证书。如需持久化证书，在 NAS 上执行：

```bash
sudo openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout /volume1/docker/lore/certs/key.pem \
  -out /volume1/docker/lore/certs/cert.pem \
  -days 3650 \
  -subj "/CN=<你的NAS主机名>" \
  -addext "subjectAltName=IP:<你的NAS-IP>,DNS:<你的NAS主机名>"
```

将 `<你的NAS主机名>` 和 `<你的NAS-IP>` 替换为实际值（如
`mynas.local` 和 `192.168.1.50`）。

### 5.5（可选）创建 `local.toml` 配置覆盖

镜像中已内置 `/etc/lore/config/docker.toml`，将两个存储都指向 `/data`。
如需进一步自定义——持久化证书、存储容量限制、日志级别等——
在 NAS 上创建 `/volume1/docker/lore/local.toml`。

以下示例引用步骤 5.4 中生成的持久化证书：

```toml
[server.quic.certificate]
cert_file = "/etc/lore/certs/cert.pem"
pkey_file = "/etc/lore/certs/key.pem"
```

然后在 `lore.yaml` 的 `volumes` 部分取消对应行的注释：

```yaml
- /volume1/docker/lore/local.toml:/etc/lore/config/local.toml:ro
- /volume1/docker/lore/certs/cert.pem:/etc/lore/certs/cert.pem:ro
- /volume1/docker/lore/certs/key.pem:/etc/lore/certs/key.pem:ro
```

> **重要：** 挂载单个文件，不要挂载整个 `/etc/lore/config` 目录。
> 挂载整个目录会覆盖镜像内置的 `docker.toml`，导致服务器丢失存储路径配置。
> 官方 Docker 部署指南也是采用同样的单文件挂载方式。

---

## 6. 部署容器

### 方式 A — Container Manager 界面（DSM 7.2+）

1. 打开 **Container Manager**。
2. 进入 **项目** → **新增**。
3. 填写项目名称（如 `lore`）。
4. 设置路径为 `/volume1/docker/lore`，选择 `lore.yaml`。
5. （可选）**Web 门户**可以跳过——Lore 没有 Web 界面。
6. 点击 **下一步**，确认后点击 **完成**。

Container Manager 在后台执行 `docker compose up -d`。

### 方式 B — 命令行

```bash
cd /volume1/docker/lore
sudo docker compose -f lore.yaml up -d
```

---

## 7. 验证部署

### 7.1 检查容器是否运行

```bash
sudo docker ps --filter "name=lore-server"
```

### 7.2 查看日志

```bash
sudo docker logs lore-server
```

正常启动应看到类似以下日志：

```text
INFO  loreserver: Lore Server starting…
INFO  loreserver: HTTP health-check endpoint listening on 0.0.0.0:41339
INFO  loreserver: gRPC endpoint listening on 0.0.0.0:41337
INFO  loreserver: QUIC endpoint listening on 0.0.0.0:41337
```

### 7.3 访问健康检查端点

从局域网内任意机器执行：

```bash
curl -i http://<你的NAS-IP>:41339/health_check
```

正常返回：`HTTP/1.1 200 OK`，响应体为空。

---

## 8. 连接 Lore 客户端

在安装了 `lore` CLI 的工作站上，将远程指向 NAS：

```bash
# 远程地址格式：lore://<主机>:<端口>
lore remote add origin lore://<你的NAS-IP>:41337
```

之后即可正常执行 clone、push、pull 等操作。完整工作流参见
[Lore 快速入门][quickstart]。

> **TLS 说明：** 默认情况下服务器使用临时自签名证书，Lore CLI
> 首次连接时会提示警告——接受即可（或安装步骤 5.4 的持久化证书并在客户端信任）。

---

## 9. 日常运维

| 操作 | 命令（在 NAS 上执行） |
|---|---|
| 停止 | `sudo docker stop lore-server` |
| 启动 | `sudo docker start lore-server` |
| 重启 | `sudo docker restart lore-server` |
| 查看日志 | `sudo docker logs -f lore-server` |
| 更新镜像 | 重新编译 → `docker save` → 拷贝 → `docker load` → 重启 |
| 进入容器 | `sudo docker exec -it lore-server /bin/bash` |

---

## 故障排查

**容器启动后立刻退出。**
查看日志：`sudo docker logs lore-server`。常见原因：

- NAS 上端口 41337 已被占用（例如其他容器或 DSM 服务）。
- `/volume1/docker/lore/data` 目录对容器用户不可写。

**取消 `lore.yaml` 中挂载注释后启动失败。**
Docker 绑定挂载要求源文件必须存在。在取消注释之前，请先在 NAS 上
创建好 `local.toml`、`cert.pem` 和 `key.pem`。

**健康检查端点无法访问。**
检查 DSM 防火墙是否拦截了 41337 和 41339 端口：
**控制面板 → 安全性 → 防火墙 → 编辑规则** → 为端口 41337（TCP + UDP）
和 41339（TCP）添加允许规则。

**客户端无法连接。**

- 确认客户端能 ping 通 NAS IP。
- 确认 TCP 和 UDP 的 41337 端口均已映射（gRPC 用 TCP，QUIC 用 UDP）。
- 查看服务器日志是否有证书或绑定错误。

**Linux / macOS 编译机器上构建失败。**

- 确保 `protobuf-compiler` 可用（Dockerfile 会自动安装）。
- 增加 Docker 内存限制（最终二进制链接阶段可能超过 4 GB）。

**GitHub Actions 编译失败。**
在仓库的 **Actions** 标签中点击失败的 job 查看日志。常见原因：

- Workflow 文件 YAML 缩进有问题——检查 `.github/workflows/build.yml` 的缩进。
- `GITHUB_TOKEN` 权限不足——在仓库 **Settings → Actions → General → Workflow permissions** 中勾选 **Read and write permissions**。

**NAS 执行 `docker pull ghcr.io/...` 报 "unauthorized"。**

- 确认 GitHub Token 已勾选 `read:packages` 权限。
- 确认在 NAS 上执行了 `docker login ghcr.io`。
- Token 不要包含特殊字符导致 shell 转义问题——用 `--password-stdin` 方式登录。

**Windows Docker Desktop 安装后无法启动。**
Docker Desktop 的 Hyper-V 后端仅支持 Windows 专业版/企业版。
如果是 Windows 家庭版，请改用方案 B（GitHub Actions）或装 WSL2。

**DS918+ 上直接编译报 OOM / 被 killed。**
J3455 的 8 GB 内存在链接阶段可能不够。两个解决方向：

- 在 Container Manager 中为 Docker 增加 swap 空间。
- 修改 Dockerfile 中 `cargo build` 行，加上 `--jobs 2`（限制并行编译进程数）。

**NAS 上报 "exec format error"。**
镜像架构错误。确认编译时加了 `--platform linux/amd64`，或用
`sudo docker inspect lore-server:latest | grep Architecture` 检查镜像架构，
确认输出为 `"Architecture": "amd64"`。

[deploy-guide]: https://epicgames.github.io/lore/how-to/deploy-local-lore-server/
[quickstart]: https://epicgames.github.io/lore/tutorials/quickstart/
