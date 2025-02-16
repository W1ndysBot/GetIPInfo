# script/GetIPInfo/main.py

import logging
import os
import re
import sys
import aiohttp
from bs4 import BeautifulSoup

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import *
from app.switch import load_switch, save_switch

# 数据存储路径，实际开发时，请将GetIPInfo替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "GetIPInfo",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "GetIPInfo")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "GetIPInfo", status)


# 访问 https://ip.900cha.com/ 获取IP页面
async def get_ip_info(ip):
    url = f"https://ip.900cha.com/{ip}.html#/"
    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        async with session.get(url, headers=headers) as response:
            return await response.text()


# 解析IP页面提取相关信息
def parse_ip_info(html):
    soup = BeautifulSoup(html, "html.parser")
    # 找到包含地理位置信息的列表
    info_list = soup.find("ul", class_="list-unstyled mt-3")
    if info_list:
        # 提取每个列表项的文本
        info_items = [li.get_text(strip=True) for li in info_list.find_all("li")]
        return "\n".join(info_items)
    return "未找到地理位置信息"


# 群消息处理函数
async def handle_GetIPInfo_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))
        match = re.match(r"\s*(ip|IP)\s*([\w.-]+)\s*", raw_message)
        if match:
            ip = match.group(2)
            ip_info = await get_ip_info(ip)
            ip_info = parse_ip_info(ip_info)
            message = f"[CQ:reply,id={message_id}]{ip_info}"
            await send_group_msg(websocket, group_id, message)
    except Exception as e:
        logging.error(f"处理GetIPInfo群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理GetIPInfo群消息失败，错误信息：" + str(e),
        )
        return


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    post_type = msg.get("post_type", "response")  # 添加默认值
    try:
        # 处理回调事件
        if msg.get("status") == "ok":
            return

        post_type = msg.get("post_type")

        # 处理元事件
        if post_type == "meta_event":
            return

        # 处理消息事件
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                raw_message = msg.get("raw_message", "")
                if raw_message.lower().startswith(("ip", "ip ")):
                    await handle_GetIPInfo_group_message(websocket, msg)
            elif message_type == "private":
                return

        # 处理通知事件
        elif post_type == "notice":
            if msg.get("notice_type") == "group":
                return

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理GetIPInfo{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理GetIPInfo{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理GetIPInfo{error_type}事件失败，错误信息：{str(e)}",
                )
