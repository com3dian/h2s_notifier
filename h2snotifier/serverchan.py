import requests
import logging


# Server酱推送函数
# SCKEY 建议放在 .env 文件中，通过参数传入

def send_wechat_msg(title, content, sckey):
    """
    使用Server酱推送消息到微信
    :param title: 消息标题
    :param content: 消息内容
    :param sckey: Server酱的SCKEY
    :return: 响应结果或None
    """
    if not sckey or sckey == 'SCT123456789abcdefg':
        logging.error("Server酱推送失败: SCKEY 无效，请在 .env 文件中设置正确的 SERVERCHAN_SCKEY")
        return None

    # Server酱API地址
    url = f"https://sctapi.ftqq.com/{sckey}.send"

    # 准备请求数据
    data = {
        "title": title,
        "desp": content
    }

    try:
        # 打印请求信息用于调试
        logging.info(f"正在向 Server酱 发送请求: URL={url}, 标题={title}, 内容长度={len(content)}")

        # 发送请求
        resp = requests.post(url, data=data, timeout=15)

        # 打印响应状态
        logging.info(f"Server酱响应状态码: {resp.status_code}")

        # 检查响应状态
        if resp.status_code != 200:
            logging.error(f"Server酱返回错误: HTTP {resp.status_code}, 响应: {resp.text[:200]}")
            return None

        # 解析响应
        result = resp.json()

        # 检查API返回结果
        if result.get('code') == 0:
            logging.info("Server酱推送成功")
        else:
            logging.error(f"Server酱API返回错误: {result}")

        return result

    except requests.exceptions.RequestException as e:
        logging.error(f"Server酱请求异常: {e}")
        return None

    except ValueError as e:
        logging.error(f"Server酱响应解析失败: {e}")
        return None

    except Exception as e:
        logging.error(f"Server酱推送未知错误: {e}")
        return None
