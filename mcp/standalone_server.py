#!/usr/bin/env python3
"""
独立版 Playwright MCP Server
提供标准输入输出接口，兼容所有 Agent
"""

import os
import sys
import json
import logging
import random
import time
from pathlib import Path
from typing import Dict, Any, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class PlaywrightMCP:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.screenshot_dir = Path("./logs/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def random_delay(self, min_sec=0.5, max_sec=2.0):
        time.sleep(random.uniform(min_sec, max_sec))

    def take_screenshot(self, name: str) -> str:
        path = self.screenshot_dir / f"{name}_{int(time.time())}.png"
        if self.page:
            self.page.screenshot(path=str(path))
        return str(path)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        tool = request.get("tool")
        params = request.get("params", {})

        try:
            if tool == "launch_browser":
                return self._launch_browser(params)
            elif tool == "close_browser":
                return self._close_browser()
            elif tool == "navigate_to_url":
                return self._navigate_to_url(params)
            elif tool == "fill_input":
                return self._fill_input(params)
            elif tool == "click_element":
                return self._click_element(params)
            elif tool == "wait_for_selector":
                return self._wait_for_selector(params)
            elif tool == "get_text":
                return self._get_text(params)
            elif tool == "screenshot":
                return self._screenshot(params)
            elif tool == "upload_file":
                return self._upload_file(params)
            elif tool == "scroll":
                return self._scroll(params)
            elif tool == "execute_script":
                return self._execute_script(params)
            elif tool == "get_page_info":
                return self._get_page_info()
            else:
                return {"success": False, "error": f"Unknown tool: {tool}"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}

    def _launch_browser(self, params: Dict) -> Dict:
        headless = params.get("headless", False)
        viewport_width = params.get("viewport_width", 1280)
        viewport_height = params.get("viewport_height", 720)

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            viewport={'width': viewport_width, 'height': viewport_height}
        )
        self.page = self.context.new_page()

        return {"success": True, "message": f"Browser launched (headless={headless})"}

    def _close_browser(self) -> Dict:
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

        return {"success": True, "message": "Browser closed"}

    def _navigate_to_url(self, params: Dict) -> Dict:
        url = params.get("url")
        wait_until = params.get("wait_until", "networkidle")

        self.page.goto(url, wait_until=wait_until, timeout=30000)
        self.random_delay()

        return {"success": True, "url": self.page.url}

    def _fill_input(self, params: Dict) -> Dict:
        selector = params.get("selector")
        value = params.get("value")

        self.page.locator(selector).fill(value)
        self.random_delay()

        return {"success": True, "message": f"Filled: {selector}"}

    def _click_element(self, params: Dict) -> Dict:
        selector = params.get("selector")
        button = params.get("button", "left")

        self.page.locator(selector).click(button=button)
        self.random_delay()

        return {"success": True, "message": f"Clicked: {selector}"}

    def _wait_for_selector(self, params: Dict) -> Dict:
        selector = params.get("selector")
        timeout = params.get("timeout", 30000)

        self.page.wait_for_selector(selector, timeout=timeout)
        self.random_delay(0.5, 1)

        return {"success": True, "message": f"Element found: {selector}"}

    def _get_text(self, params: Dict) -> Dict:
        selector = params.get("selector")
        text = self.page.locator(selector).inner_text()

        return {"success": True, "text": text}

    def _screenshot(self, params: Dict) -> Dict:
        name = params.get("name", "screenshot")
        path = self.take_screenshot(name)

        return {"success": True, "path": path}

    def _upload_file(self, params: Dict) -> Dict:
        selector = params.get("selector")
        file_path = params.get("file_path")

        self.page.locator(selector).set_input_files(file_path)
        self.random_delay()

        return {"success": True, "message": f"Uploaded: {file_path}"}

    def _scroll(self, params: Dict) -> Dict:
        x = params.get("x", 0)
        y = params.get("y", 500)

        self.page.evaluate(f"window.scrollTo({x}, {y})")
        self.random_delay()

        return {"success": True, "message": f"Scrolled to ({x}, {y})"}

    def _execute_script(self, params: Dict) -> Dict:
        script = params.get("script")
        result = self.page.evaluate(script)

        return {"success": True, "result": result}

    def _get_page_info(self) -> Dict:
        return {
            "success": True,
            "url": self.page.url,
            "title": self.page.title()
        }


def main():
    """MCP Server 主循环 - 从 stdin 读取请求，输出到 stdout"""
    mcp = PlaywrightMCP()
    logger.info("🚀 Playwright MCP Server 启动...")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line.strip())
            response = mcp.handle_request(request)

            print(json.dumps(response), flush=True)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(json.dumps({"success": False, "error": str(e)}), flush=True)

    mcp._close_browser()
    logger.info("👋 MCP Server 已关闭")


if __name__ == "__main__":
    main()
