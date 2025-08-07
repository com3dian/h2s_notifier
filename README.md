# Holland2Stay 房源监控通知系统

> [!NOTE]
> 本仓库是 [751K/holland2stay_h2s_check](https://github.com/751K/holland2stay_h2s_check) 的一个分支。

本项目基于 [JafarAkhondali/Holland2StayNotifier](https://github.com/JafarAkhondali/Holland2StayNotifier) 进行二次开发，将原有的Telegram通知改为使用PushPlus推送通知，并增加了多项实用功能。

## 致谢
- 原项目作者: [JafarAkhondali](https://github.com/JafarAkhondali)
- 原项目贡献者: [MHMALEK](https://github.com/MHMALEK)

## 新增功能
- **PushPlus通知**: 使用PushPlus将新房源信息推送到微信等渠道
- **直接预订筛选**: 只监控可直接预订的房源，忽略需要抽签的房源
- **价格上限过滤**: 设置最高价格限制，超过指定价格的房源不会推送
- **数据库连接优化**: 优化数据库连接管理，避免重复创建连接
- **日志增强**: 同时将日志输出到文件和控制台，方便监控
- **数据管理**: 提供数据库查看和清理工具
- **统一配置**: 将所有配置项集中到 `config.json` 文件

## 安装与配置:
```bash
# 安装依赖
python -m pip install -r requirements.txt 
# 运行程序
python main.py
```

## 配置项说明
在 `config.json` 中可以设置以下参数：

```json
{
  "PUSHPLUS_TOKEN": "你的PushPlusToken", // PushPlus的Token
  "only_direct_booking": true,     // 是否只监控可直接预订的房源
  "max_price": 1000,               // 房源价格上限(欧元)
  "notifications": {
    "groups": [
      {
        "name": "监控组名称",
        "cities": ["城市ID列表"]
      }
    ]
  },
  "monitoring_settings": {         // 持续监控设置
    "enabled": false,              // 是否启用持续监控，默认为 false (单次运行)
    "timezone": "Europe/Amsterdam",  // 指定时区，例如 "Europe/Amsterdam"
    "workdays": [0, 1, 2, 3, 4],   // 工作日列表，0=周一, 6=周日
    "start_hour": 9,               // 监控开始小时 (24小时制)
    "end_hour": 17,                // 监控结束小时 (24小时制，不包含此小时)
    "interval_minutes": 5,         // 工作时间内的监控检查间隔 (分钟)
    "off_hours_interval_minutes": 30, // 非工作时间的监控检查间隔 (分钟)
    "interval_jitter_percent": 0.1 // 监控间隔的抖动百分比 (例如 0.1 表示 +/-10%)
  },
  "legacy_settings": {             // 旧版配置，可忽略或删除
    "TELEGRAM_API_KEY": "",
    "DEBUGGING_CHAT_ID": ""
  }
}
```

## 城市ID对照表
```
"24": "Amsterdam"
"320": "Arnhem"
"619": "Capelle aan den IJssel"
"26": "Delft"
"28": "Den Bosch"
"90": "Den Haag"
"110": "Diemen"
"620": "Dordrecht"
"29": "Eindhoven"
"545": "Groningen"
"616": "Haarlem"
"6099": "Helmond"
```

## 数据库管理
查看数据库内容:
```bash
python view_db.py
```

清理数据库:
```bash
python clear_db.py
```

## 定时任务

内置的持续监控功能 (`"monitoring_settings": { "enabled": true }`) 启动后，程序会根据 `timezone`, `workdays`, `start_hour`, `end_hour`, `interval_minutes`, `off_hours_interval_minutes`, 和 `interval_jitter_percent` 的设置自动调整监控频率并持续运行。在工作时间和非工作时间，程序都会执行完整的房源检查和推送逻辑。

如果选择不启用内置的持续监控功能 (`"monitoring_settings": { "enabled": false }`)，你仍然可以使用 crontab 来实现定时执行。

添加 crontab 定时任务:
```
# 每天 9 点到 17 点之间，每隔 5 分钟执行一次
*/5 9-17 * * 1-5 python /path/to/your/main.py

# 每天 17 点到 次日 9 点之间，每隔 30 分钟执行一次
*/30 0-8,17-23 * * 1-5 python /path/to/your/main.py
```

## 部署到 Azure

本节介绍如何将应用程序作为 Docker 容器部署到 Azure App Service。

### 先决条件

*   一个拥有有效订阅的 Azure 帐户。
*   已安装 [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)。
*   已安装 [Docker](https://docs.docker.com/get-docker/)。

### 1. 构建并推送 Docker 镜像

1.  **登录到 Azure:**

    ```bash
    az login
    ```

2.  **创建资源组:**

    ```bash
    az group create --name <resource-group-name> --location <location>
    ```

3.  **创建 Azure 容器注册表 (ACR):**

    ```bash
    az acr create --resource-group <resource-group-name> --name <acr-name> --sku Basic --admin-enabled true
    ```

4.  **登录到您的 ACR:**

    ```bash
    az acr login --name <acr-name>
    ```

5.  **构建 Docker 镜像:**

    ```bash
    docker build -t <acr-name>.azurecr.io/h2snotifier:latest h2snotifier/
    ```

6.  **将镜像推送到您的 ACR:**

    ```bash
    docker push <acr-name>.azurecr.io/h2snotifier:latest
    ```

### 2. 部署到 Azure App Service

1.  **创建 App Service 计划:**

    ```bash
    az appservice plan create --name <app-service-plan-name> --resource-group <resource-group-name> --is-linux
    ```

2.  **创建 Web 应用:**

    ```bash
    az webapp create --resource-group <resource-group-name> --plan <app-service-plan-name> --name <web-app-name> --deployment-container-image-name <acr-name>.azurecr.io/h2snotifier:latest
    ```

3.  **配置 Web 应用以使用容器注册表:**

    ```bash
    az webapp config container set --name <web-app-name> --resource-group <resource-group-name> --docker-custom-image-name <acr-name>.azurecr.io/h2snotifier:latest --docker-registry-server-url https://<acr-name>.azurecr.io --docker-registry-server-user <acr-username> --docker-registry-server-password <acr-password>
    ```

    您可以从 Azure 门户中您的 ACR 的“访问密钥”部分获取 ACR 用户名和密码。

4.  **启用持续部署（可选）:**

    当新镜像被推送到容器注册表时，这将自动重新部署应用程序。

    ```bash
    az webapp deployment container config --enable-cd true --name <web-app-name> --resource-group <resource-group-name>
    ```
