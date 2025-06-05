import os
import sys
import time
import logging
import schedule
import datetime
import pytz
import subprocess
import random
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# 项目根目录
PROJECT_DIR = Path(__file__).parent.absolute()

# 荷兰时区
NETHERLANDS_TZ = pytz.timezone('Europe/Amsterdam')


def is_workday():
    """检查当前是否为工作日（周一至周五）"""
    now = datetime.datetime.now(NETHERLANDS_TZ)
    return now.weekday() < 5  # 0-4 是周一至周五


def is_working_hours():
    """检查当前是否为工作时间（9:00-18:00）"""
    now = datetime.datetime.now(NETHERLANDS_TZ)
    return 9 <= now.hour < 18


def should_execute():
    """决定是否执行查询任务"""
    return is_workday() and is_working_hours()


def run_query():
    """执行查询任务"""
    if not should_execute():
        logging.info("当前不在荷兰工作时间，跳过查询")
        return

    try:
        logging.info("开始执行查询任务...")
        # 使用subprocess调用main.py
        result = subprocess.run(
            [sys.executable, os.path.join(PROJECT_DIR, "main.py")],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logging.info("查询任务执行成功")
        else:
            logging.error(f"查询任务执行失败，返回码: {result.returncode}")
            logging.error(f"错误输出: {result.stderr}")

    except Exception as e:
        logging.error(f"执行查询任务时出现异常: {str(e)}")


def schedule_queries():
    """安排每小时执行45次查询的时间表，即每80秒查询一次"""
    # 清除所有现有的任务
    schedule.clear()

    # 基本间隔：每80秒
    interval_seconds = 80

    # 为每个任务添加一些随机偏移，避免完全均匀分布
    for i in range(45):
        # 计算延迟时间，添加±10秒的随机偏移
        offset = random.randint(-10, 10)
        delay = i * interval_seconds + offset

        # 确保延迟不为负数且不超过3600秒
        delay = max(0, min(delay, 3600 - interval_seconds))

        # 对于schedule库，每小时任务的时间格式必须是"MM:SS"
        minutes = (delay // 60) % 60
        seconds = delay % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        # 添加任务到队列
        schedule.every().hour.at(time_str).do(run_query)

    logging.info(f"已安排每小时执行45次查询的任务")


def main():
    """主函数"""
    logging.info("房源查询调度器启动")

    # 安排查询任务
    schedule_queries()

    # 立即执行一次，以确认系统正常工作
    run_query()

    # 主循环
    try:
        while True:
            # 每次循环检查和运行到期的任务
            schedule.run_pending()
            # 休眠1秒，避免CPU占用过高
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("调度器被用户中断")
    except Exception as e:
        logging.error(f"调度器遇到错误: {str(e)}")
    finally:
        logging.info("调度器已关闭")


if __name__ == "__main__":
    main()
