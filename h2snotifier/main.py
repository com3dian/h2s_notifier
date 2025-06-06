import logging
import sys
from db import create_table, sync_houses, close_connection
from scrape import scrape, house_to_msg, CITY_IDS
from serverchan import send_wechat_msg
import json

# 配置日志记录，同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("house_sync.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

SERVERCHAN_SCKEY = None


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
        logging.error(f"读取配置文件时发生错误: {str(e)}")
        return None


def main():
    try:
        logging.info("程序开始执行")
        create_table()

        config = read_config("config.json")
        if not config:
            logging.error("无法读取配置，程序终止")
            return

        global SERVERCHAN_SCKEY
        SERVERCHAN_SCKEY = config.get("SERVERCHAN_SCKEY")
        if not SERVERCHAN_SCKEY or SERVERCHAN_SCKEY == "SCT123456789abcdefg" or SERVERCHAN_SCKEY == "SCT281078TIUMc2QgVMYTeT08ReBJW31z1":  # 更新条件以包含示例值
            logging.warning("SERVERCHAN_SCKEY未设置或使用了示例/默认值，微信推送功能将不可用")
            SERVERCHAN_SCKEY = None  # 确保在这种情况下 SERVERCHAN_SCKEY 为 None

        # 从配置文件中读取是否只抓取可直接预订的房源
        only_direct_booking = config.get("only_direct_booking", True)  # 保留默认值以防万一
        logging.info(f"配置设置：只抓取可直接预订的房源: {only_direct_booking}")

        # 获取价格上限
        max_price = config.get("max_price", 1000)  # 保留默认值以防万一
        logging.info(f"配置设置：房源价格上限: {max_price} 欧元")

        total_new_houses = 0
        filtered_by_price = 0  # 记录因价格过高而被过滤的房源数量

        for gp in config["notifications"]["groups"]:
            logging.info(f"处理监控组: {gp['name']}")
            cities = gp["cities"]
            logging.info(f"开始爬取城市: {', '.join([f'{city}({CITY_IDS.get(city, '未知')})' for city in cities])}")

            # 传递only_direct_booking参数
            houses_in_cities = scrape(cities=cities, only_direct_booking=only_direct_booking)
            if not houses_in_cities:
                logging.warning("未获取到任何房源数据，可能是爬取失败")
                continue

            logging.info(f"爬取完成，获取到 {len(houses_in_cities)} 个城市的数据")

            for city_id, houses in houses_in_cities.items():
                logging.info(f"开始处理城市 {city_id} 的 {len(houses)} 个房源")
                new_houses = sync_houses(city_id=city_id, houses=houses)
                total_new_houses += len(new_houses)

                if new_houses:
                    logging.info(f"城市 {city_id} 有 {len(new_houses)} 个新房源，准备推送通知")
                    for h in new_houses:
                        try:
                            # 检查价格是否超过上限
                            price = float(h['price_inc'].replace(',', '.'))
                            if price > max_price:
                                logging.info(f"房源 {h['url_key']} 价格为 {price} 欧元，超过上限 {max_price} 欧元，不推送")
                                filtered_by_price += 1
                                continue

                            booking_status = "可直接预订" if h.get('direct_booking') else "需要抽签"
                            title = f"新房源({booking_status}): {h['url_key']}"
                            content = house_to_msg(h)
                            logging.info(f"推送新房源通知: {h['url_key']} ({booking_status}), 价格: {price} 欧元")
                            if SERVERCHAN_SCKEY:  # 更新检查条件
                                res = send_wechat_msg(title, content, SERVERCHAN_SCKEY)
                                logging.info(f"微信推送结果: {res}")
                            else:
                                logging.warning("由于未设置有效的SERVERCHAN_SCKEY，跳过微信推送")
                        except Exception as error:
                            logging.error(f"微信推送失败: {h['url_key']}")
                            logging.error(str(error))

    except Exception as e:
        logging.error(f"程序执行过程中发生错误: {str(e)}", exc_info=True)
    finally:
        logging.info("关闭数据库连接")
        close_connection()


if __name__ == "__main__":
    main()
