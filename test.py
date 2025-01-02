import requests
from bs4 import BeautifulSoup

# 访问 https://ip.900cha.com/ 获取IP页面
def get_ip_info(ip):
    url = f"https://ip.900cha.com/{ip}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    return response.text

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

if __name__ == "__main__":
    ip = "1.1.1.1"
    ip_info = get_ip_info(ip)
    ip_info = parse_ip_info(ip_info)
    print(ip_info)