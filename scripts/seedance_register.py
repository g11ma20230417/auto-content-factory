#!/usr/bin/env python3
"""
Seedance 自动注册脚本
使用 Playwright 实现自动化注册
"""

import os
import sys
import logging
import random
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('./logs/seedance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RandomDelay:
    @staticmethod
    def between(min_sec=0.5, max_sec=2.0):
        time.sleep(random.uniform(min_sec, max_sec))

    @staticmethod
    def human_like():
        time.sleep(random.uniform(0.3, 1.5))


class SeedanceRegister:
    def __init__(self):
        self.url = os.getenv("SEEDANCE_URL", "https://www.seedance.tv")
        self.email = os.getenv("SEEDANCE_EMAIL")
        self.password = os.getenv("SEEDANCE_PASSWORD")
        self.headless = os.getenv("HEADLESS", "false").lower() == "true"
        self.screenshot_dir = Path(os.getenv("SCREENSHOT_DIR", "./logs/screenshots"))
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        if not self.email or not self.password:
            logger.error("请设置 SEEDANCE_EMAIL 和 SEEDANCE_PASSWORD 环境变量")
            sys.exit(1)

    def launch_browser(self):
        logger.info("启动浏览器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = self.context.new_page()
        logger.info("浏览器启动成功")

    def close_browser(self):
        if hasattr(self, 'browser'):
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
        logger.info("浏览器已关闭")

    def take_screenshot(self, name):
        path = self.screenshot_dir / f"{name}_{int(time.time())}.png"
        self.page.screenshot(path=str(path))
        logger.info(f"截图已保存: {path}")
        return str(path)

    def handle_captcha(self):
        logger.info("检查验证码...")
        try:
            checkbox = self.page.locator('iframe[title*="captcha"]')
            if checkbox.count() > 0:
                logger.info("检测到验证码，需要人工介入")
                self.take_screenshot("captcha_required")
                input("⚠️  请人工完成验证后按回车继续...")
            else:
                try:
                    human_checkbox = self.page.get_by_text("I'm human", exact=False)
                    if human_checkbox.count() > 0:
                        human_checkbox.first.click()
                        logger.info("已点击人类验证复选框")
                        RandomDelay.between(2, 4)
                except PlaywrightTimeoutError:
                    logger.info("未检测到验证码")
        except Exception as e:
            logger.warning(f"验证码检查异常: {e}")

    def navigate_to_register(self):
        logger.info(f"导航到注册页面: {self.url}/signup")
        self.page.goto(f"{self.url}/signup", wait_until="networkidle", timeout=30000)
        RandomDelay.human_like()
        self.take_screenshot("register_page")

    def fill_registration_form(self):
        logger.info("填写注册表单...")
        try:
            email_input = self.page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]')
            if email_input.count() > 0:
                email_input.first.fill(self.email)
                logger.info("✓ 邮箱已填写")
                RandomDelay.human_like()
            else:
                raise ValueError("无法定位邮箱输入框")

            password_input = self.page.locator('input[type="password"], input[name="password"]')
            if password_input.count() > 0:
                password_input.first.fill(self.password)
                logger.info("✓ 密码已填写")
                RandomDelay.human_like()
            else:
                raise ValueError("无法定位密码输入框")

        except Exception as e:
            logger.error(f"填写表单失败: {e}")
            self.take_screenshot("form_fill_error")
            raise

    def submit_registration(self):
        logger.info("提交注册...")
        try:
            submit_btn = self.page.locator('button[type="submit"], input[type="submit"]')
            if submit_btn.count() > 0:
                submit_btn.first.click()
                logger.info("✓ 已点击提交按钮")
                RandomDelay.between(2, 4)
            else:
                alt_btns = self.page.locator('button:has-text("Sign Up"), button:has-text("注册"), button:has-text("Create Account")')
                if alt_btns.count() > 0:
                    alt_btns.first.click()
                    logger.info("✓ 已点击替代提交按钮")
                    RandomDelay.between(2, 4)
                else:
                    raise ValueError("无法定位提交按钮")
        except Exception as e:
            logger.error(f"提交失败: {e}")
            self.take_screenshot("submit_error")
            raise

    def wait_for_success(self):
        logger.info("等待注册结果...")
        try:
            success_indicators = [
                "text=注册成功",
                "text=Sign up successful",
                "text=Welcome",
                "text=验证邮箱",
                "text=Verify email"
            ]
            for indicator in success_indicators:
                try:
                    self.page.wait_for_selector(indicator, timeout=5000)
                    logger.info(f"✓ 检测到成功标志: {indicator}")
                    self.take_screenshot("registration_success")
                    return True
                except PlaywrightTimeoutError:
                    continue

            current_url = self.page.url
            logger.info(f"当前页面URL: {current_url}")
            if "dashboard" in current_url or "welcome" in current_url:
                self.take_screenshot("registration_success")
                return True

            logger.warning("未检测到明确的成功标志")
            self.take_screenshot("registration_unclear")
            return False

        except Exception as e:
            logger.error(f"验证结果异常: {e}")
            self.take_screenshot("verification_error")
            return False

    def check_credits(self):
        logger.info("检查积分余额...")
        try:
            self.page.goto(f"{self.url}/dashboard", wait_until="networkidle", timeout=15000)
            RandomDelay.human_like()

            credit_selectors = [
                'text=/\\d+\\s*(credits?|积分)/i',
                '[class*="credit"]',
                '[class*="balance"]',
                'text=/free.*trial/i'
            ]

            for selector in credit_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0:
                        credit_text = element.inner_text()
                        logger.info(f"✓ 积分信息: {credit_text}")
                        self.take_screenshot("credits_check")
                        return credit_text
                except PlaywrightTimeoutError:
                    continue

            logger.info("未在页面找到明确的积分显示")
            return None

        except Exception as e:
            logger.warning(f"积分检查异常: {e}")
            return None

    def run(self):
        logger.info("="*50)
        logger.info("🚀 Seedance 自动注册开始")
        logger.info("="*50)

        try:
            self.launch_browser()
            self.navigate_to_register()
            self.fill_registration_form()
            self.handle_captcha()
            self.submit_registration()
            success = self.wait_for_success()

            if success:
                credits = self.check_credits()
                logger.info("="*50)
                logger.info("✅ 注册完成!")
                logger.info(f"📧 邮箱: {self.email}")
                if credits:
                    logger.info(f"💰 积分: {credits}")
                logger.info("="*50)
                return True
            else:
                logger.error("❌ 注册结果不确定，请检查截图")
                return False

        except Exception as e:
            logger.error(f"❌ 注册过程出错: {e}")
            self.take_screenshot("registration_failed")
            return False

        finally:
            self.close_browser()


def main():
    register = SeedanceRegister()
    success = register.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
