#!/usr/bin/env python3
"""
Seedance 视频生成器
自动化生成 AI 视频
"""

import os
import sys
import logging
import random
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('./logs/seedance_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RandomDelay:
    @staticmethod
    def human_like():
        time.sleep(random.uniform(0.3, 1.5))

    @staticmethod
    def between(min_sec, max_sec):
        time.sleep(random.uniform(min_sec, max_sec))


class SeedanceGenerator:
    def __init__(self):
        self.url = os.getenv("SEEDANCE_URL", "https://www.seedance.tv")
        self.email = os.getenv("SEEDANCE_EMAIL")
        self.password = os.getenv("SEEDANCE_PASSWORD")
        self.headless = os.getenv("HEADLESS", "false").lower() == "true"
        self.output_dir = Path(os.getenv("VIDEO_OUTPUT_DIR", "./output/videos"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
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
            viewport={'width': 1920, 'height': 1080},
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
        logger.info(f"截图: {path}")
        return str(path)

    def login(self):
        logger.info("登录 Seedance...")
        try:
            self.page.goto(f"{self.url}/login", wait_until="networkidle", timeout=30000)
            RandomDelay.human_like()

            email_input = self.page.locator('input[type="email"], input[name="email"]')
            if email_input.count() > 0:
                email_input.first.fill(self.email)
                RandomDelay.human_like()

            password_input = self.page.locator('input[type="password"]')
            if password_input.count() > 0:
                password_input.fill(self.password)
                RandomDelay.human_like()

            submit_btn = self.page.locator('button[type="submit"]')
            if submit_btn.count() > 0:
                submit_btn.first.click()
                RandomDelay.between(3, 5)

            self.page.wait_for_url("**/dashboard**", timeout=15000)
            logger.info("✓ 登录成功")
            self.take_screenshot("logged_in")
            return True

        except Exception as e:
            logger.error(f"登录失败: {e}")
            self.take_screenshot("login_failed")
            return False

    def check_credits(self):
        logger.info("检查积分...")
        try:
            credit_text = None
            credit_selectors = [
                '[class*="credit"]',
                '[class*="balance"]',
                'text=/\\d+\\s*(credits?|积分)/'
            ]

            for selector in credit_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0:
                        credit_text = element.inner_text()
                        logger.info(f"✓ 积分: {credit_text}")
                        break
                except:
                    continue

            return credit_text

        except Exception as e:
            logger.warning(f"积分检查失败: {e}")
            return None

    def create_new_project(self, prompt):
        logger.info(f"创建新项目: {prompt[:50]}...")
        try:
            create_btn = self.page.locator(
                'button:has-text("Create"), button:has-text("新建"), '
                'button:has-text("New Project"), button:has-text("新项目")'
            )
            if create_btn.count() > 0:
                create_btn.first.click()
                RandomDelay.human_like()

            prompt_input = self.page.locator('textarea, input[type="text"]').filter(has_text="")
            for inp in prompt_input.all():
                try:
                    placeholder = inp.get_attribute("placeholder") or ""
                    if "prompt" in placeholder.lower() or "描述" in placeholder:
                        inp.fill(prompt)
                        logger.info("✓ 提示词已输入")
                        RandomDelay.human_like()
                        break
                except:
                    continue

            self.take_screenshot("project_created")
            return True

        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            self.take_screenshot("create_failed")
            return False

    def start_generation(self, style="cinematic", duration=5):
        logger.info("开始生成视频...")
        try:
            style_select = self.page.locator(
                'select, [class*="style"], [class*="quality"]'
            )
            if style_select.count() > 0:
                try:
                    style_select.first.select_option(style)
                    logger.info(f"✓ 风格: {style}")
                    RandomDelay.human_like()
                except:
                    pass

            generate_btn = self.page.locator(
                'button:has-text("Generate"), button:has-text("生成"), '
                'button:has-text("Create Video"), button:has-text("创建视频")'
            )
            if generate_btn.count() > 0:
                generate_btn.first.click()
                logger.info("✓ 点击生成按钮")
                RandomDelay.between(2, 4)
                return True

            return False

        except Exception as e:
            logger.error(f"开始生成失败: {e}")
            return False

    def wait_for_completion(self, timeout=600):
        logger.info("等待视频生成完成...")
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    progress_elements = self.page.locator(
                        '[class*="progress"], [class*="progress-bar"], '
                        'text=/\\d+%/'
                    )
                    for el in progress_elements.all():
                        try:
                            text = el.inner_text()
                            if "%" in text or "progress" in text.lower():
                                logger.info(f"进度: {text}")
                        except:
                            pass

                    complete_indicators = [
                        'text=/download/i',
                        'text=/完成/i',
                        '[class*="download"]',
                        'text=/ready/i'
                    ]

                    for indicator in complete_indicators:
                        if self.page.locator(indicator).count() > 0:
                            logger.info("✓ 视频生成完成")
                            self.take_screenshot("video_complete")
                            return True

                    RandomDelay.between(10, 15)

                except Exception as e:
                    logger.warning(f"检查进度时异常: {e}")
                    break

            logger.warning("生成超时")
            self.take_screenshot("generation_timeout")
            return False

        except Exception as e:
            logger.error(f"等待生成时异常: {e}")
            return False

    def download_video(self):
        logger.info("下载视频...")
        try:
            download_btn = self.page.locator(
                'a:has-text("Download"), button:has-text("下载"), '
                '[download]'
            )

            if download_btn.count() > 0:
                download_btn.first.click()
                logger.info("✓ 点击下载按钮")
                RandomDelay.between(3, 5)

                downloaded_files = list(self.output_dir.glob("*.mp4"))
                if downloaded_files:
                    latest = max(downloaded_files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"✓ 视频已保存: {latest}")
                    return str(latest)

            logger.warning("未找到下载按钮或视频文件")
            self.take_screenshot("download_check")
            return None

        except Exception as e:
            logger.error(f"下载失败: {e}")
            return None

    def run(self, prompt, style="cinematic", duration=5):
        logger.info("="*60)
        logger.info("🚀 Seedance 视频生成")
        logger.info("="*60)
        logger.info(f"提示词: {prompt}")

        video_path = None

        try:
            self.launch_browser()

            if not self.login():
                logger.error("登录失败，终止")
                return None

            credits = self.check_credits()
            if credits:
                logger.info(f"当前积分: {credits}")

            if not self.create_new_project(prompt):
                logger.error("创建项目失败")
                return None

            if not self.start_generation(style, duration):
                logger.error("开始生成失败")
                return None

            if not self.wait_for_completion():
                logger.warning("视频生成可能未完成")

            video_path = self.download_video()

            logger.info("="*60)
            if video_path:
                logger.info("✅ 视频生成成功!")
                logger.info(f"📁 路径: {video_path}")
            else:
                logger.info("⚠️  视频生成完成但下载失败，请手动检查")
            logger.info("="*60)

            return video_path

        except Exception as e:
            logger.error(f"❌ 生成过程出错: {e}")
            self.take_screenshot("generation_error")
            return None

        finally:
            self.close_browser()


def main():
    prompts = [
        "A majestic mountain landscape at sunrise with golden light",
        "Futuristic city with flying cars and neon lights",
        "Peaceful ocean waves crashing on a tropical beach",
        "Northern lights dancing across the Arctic sky",
        "Cherry blossoms falling in a Japanese garden"
    ]

    generator = SeedanceGenerator()
    prompt = random.choice(prompts)
    video_path = generator.run(prompt)

    if video_path:
        print(f"\n✅ 视频已生成: {video_path}")
        sys.exit(0)
    else:
        print("\n❌ 视频生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
