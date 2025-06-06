# Holland2Stay 房源监控通知系统

本项目基于 [JafarAkhondali/Holland2StayNotifier](https://github.com/JafarAkhondali/Holland2StayNotifier) 进行二次开发，将原有的Telegram通知改为使用Server酱推送微信通知，并增加了多项实用功能。

## 新增功能
- **微信通知**: 使用Server酱将新房源信息推送到微信
- **直接预订筛选**: 只监控可直接预订的房源，忽略需要抽签的房源
- **价格上限过滤**: 设置最高价格限制，超过指定价格的房源不会推送
- **数据库连接优化**: 优化数据库连接管理，避免重复创建连接
- **日志增强**: 同时将日志输出到文件和控制台，方便监控
- **数据管理**: 提供数据库查看和清理工具
- **统一配置**: 将所有配置项集中到 `config.json` 文件

## 安装与配置:
```bash
python main.py
```

## 配置项说明
在 `config.json` 中可以设置以下参数：

```json
{
  "SERVERCHAN_SCKEY": "你的SCKEY", // Server酱的SCKEY
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
添加 crontab 定时任务:
```bash
crontab -e
# 每5分钟执行一次
*/5 * * * * cd /path/to/Holland2StayNotifier/h2snotifier/ && python main.py
```

## 致谢
- 原项目作者: [JafarAkhondali](https://github.com/JafarAkhondali)
- 原项目贡献者: [MHMALEK](https://github.com/MHMALEK)
