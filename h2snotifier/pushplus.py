import requests
import logging


def send_pushplus_msg(token, title, content, template='html', topic='', channel='', webhook=''):
    """
    发送 PushPlus 消息。
    :param token: PushPlus 的 token。
    :param title: 消息标题。
    :param content: 消息内容，支持 HTML。
    :param template: 内容模板，默认为 'html'。可选值: 'html', 'txt', 'json', 'markdown'。
    :param topic: 群组编码，不填仅发送给自己。
    :param channel: 发送渠道，默认为空。可选值: 'wechat', 'webhook', 'cp', 'mail', 'sms'。
    :param webhook: webhook编码，仅在channel='webhook'时有效。
    :return: PushPlus API 的响应。
    """
    if not token:
        logging.warning("PushPlus Token 未提供，跳过推送")
        return None

    url = "http://www.pushplus.plus/send"
    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": template,
        "topic": topic,
        "channel": channel,
        "webhook": webhook
    }
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # 如果请求失败 (状态码 4xx 或 5xx), 则抛出 HTTPError 异常
        logging.info(f"PushPlus 消息发送成功: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"发送 PushPlus 消息失败: {e}")
        return None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    # 从环境变量或配置文件中获取你的 PUSHPLUS_TOKEN 进行测试
    test_token = "你的PushPlusToken"  # 请替换为你的真实 Token 进行测试
    if test_token == "你的PushPlusToken":
        logging.warning("请替换 test_token 为你的真实 PushPlus Token 来进行测试")
    else:
        test_title = "测试 PushPlus 消息"
        test_content = "<h1>这是一条测试消息</h1><p>来自 Holland2StayNotifier 项目。</p>"
        send_pushplus_msg(test_token, test_title, test_content)
