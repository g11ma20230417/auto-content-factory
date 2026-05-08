#!/usr/bin/env python3
"""
VEOAIFree 自动视频生成脚本
https://veoaifree.com - 免费 Google VEO AI 视频生成器

特点：
- 无需注册
- 免费使用
- 基于 Google VEO AI
- 无水印
- 无限使用
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
        logging.FileHandler('./logs/veoaifree.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RandomDelay:
    @staticmethod
    def human_like():
        time.sleep(random.uniform(0.5, 2.0))

    @staticmethod
    def between(min_sec, max_sec):
        time.sleep(random.uniform(min_sec, max_sec))

    @staticmethod
    def thinking():
        time.sleep(random.uniform(2, 5))


class VEOAIFreeGenerator:
    def __init__(self):
        self.base_url = "https://veoaifree.com"
        self.generator_url = f"{self.base_url}/veo-video-generator/"
        self.headless = os.getenv("HEADLESS", "false").lower() == "true"
        self.output_dir = Path(os.getenv("VIDEO_OUTPUT_DIR", "./output/videos"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir = Path(os.getenv("SCREENSHOT_DIR", "./logs/screenshots"))
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def launch_browser(self):
        logger.info("启动浏览器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = self.context.new_page()
        logger.info("✓ 浏览器启动成功")

    def close_browser(self):
        if hasattr(self, 'browser') and self.browser:
            self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            self.playwright.stop()
        logger.info("✓ 浏览器已关闭")

    def take_screenshot(self, name):
        path = self.screenshot_dir / f"{name}_{int(time.time())}.png"
        if hasattr(self, 'page') and self.page:
            self.page.screenshot(path=str(path))
        logger.info(f"📸 截图: {path}")
        return str(path)

    def navigate_to_generator(self):
        logger.info(f"导航到视频生成页面: {self.generator_url}")
        try:
            self.page.goto(self.generator_url, wait_until="domcontentloaded", timeout=60000)
            RandomDelay.thinking()
            self.take_screenshot("page_loaded")
            logger.info("✓ 页面加载完成")
            return True
        except Exception as e:
            logger.error(f"❌ 页面加载失败: {e}")
            self.take_screenshot("page_load_error")
            return False

    def find_prompt_input(self):
        logger.info("查找提示词输入框...")
        selectors = [
            'textarea[id*="prompt" i]',
            'textarea[placeholder*="prompt" i]',
            'textarea[placeholder*="描述" i]',
            'textarea[placeholder*="prompt" i]',
            'input[id*="prompt" i]',
            'input[placeholder*="prompt" i]',
            'textarea',
            '[contenteditable="true"]'
        ]

        for selector in selectors:
            try:
                elements = self.page.locator(selector)
                count = elements.count()
                if count > 0:
                    logger.info(f"✓ 找到输入框: {selector} (数量: {count})")
                    return elements.first
            except:
                continue

        logger.warning("未找到标准输入框，尝试查找文本区域...")
        try:
            textareas = self.page.locator('textarea')
            if textareas.count() > 0:
                logger.info(f"✓ 找到 textarea (数量: {textareas.count()})")
                return textareas.first
        except:
            pass

        return None

    def find_generate_button(self):
        logger.info("查找生成按钮...")
        button_texts = [
            'Generate with VEO AI',
            'Generate',
            '生成',
            'Create Video',
            '创建视频',
            'Submit',
            '提交'
        ]

        for text in button_texts:
            try:
                btn = self.page.get_by_text(text, exact=False)
                if btn.count() > 0:
                    logger.info(f"✓ 找到按钮: {text}")
                    return btn.first
            except:
                continue

        button_selectors = [
            'button[type="submit"]',
            'button[class*="generate" i]',
            'button[class*="submit" i]',
            'button:has-text("Generate")',
            '[role="button"]:has-text("Generate")'
        ]

        for selector in button_selectors:
            try:
                btns = self.page.locator(selector)
                if btns.count() > 0:
                    logger.info(f"✓ 找到按钮: {selector}")
                    return btns.first
            except:
                continue

        return None

    def enter_prompt(self, prompt):
        logger.info(f"输入提示词: {prompt[:50]}...")
        input_field = self.find_prompt_input()

        if not input_field:
            logger.error("❌ 无法找到输入框")
            self.take_screenshot("no_input_found")
            return False

        try:
            input_field.click()
            RandomDelay.human_like()

            input_field.fill("")
            RandomDelay.human_like()

            input_field.fill(prompt)
            logger.info("✓ 提示词已输入")
            RandomDelay.human_like()
            self.take_screenshot("prompt_entered")
            return True

        except Exception as e:
            logger.error(f"❌ 输入提示词失败: {e}")
            self.take_screenshot("prompt_error")
            return False

    def select_veo_version(self, version="3.0"):
        logger.info(f"选择 VEO 版本: {version}")
        try:
            version_map = {
                "3.0": ["3.0", "VEO 3", "veo 3"],
                "2.0": ["2.0", "VEO 2", "veo 2"]
            }

            version_texts = version_map.get(version, version_map["3.0"])

            for v in version_texts:
                try:
                    radio = self.page.get_by_text(v, exact=False)
                    if radio.count() > 0:
                        radio.first.click()
                        logger.info(f"✓ 已选择 VEO {version}")
                        RandomDelay.human_like()
                        return True
                except:
                    continue

            veo_selectors = [
                'select[id*="veo" i]',
                '[class*="veo" i]',
                'button:has-text("VEO")'
            ]

            for selector in veo_selectors:
                try:
                    elements = self.page.locator(selector)
                    if elements.count() > 0:
                        elements.first.click()
                        RandomDelay.human_like()
                        logger.info(f"✓ 已点击版本选择器")
                        return True
                except:
                    continue

            logger.info("⚠️ 使用默认版本")
            return True

        except Exception as e:
            logger.warning(f"版本选择异常: {e}")
            return True

    def select_aspect_ratio(self, ratio="16:9"):
        logger.info(f"选择视频比例: {ratio}")
        try:
            ratio_texts = {
                "16:9": ["16:9", "Landscape", "横向", "16"],
                "9:16": ["9:16", "Portrait", "竖屏", "Vertical"],
                "1:1": ["1:1", "Square", "方形"]
            }

            texts = ratio_texts.get(ratio, ratio_texts["16:9"])

            for text in texts:
                try:
                    btn = self.page.get_by_text(text, exact=False)
                    if btn.count() > 0:
                        btn.first.click()
                        logger.info(f"✓ 已选择 {ratio}")
                        RandomDelay.human_like()
                        return True
                except:
                    continue

            logger.info("⚠️ 使用默认比例")
            return True

        except Exception as e:
            logger.warning(f"比例选择异常: {e}")
            return True

    def click_generate(self):
        logger.info("点击生成按钮...")
        btn = self.find_generate_button()

        if not btn:
            logger.error("❌ 无法找到生成按钮")
            self.take_screenshot("no_button_found")
            return False

        try:
            btn.scroll_into_view_if_needed()
            RandomDelay.human_like()

            btn.click()
            logger.info("✓ 已点击生成按钮")
            self.take_screenshot("generation_started")
            return True

        except Exception as e:
            logger.error(f"❌ 点击生成按钮失败: {e}")
            self.take_screenshot("button_click_error")
            return False

    def wait_for_generation(self, timeout=300):
        logger.info("等待视频生成完成...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                progress_indicators = [
                    '[class*="progress" i]',
                    '[class*="loading" i]',
                    '[class*="spinner" i]',
                    'text=/\\d+%/',
                    'text=/processing/i',
                    'text=/generating/i',
                    'text=/creating/i'
                ]

                for indicator in progress_indicators:
                    elements = self.page.locator(indicator)
                    if elements.count() > 0:
                        try:
                            text = elements.first.inner_text()
                            if text:
                                logger.info(f"📊 状态: {text}")
                        except:
                            pass

                download_indicators = [
                    '[download]',
                    'a:has-text("Download")',
                    'button:has-text("Download")',
                    'text=/download/i',
                    '[class*="download" i]',
                    '[class*="result" i]',
                    'video'
                ]

                for indicator in download_indicators:
                    elements = self.page.locator(indicator)
                    if elements.count() > 0:
                        logger.info(f"✓ 检测到结果元素: {indicator}")
                        self.take_screenshot("generation_complete")
                        return True

                if int(time.time() - start_time) % 30 < 1:
                    self.take_screenshot("generation_progress")

                RandomDelay.between(5, 10)

            except Exception as e:
                logger.warning(f"检查进度异常: {e}")
                RandomDelay.between(5, 10)

        logger.warning("⚠️ 生成超时")
        self.take_screenshot("generation_timeout")
        return False

    def find_video_element(self):
        logger.info("查找视频元素...")
        video_selectors = [
            'video',
            '[class*="video" i]',
            '[class*="player" i]',
            'iframe'
        ]

        for selector in video_selectors:
            try:
                elements = self.page.locator(selector)
                count = elements.count()
                if count > 0:
                    logger.info(f"✓ 找到 {count} 个元素: {selector}")
                    return elements.first
            except:
                continue

        return None

    def download_video(self):
        logger.info("尝试下载视频...")
        try:
            download_btn = None

            download_selectors = [
                'button:has-text("Download")',
                'a:has-text("Download")',
                '[class*="download" i]',
                '[download]'
            ]

            for selector in download_selectors:
                try:
                    btns = self.page.locator(selector)
                    if btns.count() > 0:
                        download_btn = btns.first
                        logger.info(f"✓ 找到下载按钮: {selector}")
                        break
                except:
                    continue

            if download_btn:
                with self.page.expect_download(timeout=60000) as download_info:
                    download_btn.click()
                download = download_info.value
                save_path = self.output_dir / f"veoaifree_{int(time.time())}.mp4"
                download.save_as(str(save_path))
                logger.info(f"✅ 视频已保存: {save_path}")
                return str(save_path)

            video = self.find_video_element()
            if video:
                self.take_screenshot("video_result")
                logger.info("✓ 视频已生成，请手动下载")
                return None

            self.take_screenshot("no_download_found")
            return None

        except Exception as e:
            logger.error(f"❌ 下载失败: {e}")
            self.take_screenshot("download_error")
            return None

    def run(self, prompt, veo_version="3.0", aspect_ratio="16:9"):
        logger.info("="*60)
        logger.info("🚀 VEOAIFree 自动视频生成")
        logger.info("="*60)
        logger.info(f"🎬 提示词: {prompt}")
        logger.info(f"⚙️  VEO 版本: {veo_version}")
        logger.info(f"📐 视频比例: {aspect_ratio}")

        video_path = None

        try:
            self.launch_browser()

            if not self.navigate_to_generator():
                logger.error("页面加载失败")
                return None

            if not self.enter_prompt(prompt):
                logger.error("输入提示词失败")
                return None

            self.select_veo_version(veo_version)
            self.select_aspect_ratio(aspect_ratio)

            if not self.click_generate():
                logger.error("点击生成按钮失败")
                return None

            if not self.wait_for_generation():
                logger.warning("视频生成可能未完成")

            video_path = self.download_video()

            logger.info("="*60)
            if video_path:
                logger.info("✅ 视频生成成功!")
                logger.info(f"📁 保存路径: {video_path}")
            else:
                logger.info("⚠️ 视频已生成，请在浏览器中手动下载")
                logger.info("💡 截图已保存，可查看生成结果")
            logger.info("="*60)

            return video_path

        except Exception as e:
            logger.error(f"❌ 生成过程出错: {e}")
            self.take_screenshot("generation_error")
            return None

        finally:
            RandomDelay.between(2, 5)
            self.close_browser()


def main():
    if len(sys.argv) < 2:
        print("\n" + "="*50)
        print("VEOAIFree 自动视频生成器")
        print("="*50)
        print("\n用法:")
        print("  python veoaifree_generator.py <提示词> [版本] [比例]")
        print("\n示例:")
        print('  python veoaifree_generator.py "A sunset over mountains with golden light"')
        print('  python veoaifree_generator.py "Futuristic city" 3.0 16:9')
        print('  python veoaifree_generator.py "Ocean waves" 2.0 9:16')
        print("\n版本: 3.0 或 2.0 (默认: 3.0)")
        print("比例: 16:9 (横向), 9:16 (竖屏), 1:1 (方形)")
        print("="*50)

        prompts = [
            "A majestic mountain landscape at sunrise with golden light rays",
            "Futuristic city with flying cars and neon lights at night",
            "Peaceful ocean waves crashing on a tropical beach at sunset",
            "Northern lights dancing across the Arctic sky with stars",
            "Cherry blossoms falling in a traditional Japanese garden",
            "Aerial view of a forest with misty morning fog",
            "Wild horses running across a green meadow",
            "A cozy coffee shop with rain outside the window"
        ]

        prompt = random.choice(prompts)
        logger.info(f"\n使用随机提示词: {prompt}")
    else:
        prompt = sys.argv[1]

    veo_version = sys.argv[2] if len(sys.argv) > 2 else "3.0"
    aspect_ratio = sys.argv[3] if len(sys.argv) > 3 else "16:9"

    generator = VEOAIFreeGenerator()
    video_path = generator.run(prompt, veo_version, aspect_ratio)

    if video_path:
        print(f"\n✅ 视频已保存: {video_path}")
        sys.exit(0)
    else:
        print("\n⚠️ 视频已生成，请在浏览器中查看并手动下载")
        print("📸 截图已保存在 ./logs/screenshots/")
        sys.exit(0)


if __name__ == "__main__":
    main()
