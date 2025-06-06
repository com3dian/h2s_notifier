import logging
import sys
from db import create_table, sync_houses, close_connection
from scrape import scrape, house_to_msg, CITY_IDS
from pushplus import send_pushplus_msg
import json
import time
from datetime import datetime, timezone
import pytz
import random # 导入 random 模块

# 配置日志记录，同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("house_sync.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# SERVERCHAN_SCKEY = None


def read_config(config_path="config.json"):
    try:
        logging.info(f"正在读取配置文件: {config_path}")
        with open(config_path) as f:
            config = json.load(f)
            logging.info(f"成功读取配置文件，包含 {len(config['notifications']['groups'])} 个监控组")
            return config
    except FileNotFoundError:
        logging.error(f"配置文件未找到: {config_path}")
        return None
    except json.JSONDecodeError:
        logging.error(f"配置文件格式错误: {config_path}")
        return None
    except Exception as e:
        logging.error(f"读取配置文件时发生错误: {str(e)}", exc_info=True) # 增强错误日志
        return None


def process_notifications(config, pushplus_token_to_use):
    logging.info("开始处理房源通知...")
    only_direct_booking = config.get("only_direct_booking", True)
    logging.info(f"配置设置：只抓取可直接预订的房源: {only_direct_booking}")
    max_price = config.get("max_price", 1000)
    logging.info(f"配置设置：房源价格上限: {max_price} 欧元")

    total_new_houses_cycle = 0
    filtered_by_price_cycle = 0

    for gp in config.get("notifications", {}).get("groups", []):
        logging.info(f"处理监控组: {gp.get('name', '未命名组')}")
        cities = gp.get("cities", [])
        if not cities:
            logging.warning(f"监控组 {gp.get('name', '未命名组')} 未配置城市，跳过")
            continue
        logging.info(f"开始爬取城市: {', '.join([f'{city}({CITY_IDS.get(city, '未知')})' for city in cities])}")

        houses_in_cities = scrape(cities=cities, only_direct_booking=only_direct_booking)
        if not houses_in_cities:
            logging.warning("未获取到任何房源数据，可能是爬取失败")
            continue

        logging.info(f"爬取完成，获取到 {len(houses_in_cities)} 个城市的数据")

        for city_id, houses in houses_in_cities.items():
            logging.info(f"开始处理城市 {city_id} 的 {len(houses)} 个房源")
            new_houses = sync_houses(city_id=city_id, houses=houses)
            total_new_houses_cycle += len(new_houses)

            if new_houses:
                logging.info(f"城市 {city_id} 有 {len(new_houses)} 个新房源，准备推送通知")
                for h in new_houses:
                    try:
                        price_str = h.get('price_inc', '0').replace(',', '.')
                        price = float(price_str)
                        if price > max_price:
                            logging.info(f"房源 {h.get('url_key', 'N/A')} 价格为 {price} 欧元，超过上限 {max_price} 欧元，不推送")
                            filtered_by_price_cycle += 1
                            continue

                        booking_status = "可直接预订" if h.get('direct_booking') else "需要抽签"
                        title = f"新房源({booking_status}): {h.get('url_key', 'N/A')}"
                        content = house_to_msg(h)
                        logging.info(f"推送新房源通知: {h.get('url_key', 'N/A')} ({booking_status}), 价格: {price} 欧元")
                        if pushplus_token_to_use:
                            res = send_pushplus_msg(pushplus_token_to_use, title, content) # 修正参数顺序
                            logging.info(f"PushPlus 推送结果: {res}")
                        else:
                            logging.warning("由于未设置有效的 PUSHPLUS_TOKEN，跳过推送")
                    except Exception as error:
                        logging.error(f"推送失败: {h.get('url_key', 'N/A')}", exc_info=True)
    logging.info(f"本轮处理完成：新增房源 {total_new_houses_cycle} 个，因价格过滤 {filtered_by_price_cycle} 个。")


def main():
    try:
        logging.info("程序开始执行")
        create_table()

        config = read_config("config.json")
        if not config:
            logging.error("无法读取配置，程序终止")
            return

        pushplus_token_from_config = config.get("PUSHPLUS_TOKEN") # 读取 PUSHPLUS_TOKEN
        if not pushplus_token_from_config or "你的PushPlusToken" in pushplus_token_from_config:
            logging.warning("PUSHPLUS_TOKEN 未设置或使用了示例/默认值，推送功能将不可用")
            pushplus_token_to_use = None
        else:
            pushplus_token_to_use = pushplus_token_from_config

        monitoring_settings = config.get("monitoring_settings", {})
        monitoring_enabled = monitoring_settings.get("enabled", False)

        if monitoring_enabled:
            logging.info("持续监控模式已启用")
            tz_str = monitoring_settings.get("timezone", "Europe/Amsterdam")
            try:
                monitor_tz = pytz.timezone(tz_str)
            except pytz.exceptions.UnknownTimeZoneError:
                logging.error(f"无效的时区配置: {tz_str}. 将使用 UTC.")
                monitor_tz = pytz.utc

            workdays = monitoring_settings.get("workdays", [0, 1, 2, 3, 4]) # Mon-Fri
            start_hour = monitoring_settings.get("start_hour", 9)
            end_hour = monitoring_settings.get("end_hour", 17)
            interval_minutes = monitoring_settings.get("interval_minutes", 5)
            base_interval_seconds = interval_minutes * 60
            interval_jitter_percent = monitoring_settings.get("interval_jitter_percent", 0.0)
            off_hours_interval_minutes = monitoring_settings.get("off_hours_interval_minutes", 30) # 读取非工作时间间隔
            off_hours_interval_seconds = off_hours_interval_minutes * 60

            logging.info(f"监控参数：时区={monitor_tz}, 工作日={workdays}, 时间={start_hour:02d}:00-{end_hour:02d}:00, 工作时间间隔={interval_minutes}分钟, 非工作时间间隔={off_hours_interval_minutes}分钟, 抖动={interval_jitter_percent*100}%")

            while True:
                now_local = datetime.now(monitor_tz)
                current_weekday = now_local.weekday()
                current_hour = now_local.hour

                is_work_time = current_weekday in workdays and start_hour <= current_hour < end_hour
                current_base_interval_seconds = 0
                current_interval_description = ""

                if is_work_time:
                    # logging.info(f"当前时间 {now_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')} 在监控时段内。使用工作时间间隔。") # 日志移到下方统一处理
                    current_base_interval_seconds = base_interval_seconds
                    current_interval_description = f"{interval_minutes} 分钟 (工作时间)"
                else:
                    # logging.info(f"当前时间 {now_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')} 不在监控时段内。使用非工作时间间隔。") # 日志移到下方统一处理
                    current_base_interval_seconds = off_hours_interval_seconds
                    current_interval_description = f"{off_hours_interval_minutes} 分钟 (非工作时间)"

                logging.info(f"当前时间 {now_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')} - {current_interval_description}. 开始执行检查流程...")
                process_notifications(config, pushplus_token_to_use)

                # 计算抖动和休眠时间
                jitter_range = current_base_interval_seconds * interval_jitter_percent
                random_jitter = random.uniform(-jitter_range, jitter_range)
                current_sleep_interval = current_base_interval_seconds + random_jitter
                current_sleep_interval = max(1, current_sleep_interval)

                # current_interval_minutes_display = current_base_interval_seconds / 60 # 已在 current_interval_description 中体现
                logging.info(f"等待 {current_sleep_interval:.2f} 秒 (下次检查基于 {current_interval_description}, +/- {interval_jitter_percent*100}% 抖动) 后再次检查...")
                time.sleep(current_sleep_interval)
        else:
            logging.info("单次运行模式")
            process_notifications(config, pushplus_token_to_use) # 传递 PUSHPLUS_TOKEN

    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.error(f"程序执行过程中发生错误: {str(e)}", exc_info=True)
    finally:
        logging.info("关闭数据库连接")
        close_connection()


if __name__ == "__main__":
    main()
