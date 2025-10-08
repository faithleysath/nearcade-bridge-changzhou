# Nearcade Bridge Changzhou (with NapCat)

这是一个集成了 QQ 机器人 ([NapCat](https://github.com/NapNeko/NapCat-Docker)) 的完整解决方案，用于将常州地区音游机厅人数信息从 QQ 群消息同步到 [Nearcade](https://nearcade.phizone.cn/) 网站。

## 架构

本项目使用 Docker Compose 同时运行两个服务：

1.  `napcat`: 一个功能强大的 QQ 机器人客户端，负责登录 QQ 账号并接收消息。
2.  `nearcade-bridge`: 我们编写的桥接服务，它从 `napcat` 接收 WebSocket 消息，提取机厅人数信息，并将其上传到 Nearcade API。

`napcat` 服务通过反向 WebSocket 将所有收到的消息推送到 `nearcade-bridge` 服务进行处理。

## 功能

- **一体化部署**: 使用 Docker Compose 一键启动 QQ 机器人和数据处理服务。
- **持久化登录**: QQ 账号的登录状态会保存在本地卷中，重启后无需反复扫码。
- **实时监听与处理**: `napcat` 实时接收消息，`nearcade-bridge` 实时处理并上传。
- **配置简单**: 核心配置集中在 `.env` 和 `constant.py` 文件中。

## 安装与配置

### 1. 前提条件

-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### 2. 克隆仓库

```bash
git clone https://github.com/faithleysath/nearcade-bridge-changzhou.git
cd nearcade-bridge-changzhou
```

### 3. 创建并配置 .env 文件

在项目根目录下创建一个名为 `.env` 的文件，并填入你的 Nearcade API 密钥。

```.env
# .env
API_KEY=你的API密钥

# 可选: 设置运行 NapCat 容器的用户和组 ID，避免文件权限问题
# 在 Linux/macOS 下，可以使用 `id -u` 和 `id -g` 命令获取
# NAPCAT_UID=1000
# NAPCAT_GID=1000
```

### 4. (可选) 修改常量

如果你需要监听不同的 QQ 群、QQ 号或者修改机厅信息，请直接编辑 `constant.py` 文件。本项目中的 `napcat_config/onebot11.json` 已预先配置为将消息转发给 `nearcade-bridge` 服务，通常无需修改。

## 运行服务

1.  **启动服务**

    在项目根目录下，运行以下命令来启动整个服务栈：

    ```bash
    docker-compose up -d
    ```

    Docker Compose 将会自动构建 `nearcade-bridge` 镜像，拉取 `napcat` 镜像，并以后台模式启动两个容器。

2.  **登录 QQ**

    服务启动后，在浏览器中打开 `http://<你的服务器IP>:6099`。你将看到 NapCat 的 WebUI 界面，按照提示扫码登录你的 QQ 机器人账号。

3.  **查看日志**

    你可以使用以下命令分别查看两个服务的实时日志：

    ```bash
    # 查看桥接服务的日志
    docker-compose logs -f nearcade-bridge

    # 查看 NapCat 机器人的日志
    docker-compose logs -f napcat
    ```

4.  **停止服务**

    若要停止并移除所有容器，请运行：

    ```bash
    docker-compose down
    ```

## 二次开发：适配其他城市

如果你希望将此项目用于常州以外的其他城市，主要需要修改 `src/constant.py` 文件中的配置。

### 1. 修改机厅信息

核心是更新 `arcade_maps` 字典。你需要为你的城市的每个机厅添加一个条目。

```python
# src/constant.py

arcade_maps = {
    "你的机厅简称1": {
        "path": "从Nearcade网站上找到的路径",
        "gameid": 从Nearcade网站上找到的游戏ID
    },
    "你的机厅简称2": {
        "path": "...",
        "gameid": ...
    },
    # ...
}
```

-   **机厅简称**: 一个简短易记的中文名，机器人将通过这个名字从QQ消息中识别机厅。
-   **`path`**: 机厅在 Nearcade 网站上的唯一路径。通常可以在机厅页面的 URL 中找到，格式类似于 `bemanicn/xxxx`，例如可以从[https://nearcade.phizone.cn/shops/bemanicn/4246](https://nearcade.phizone.cn/shops/bemanicn/4246)中提取`bemanicn/4246`。
-   **`gameid`**: 你要更新人数的游戏在该机厅的唯一 ID。 你可以在[获取店铺详情](https://nearcade.apifox.cn/350651823e0)页面，点击`调试`按钮，查看返回的 JSON 数据中对应游戏的 `gameid`。如果有多个，建议默认用`titleId`最小，`gameId`最小的那个。

`arcade_names` 列表会自动根据 `arcade_maps` 生成，无需手动修改。

### 2. 修改监听的 QQ 群和用户

同样在 `src/constant.py` 文件中，你需要更新以下两个变量：

```python
# src/constant.py

# 你要监听的QQ群号
listen_qq_group = 123456789
# 发送人数信息的QQ号 (通常那个群里的改卡机器人)
listen_qq_id = 987654321
```

-   `listen_qq_group`: 设置为你的机器人所在的，用来播报人数的 QQ 群号。
-   `listen_qq_id`: 设置为播报人数消息的 QQ 用户号。只有来自这个 QQ 号的消息才会被处理，以避免响应无关消息。

### 3. (可选) 修改消息提取逻辑

本项目默认的消息提取逻辑位于 `src/extract.py` 文件中，它依赖一个正则表达式来匹配 `机厅名` 和 `人数`。

当前的正则表达式假定消息格式为：`[机厅名]...[数字]人`。

示例：
```
...
宁天 当前 0 人
[上次更新于1小时20分前]
万乐 当前 2 人
[上次更新于1小时01分前]
...
```
```
收到！万乐现在有2人
```
```
人数没有变化哦，中超还是2个人
```

如果你的 QQ 群播报格式不同（例如，使用 `：` 分隔，或者没有 `人` 字），你可能需要修改 `src/extract.py` 文件中的 `pattern` 变量。

```python
# src/extract.py

# ...
    # 默认格式: (机厅名).*?(数字)个?人
    pattern = re.compile(f"({keyword_part}).*?(\d+)\s*个?人")
# ...
```

你需要根据你的实际消息格式，调整这个正则表达式以确保能正确提取信息。

完成以上修改后，重新构建并启动 Docker 容器即可让机器人为你所在的城市服务。

```bash
docker-compose up -d --build
```

## 文件结构

-   `Dockerfile`: 用于构建 `nearcade-bridge` 服务的镜像。
-   `docker-compose.yml`: 定义和编排 `nearcade-bridge` 和 `napcat` 两个服务。
-   `.env` (需手动创建): 存放敏感配置，如 API 密钥。
-   `src/`: 存放所有 Python 源代码。
    -   `websocket_server.py`: WebSocket 服务器主程序。
    -   `extract.py`: 提取机厅和人数信息。
    -   `upload.py`: 上传数据到 Nearcade API。
    -   `cache.py`: 内存缓存功能。
    -   `constant.py`: 存放常量和配置。
-   `napcat_config/`: 存放 NapCat 的配置文件。
    -   `onebot11.json`: 配置 NapCat 将消息转发到 `nearcade-bridge`。
-   `qq_data/` (自动生成): 用于持久化存储 QQ 登录信息。
-   `requirements.txt`: Python 依赖项列表。
