import sqlite3
import os
import logging
import sys

# 配置日志记录，同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("house_sync.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def delete_database_file():
    """完全删除数据库文件"""
    try:
        if os.path.exists("houses.db"):
            os.remove("houses.db")
            logging.info("数据库文件已完全删除")
            print("✓ 数据库文件已成功删除")
            return True
        else:
            logging.info("数据库文件不存在，无需删除")
            print("! 数据库文件不存在")
            return False
    except Exception as e:
        logging.error(f"删除数据库文件时出错: {e}")
        print(f"✗ 删除数据库文件失败: {e}")
        return False


def clear_table_data():
    """清空数据库表中的数据，但保留表结构"""
    try:
        conn = sqlite3.connect("houses.db")
        cursor = conn.cursor()

        # 获取表数据数量
        cursor.execute("SELECT COUNT(*) FROM houses")
        count = cursor.fetchone()[0]

        # 清空表数据
        cursor.execute("DELETE FROM houses")
        conn.commit()

        logging.info(f"houses 表中的 {count} 条数据已清空，表结构保留")
        print(f"✓ 成功从 houses 表中删除了 {count} 条记录")

        conn.close()
        return True
    except sqlite3.Error as e:
        logging.error(f"清空表数据时出错: {e}")
        print(f"✗ 清空表数据失败: {e}")
        return False
    except Exception as e:
        logging.error(f"操作数据库时出错: {e}")
        print(f"✗ 操作数据库失败: {e}")
        return False


if __name__ == "__main__":
    print("数据库清理工具")
    print("-" * 30)
    print("请选择操作:")
    print("1. 清空表数据 (保留表结构)")
    print("2. 删除整个数据库文件")
    print("3. 取消")

    choice = input("请输入选项 (1/2/3): ")

    if choice == "1":
        clear_table_data()
    elif choice == "2":
        confirm = input("确定要删除整个数据库文件吗？这将删除所有数据！(y/n): ")
        if confirm.lower() == "y":
            delete_database_file()
        else:
            print("已取消删除操作")
    else:
        print("操作已取消")
