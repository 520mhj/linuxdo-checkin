import os
import random
import time

from loguru import logger
from playwright.sync_api import sync_playwright
from tabulate import tabulate

USERNAME = os.environ.get("USERNAME").split(",")
PASSWORD = os.environ.get("PASSWORD").split(",")

HOME_URL = "https://linux.do/"

class LinuxDoBrowser:
    def __init__(self) -> None:
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True, timeout=30000)
        self.context = self.browser.new_context()

    def login(self, username, password):
        # 每次登录都创建新的页面
        self.page = self.context.new_page()
        self.page.goto(HOME_URL)
        # 调试：打印页面的完整HTML
        print(self.page.content())

        logger.info(f"尝试登录用户: {username}")
        
        try:
            # 等待并点击登录按钮
            self.page.wait_for_selector(".login-button .d-button-label", timeout=30000)
            self.page.click(".login-button .d-button-label")
            
            # 填写用户名和密码
            self.page.fill("#login-account-name", username)
            self.page.fill("#login-account-password", password)
            
            # 点击确认登录
            self.page.click("#login-button")
            
            # 等待登录完成
            time.sleep(10)
            
            # 检查是否登录成功
            user_ele = self.page.query_selector("#current-user")
            if not user_ele:
                logger.error(f"用户 {username} 登录失败")
                self.page.close()
                return False
            
            logger.info(f"用户 {username} 登录成功")
            return True
        
        except Exception as e:
            logger.error(f"登录过程出现错误: {e}")
            self.page.close()
            return False

    def click_topic(self):
        for topic in self.page.query_selector_all("#list-area .title"):
            logger.info("点击主题: " + topic.get_attribute("href"))
            page = self.context.new_page()
            page.goto(HOME_URL + topic.get_attribute("href"))
            time.sleep(3)
            if random.random() < 0.02:  # 2%概率点赞
                self.click_like(page)
            time.sleep(3)
            page.close()

    def run(self):
        for username, password in zip(USERNAME, PASSWORD):
            # 每个用户重新生成页面
            login_result = self.login(username, password)
            
            if not login_result:
                logger.error(f"用户 {username} 登录失败，跳过后续操作")
                continue
            
            # 点击主题和打印连接信息
            self.click_topic()
            self.print_connect_info()
            
            # 关闭当前页面
            self.page.close()

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
    if not USERNAME or not PASSWORD:
        print("请设置 USERNAME 和 PASSWORD")
        exit(1)
    
    l = LinuxDoBrowser()
    l.run()
