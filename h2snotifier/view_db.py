import sqlite3
import sys

def view_table_schema(cursor, table_name):
    """显示表结构"""
    print(f"\n--- {table_name} 表结构 ---")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

def view_table_data(cursor, table_name, limit=10):
    """显示表数据"""
    print(f"\n--- {table_name} 数据 (最多 {limit} 条) ---")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()

    # 获取列名
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    header = [col[1] for col in columns]

    # 打印表头
    print("  ".join([f"{col:<15}" for col in header]))
    print("-" * (17 * len(header)))

    # 打印数据
    for row in rows:
        print("  ".join([f"{str(val):<15}" for val in row]))

    # 显示总记录数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\n总记录数: {count}")

def view_unoccupied_houses(cursor, limit=10):
    """显示未被占用的房源"""
    print(f"\n--- 当前可用房源 (最多 {limit} 条) ---")
    query = """
    SELECT url_key, city, area, price_inc, available_from, rooms, contract_type, created_at 
    FROM houses 
    WHERE occupied_at IS NULL 
    ORDER BY created_at DESC
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    # 表头
    header = ["URL Key", "城市ID", "面积", "价格", "可用日期", "房间数", "合同类型", "创建时间"]
    print("  ".join([f"{col:<15}" for col in header]))
    print("-" * (17 * len(header)))

    # 打印数据
    for row in rows:
        print("  ".join([f"{str(val):<15}" for val in row]))

    # 显示总记录数
    cursor.execute("SELECT COUNT(*) FROM houses WHERE occupied_at IS NULL")
    count = cursor.fetchone()[0]
    print(f"\n当前可用房源数: {count}")

def view_recent_occupied(cursor, limit=10):
    """显示最近被占用的房源"""
    print(f"\n--- 最近被占用的房源 (最多 {limit} 条) ---")
    query = """
    SELECT url_key, city, area, price_inc, available_from, rooms, contract_type, created_at, occupied_at 
    FROM houses 
    WHERE occupied_at IS NOT NULL 
    ORDER BY occupied_at DESC
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    # 表头
    header = ["URL Key", "城市ID", "面积", "价格", "可用日期", "房间数", "合同类型", "创建时间", "占用时间"]
    print("  ".join([f"{col:<15}" for col in header]))
    print("-" * (17 * len(header)))

    # 打印数据
    for row in rows:
        print("  ".join([f"{str(val):<15}" for val in row]))

    # 显示总记录数
    cursor.execute("SELECT COUNT(*) FROM houses WHERE occupied_at IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"\n已占用房源数: {count}")

def main():
    # 连接数据库
    try:
        conn = sqlite3.connect("houses.db")
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("数据库中没有表！")
            return

        print("数据库中的表:")
        for i, table in enumerate(tables):
            print(f"{i+1}. {table[0]}")

        # 显示表结构
        for table in tables:
            view_table_schema(cursor, table[0])

        # 显示具体数据
        for table in tables:
            view_table_data(cursor, table[0])

        # 显示特定查询
        view_unoccupied_houses(cursor)
        view_recent_occupied(cursor)

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
