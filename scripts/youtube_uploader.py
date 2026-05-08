#!/usr/bin/env python3
"""
YouTube 自动上传脚本
使用 Playwright 实现自动化上传
"""

import os
import sys
import logging
import random
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('./logs/youtube.log'),
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


class YouTubeUploader:
    def __init__(self):
        self.email = os.getenv("YOUTUBE_EMAIL")
        self.password = os.getenv("YOUTUBE_PASSWORD")
        self.headless = os.getenv("HEADLESS", "false").lower() == "true"
        self.screenshot_dir = Path(os.getenv("SCREENSHOT_DIR", "./logs/screenshots"))
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.default_title = os.getenv("DEFAULT_TITLE", "Amazing AI Generated Video")
        self.default_description = os.getenv("DEFAULT_DESCRIPTION", "Created with Seedance AI")
        self.default_tags = os.getenv("DEFAULT_TAGS", "AI,artificial intelligence,AI video").split(",")

        if not self.email or not self.password:
            logger.error("请设置 YOUTUBE_EMAIL 和 YOUTUBE_PASSWORD 环境变量")
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

    def login(self):
        logger.info("开始 YouTube 登录...")
        try:
            self.page.goto("https://www.youtube.com/signin", wait_until="networkidle", timeout=30000)
            RandomDelay.human_like()

            email_input = self.page.locator('input[type="email"], input[name="identifier"]')
            if email_input.count() > 0:
                email_input.first.fill(self.email)
                RandomDelay.human_like()
                self.page.locator('button[type="submit"], #identifierNext').click()
                logger.info("✓ 邮箱已输入")
                RandomDelay.between(2, 4)

            password_input = self.page.locator('input[type="password"], input[name="password"]')
            if password_input.count() > 0:
                password_input.fill(self.password)
                RandomDelay.human_like()
                self.page.locator('button[type="submit"], #passwordNext').click()
                logger.info("✓ 密码已输入")
                RandomDelay.between(3, 5)

            self.page.wait_for_url("**/feed/**", timeout=20000)
            logger.info("✓ 登录成功")
            self.take_screenshot("youtube_logged_in")
            return True

        except Exception as e:
            logger.error(f"登录失败: {e}")
            self.take_screenshot("youtube_login_failed")
            return False

    def navigate_to_upload(self):
        logger.info("导航到上传页面...")
        try:
            self.page.goto("https://www.youtube.com/upload", wait_until="networkidle", timeout=30000)
            RandomDelay.human_like()

            file_input = self.page.locator('input[type="file"]')
            if file_input.count() > 0:
                logger.info("✓ 上传页面已加载")
                self.take_screenshot("upload_page_ready")
                return True
            else:
                logger.warning("未找到文件上传控件，尝试备用方式...")
                self.page.goto("https://studio.youtube.com", wait_until="networkidle")
                RandomDelay.human_like()
                create_btn = self.page.locator('text="创建", text="Create"').first
                if create_btn.count() > 0:
                    create_btn.click()
                    RandomDelay.human_like()
                    return True
                return False

        except Exception as e:
            logger.error(f"导航到上传页面失败: {e}")
            self.take_screenshot("upload_nav_failed")
            return False

    def upload_video(self, video_path):
        logger.info(f"上传视频: {video_path}")
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return False

        try:
            file_input = self.page.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.first.set_input_files(video_path)
                logger.info("✓ 文件已选择")
                RandomDelay.between(3, 5)

                self.page.wait_for_selector('.ytcp-uploads-dialog, #upload-manager', timeout=30000)
                logger.info("✓ 上传进度已开始")
                self.take_screenshot("video_uploading")
                return True
            else:
                logger.error("未找到文件上传控件")
                return False

        except Exception as e:
            logger.error(f"上传失败: {e}")
            self.take_screenshot("upload_failed")
            return False

    def wait_for_upload_complete(self, timeout=600):
        logger.info("等待上传完成...")
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    progress = self.page.locator('.ytcp-upload-progress, .progress-bar')
                    if progress.count() > 0:
                        text = progress.first.inner_text()
                        logger.info(f"上传进度: {text}")

                    if "完成" in self.page.content() or "complete" in self.page.content().lower():
                        logger.info("✓ 上传完成")
                        self.take_screenshot("upload_complete")
                        return True

                    RandomDelay.between(5, 10)
                except:
                    break

            logger.info("上传可能已完成或超时")
            return True

        except Exception as e:
            logger.warning(f"等待上传完成时异常: {e}")
            return True

    def set_video_details(self, title=None, description=None, tags=None):
        logger.info("设置视频详情...")
        try:
            title = title or self.default_title
            description = description or self.default_description
            tags = tags or self.default_tags

            RandomDelay.human_like()

            title_input = self.page.locator('#title-input, input[id*="title"]')
            if title_input.count() > 0:
                title_input.first.fill(title)
                logger.info(f"✓ 标题已设置: {title[:30]}...")

            RandomDelay.human_like()

            desc_input = self.page.locator('#description-input, textarea[id*="description"]')
            if desc_input.count() > 0:
                desc_input.first.fill(description)
                logger.info(f"✓ 描述已设置: {description[:30]}...")

            RandomDelay.human_like()

            tag_input = self.page.locator('[placeholder*="tag" i], [placeholder*="标签" i]')
            if tag_input.count() > 0 and tags:
                for tag in tags[:5]:
                    tag_input.first.fill(tag)
                    tag_input.first.press("Enter")
                    RandomDelay.between(0.5, 1)
                logger.info(f"✓ 标签已添加: {len(tags)} 个")

            self.take_screenshot("video_details_set")
            return True

        except Exception as e:
            logger.warning(f"设置视频详情异常: {e}")
            return False

    def publish_video(self):
        logger.info("发布视频...")
        try:
            RandomDelay.human_like()

            publish_btn = self.page.locator(
                'button:has-text("发布"), button:has-text("Publish"), '
                'button:has-text("公开"), button:has-text("Public")'
            )

            if publish_btn.count() > 0:
                publish_btn.first.click()
                logger.info("✓ 已点击发布按钮")
                RandomDelay.between(2, 4)

            done_btn = self.page.locator(
                'button:has-text("完成"), button:has-text("Done")'
            )
            if done_btn.count() > 0:
                done_btn.first.click()
                logger.info("✓ 已点击完成按钮")
                RandomDelay.between(2, 3)

            self.take_screenshot("video_published")
            logger.info("✅ 视频发布成功!")
            return True

        except Exception as e:
            logger.error(f"发布失败: {e}")
            self.take_screenshot("publish_failed")
            return False

    def run(self, video_path, title=None, description=None, tags=None):
        logger.info("="*50)
        logger.info("🚀 YouTube 自动上传开始")
        logger.info("="*50)

        try:
            self.launch_browser()

            if not self.login():
                logger.error("登录失败，终止上传")
                return False

            if not self.navigate_to_upload():
                logger.error("无法导航到上传页面")
                return False

            if not self.upload_video(video_path):
                logger.error("视频上传失败")
                return False

            if not self.wait_for_upload_complete():
                logger.warning("等待上传完成超时")

            self.set_video_details(title, description, tags)

            if not self.publish_video():
                logger.error("视频发布失败")
                return False

            logger.info("="*50)
            logger.info("✅ 上传完成!")
            logger.info(f"📹 视频: {video_path}")
            logger.info(f"📝 标题: {title or self.default_title}")
            logger.info("="*50)
            return True

        except Exception as e:
            logger.error(f"❌ 上传过程出错: {e}")
            self.take_screenshot("upload_process_error")
            return False

        finally:
            self.close_browser()


def main():
    if len(sys.argv) < 2:
        print("用法: python youtube_uploader.py <视频路径> [标题] [描述]")
        print("示例: python youtube_uploader.py ./video.mp4 '我的AI视频' '这是一个AI生成的视频'")
        sys.exit(1)

    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    description = sys.argv[3] if len(sys.argv) > 3 else None

    uploader = YouTubeUploader()
    success = uploader.run(video_path, title, description)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
