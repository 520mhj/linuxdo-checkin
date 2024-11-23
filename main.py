import os
import random
import time

from loguru import logger
from playwright.sync_api import sync_playwright
from tabulate import tabulate

# 获取以逗号分隔的多个用户名和密码
USERNAMES = os.environ.get("USERNAME", "").split(",")
PASSWORDS = os.environ.get("PASSWORD", "").split(",")

HOME_URL = "https://linux.do/"

class LinuxDoBrowser:
    def __init__(self) -> None:
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True, timeout=30000)

    def login(self, context, username, password):
        page = context.new_page()
        page.goto(HOME_URL)

        logger.info(f"尝试登录用户: {username}")

        try:
            # 等待并点击登录按钮
            page.wait_for_selector(".login-button .d-button-label", timeout=60000)  # 等待60秒
            page.click(".login-button .d-button-label")

            # 填写用户名和密码
            page.fill("#login-account-name", username)
            page.fill("#login-account-password", password)

            # 点击确认登录
            page.click("#login-button")

            # 等待登录完成
            page.wait_for_selector("#current-user", timeout=60000)  # 等待60秒

            user_ele = page.query_selector("#current-user")
            if not user_ele:
                logger.error(f"用户 {username} 登录失败")
                page.close()
                return False

            logger.info(f"用户 {username} 登录成功")
            return page  # 返回已登录的页面
        except Exception as e:
            logger.error(f"用户 {username} 登录过程中出现错误: {e}")
            page.close()
            return False

    def click_topic(self, page):
        try:
            page.wait_for_selector("#list-area .title", timeout=60000)  # 等待主题加载
            topics = page.query_selector_all("#list-area .title")
            for topic in topics:
                href = topic.get_attribute("href")
                logger.info(f"点击主题: {href}")
                topic_page = page.context.new_page()
                topic_page.goto(HOME_URL + href)
                time.sleep(3)
                if random.random() < 0.02:  # 2%概率点赞
                    self.click_like(topic_page)
                time.sleep(3)
                topic_page.close()
        except Exception as e:
            logger.error(f"点击主题过程中出现错误: {e}")

    def run(self):
        if not USERNAMES or not PASSWORDS:
            logger.error("请设置 USERNAME 和 PASSWORD 环境变量")
            return

        if len(USERNAMES) != len(PASSWORDS):
            logger.error("用户名和密码的数量不匹配")
            return

        for username, password in zip(USERNAMES, PASSWORDS):
            context = self.browser.new_context()
            login_result = self.login(context, username, password)
            if not login_result:
                logger.error(f"用户 {username} 登录失败，跳过后续操作")
                context.close()
                continue

            page = login_result
            self.click_topic(page)
            self.print_connect_info(context)

            # 完成后关闭上下文
            context.close()

    def click_like(self, page):
        try:
            page.locator(".discourse-reactions-reaction-button").first.click()
            logger.info("点赞成功")
        except Exception as e:
            logger.error(f"点赞过程中出现错误: {e}")

    def print_connect_info(self, context):
        try:
            page = context.new_page()
            page.goto("https://connect.linux.do/")
            page.wait_for_selector("table tr", timeout=60000)

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
        except Exception as e:
            logger.error(f"打印连接信息过程中出现错误: {e}")

    def close(self):
        self.browser.close()
        self.pw.stop()

if __name__ == "__main__":
    l = LinuxDoBrowser()
    try:
        l.run()
    finally:
        l.close()
