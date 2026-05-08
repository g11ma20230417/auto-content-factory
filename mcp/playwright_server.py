#!/usr/bin/env python3
"""
Playwright MCP Server - 为 Agent 提供浏览器自动化能力
基于 FastMCP 框架
"""

import os
import sys
import json
import logging
import asyncio
import random
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

server = Server("playwright-mcp")


@dataclass
class BrowserContext:
    browser = None
    context = None
    page = None
    playwright = None


browser_ctx = BrowserContext()


def random_delay(min_sec=0.5, max_sec=2.0):
    time.sleep(random.uniform(min_sec, max_sec))


def take_screenshot(name: str) -> str:
    screenshot_dir = Path("./logs/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{name}_{int(time.time())}.png"
    if browser_ctx.page:
        browser_ctx.page.screenshot(path=str(path))
    return str(path)


@server.list_tools()
def list_tools() -> List[Tool]:
    return [
        Tool(
            name="launch_browser",
            description="启动浏览器实例",
            inputSchema={
                "type": "object",
                "properties": {
                    "headless": {"type": "boolean", "description": "是否无头模式", "default": False},
                    "viewport_width": {"type": "integer", "description": "视口宽度", "default": 1280},
                    "viewport_height": {"type": "integer", "description": "视口高度", "default": 720}
                }
            }
        ),
        Tool(
            name="close_browser",
            description="关闭浏览器实例",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="navigate_to_url",
            description="导航到指定URL",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "description": "目标URL"},
                    "wait_until": {"type": "string", "description": "等待条件", "default": "networkidle"}
                }
            }
        ),
        Tool(
            name="fill_input",
            description="填写输入框",
            inputSchema={
                "type": "object",
                "required": ["selector", "value"],
                "properties": {
                    "selector": {"type": "string", "description": "CSS选择器或 XPath"},
                    "value": {"type": "string", "description": "要填写的值"}
                }
            }
        ),
        Tool(
            name="click_element",
            description="点击元素",
            inputSchema={
                "type": "object",
                "required": ["selector"],
                "properties": {
                    "selector": {"type": "string", "description": "CSS选择器或 XPath"},
                    "button": {"type": "string", "description": "鼠标按钮", "default": "left"}
                }
            }
        ),
        Tool(
            name="wait_for_selector",
            description="等待元素出现",
            inputSchema={
                "type": "object",
                "required": ["selector"],
                "properties": {
                    "selector": {"type": "string", "description": "CSS选择器"},
                    "timeout": {"type": "integer", "description": "超时时间(毫秒)", "default": 30000}
                }
            }
        ),
        Tool(
            name="get_text",
            description="获取元素文本",
            inputSchema={
                "type": "object",
                "required": ["selector"],
                "properties": {
                    "selector": {"type": "string", "description": "CSS选择器"}
                }
            }
        ),
        Tool(
            name="get_attribute",
            description="获取元素属性",
            inputSchema={
                "type": "object",
                "required": ["selector", "attribute"],
                "properties": {
                    "selector": {"type": "string", "description": "CSS选择器"},
                    "attribute": {"type": "string", "description": "属性名"}
                }
            }
        ),
        Tool(
            name="upload_file",
            description="上传文件",
            inputSchema={
                "type": "object",
                "required": ["selector", "file_path"],
                "properties": {
                    "selector": {"type": "string", "description": "文件输入框选择器"},
                    "file_path": {"type": "string", "description": "文件路径"}
                }
            }
        ),
        Tool(
            name="screenshot",
            description="截图",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "截图名称", "default": "screenshot"},
                    "full_page": {"type": "boolean", "description": "是否截取整页", "default": False}
                }
            }
        ),
        Tool(
            name="execute_script",
            description="执行JavaScript",
            inputSchema={
                "type": "object",
                "required": ["script"],
                "properties": {
                    "script": {"type": "string", "description": "JavaScript代码"}
                }
            }
        ),
        Tool(
            name="scroll",
            description="滚动页面",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X轴滚动像素"},
                    "y": {"type": "integer", "description": "Y轴滚动像素"}
                }
            }
        ),
        Tool(
            name="get_page_info",
            description="获取当前页面信息",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    global browser_ctx

    try:
        if name == "launch_browser":
            headless = arguments.get("headless", False)
            viewport_width = arguments.get("viewport_width", 1280)
            viewport_height = arguments.get("viewport_height", 720)

            browser_ctx.playwright = sync_playwright().start()
            browser_ctx.browser = browser_ctx.playwright.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            browser_ctx.context = browser_ctx.browser.new_context(
                viewport={'width': viewport_width, 'height': viewport_height},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            browser_ctx.page = browser_ctx.context.new_page()

            return [TextContent(type="text", text=f"✅ 浏览器启动成功 (headless={headless})")]

        elif name == "close_browser":
            if browser_ctx.browser:
                browser_ctx.browser.close()
            if browser_ctx.playwright:
                browser_ctx.playwright.stop()
            browser_ctx.browser = None
            browser_ctx.context = None
            browser_ctx.page = None
            browser_ctx.playwright = None

            return [TextContent(type="text", text="✅ 浏览器已关闭")]

        elif name == "navigate_to_url":
            url = arguments["url"]
            wait_until = arguments.get("wait_until", "networkidle")

            browser_ctx.page.goto(url, wait_until=wait_until, timeout=30000)
            random_delay()

            return [TextContent(type="text", text=f"✅ 已导航到: {url}")]

        elif name == "fill_input":
            selector = arguments["selector"]
            value = arguments["value"]

            element = browser_ctx.page.locator(selector)
            element.fill(value)
            random_delay()

            return [TextContent(type="text", text=f"✅ 已填写: {selector}")]

        elif name == "click_element":
            selector = arguments["selector"]
            button = arguments.get("button", "left")

            element = browser_ctx.page.locator(selector)
            element.click(button=button)
            random_delay()

            return [TextContent(type="text", text=f"✅ 已点击: {selector}")]

        elif name == "wait_for_selector":
            selector = arguments["selector"]
            timeout = arguments.get("timeout", 30000)

            browser_ctx.page.wait_for_selector(selector, timeout=timeout)
            random_delay(0.5, 1)

            return [TextContent(type="text", text=f"✅ 元素已出现: {selector}")]

        elif name == "get_text":
            selector = arguments["selector"]
            element = browser_ctx.page.locator(selector)
            text = element.inner_text()

            return [TextContent(type="text", text=text)]

        elif name == "get_attribute":
            selector = arguments["selector"]
            attribute = arguments["attribute"]

            element = browser_ctx.page.locator(selector)
            value = element.get_attribute(attribute)

            return [TextContent(type="text", text=str(value) if value else "")]

        elif name == "upload_file":
            selector = arguments["selector"]
            file_path = arguments["file_path"]

            element = browser_ctx.page.locator(selector)
            element.set_input_files(file_path)
            random_delay()

            return [TextContent(type="text", text=f"✅ 文件已上传: {file_path}")]

        elif name == "screenshot":
            name = arguments.get("name", "screenshot")
            full_page = arguments.get("full_page", False)

            path = take_screenshot(name)
            if full_page:
                browser_ctx.page.screenshot(path=path, full_page=True)

            return [TextContent(type="text", text=f"✅ 截图已保存: {path}")]

        elif name == "execute_script":
            script = arguments["script"]
            result = browser_ctx.page.evaluate(script)

            return [TextContent(type="text", text=str(result))]

        elif name == "scroll":
            x = arguments.get("x", 0)
            y = arguments.get("y", 500)

            browser_ctx.page.evaluate(f"window.scrollTo({x}, {y})")
            random_delay()

            return [TextContent(type="text", text=f"✅ 已滚动到 ({x}, {y})")]

        elif name == "get_page_info":
            info = {
                "url": browser_ctx.page.url,
                "title": browser_ctx.page.title(),
                "viewport": browser_ctx.context.viewport_size
            }

            return [TextContent(type="text", text=json.dumps(info, ensure_ascii=False, indent=2))]

        else:
            return [TextContent(type="text", text=f"❌ 未知工具: {name}")]

    except PlaywrightTimeoutError:
        return [TextContent(type="text", text=f"⏱️ 操作超时: {name}")]
    except Exception as e:
        logger.error(f"工具执行错误: {e}")
        take_screenshot(f"error_{name}")
        return [TextContent(type="text", text=f"❌ 错误: {str(e)}")]


async def main():
    logger.info("🚀 Playwright MCP Server 启动中...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
