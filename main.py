import os
import random
import time

from loguru import logger
from playwright.sync_api import sync_playwright
from tabulate import tabulate

# 获取以逗号分隔的多个用户名和密码
USERNAME = os.environ.get("USERNAME").split(",")
PASSWORD = os.environ.get("PASSWORD").split(",")

HOME_URL = "https://linux.do/"

class LinuxDoBrowser:
    def __init__(self) -> None:
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True, timeout=30000)
        self.context = self.browser.new_context()

    def login(self, username, password):
        logger.info(f"尝试登录用户: {username}")
        self.page = self.context.new_page()  # 每次登录都创建新页面
        self.page.goto(HOME_URL)
        
        # 使用动态等待，以确保页面状态正确
        try:
            self.page.wait_for_selector(".login-button .d-button-label", timeout=60000)  # 等待60秒
            self.page.click(".login-button .d-button-label")
        except Exception as e:
            logger.error(f"等待登录按钮失败: {e}")
            self.page.close()  # 确保页面被关闭
            return False
        
        self.page.fill("#login-account-name", username)
        self.page.fill("#login-account-password", password)
        self.page.click("#login-button")

        # 等待用户元素加载以验证是否登录成功
        try:
            self.page.wait_for_selector("#current-user", timeout=60000)  # 等待60秒
            user_ele = self.page.query_selector("#current-user")
            if not user_ele:
                logger.error(f"{username} 登录失败")
                return False
            else:
                logger.info(f"{username} 登录成功")
                return True
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
        finally:
            self.page.close()  # 不论成功与否，始终关闭页面以释放资源

    def click_topic(self):
        for topic in self.page.query_selector_all("#list-area .title"):
            logger.info("点击主题: " + topic.get_attribute("href"))
            page = self.context.new_page()
            page.goto(HOME_URL + topic.get_attribute("href"))
            time.sleep(3)
            if random.random() < 0.02:  # 100 * 0.02 * 30 = 60
                self.click_like(page)
            time.sleep(3)
            page.close()

    def run(self):
        for username, password in zip(USERNAME, PASSWORD):
            if not self.login(username, password):
                continue
            self.click_topic()
            self.print_connect_info()

    def click_like(self, page):
        logger.info("点击点赞")
        page.locator(".discourse-reactions-reaction-button").first.click()
        logger.info("点赞成功")

    def print_connect_info(self):
        logger.info("打印连接信息")
        page = self.context.new_page()
        page.goto("https://connect.linux.do/")
        rows = page.query_selector_all("table tr")

        info = []

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 3:
                project = cells[0].text_content().strip()
                current = cells[1].text_content().strip()
                requirement = cells[2].text_content().strip()
                info.append([project, current, requirement])

        print("--------------连接信息-----------------")
        print(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))

        page.close()

if __name__ == "__main__":
    if len(USERNAME) == 0 or len(PASSWORD) == 0:
        print("请设置 USERNAME 和 PASSWORD")
        exit(1)
    if len(USERNAME) != len(PASSWORD):
        print("用户和密码的数量不匹配")
        exit(1)
    l = LinuxDoBrowser()
    l.run()
