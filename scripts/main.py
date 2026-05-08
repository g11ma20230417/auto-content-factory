#!/usr/bin/env python3
"""
Auto Content Factory - 主入口
一键完成：Seedance注册 → 视频生成 → YouTube上传
赚钱流水线！
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def setup_directories():
    Path("./logs/screenshots").mkdir(parents=True, exist_ok=True)
    Path("./output/videos").mkdir(parents=True, exist_ok=True)
    logger.info("✓ 目录结构已创建")


def run_seedance_register():
    logger.info("="*60)
    logger.info("📋 阶段1: Seedance 注册")
    logger.info("="*60)
    try:
        from seedance_register import SeedanceRegister
        register = SeedanceRegister()
        success = register.run()
        return success
    except Exception as e:
        logger.error(f"Seedance 注册失败: {e}")
        return False


def run_seedance_generate(prompt=None, style="cinematic"):
    logger.info("="*60)
    logger.info("📋 阶段2: Seedance 视频生成")
    logger.info("="*60)
    try:
        from seedance_generator import SeedanceGenerator
        generator = SeedanceGenerator()

        if not prompt:
            prompts = [
                "A majestic mountain landscape at sunrise with golden light",
                "Futuristic city with flying cars and neon lights",
                "Peaceful ocean waves on a tropical beach",
                "Northern lights dancing across the Arctic sky",
                "Cherry blossoms falling in a Japanese garden"
            ]
            import random
            prompt = random.choice(prompts)

        logger.info(f"使用提示词: {prompt}")
        video_path = generator.run(prompt, style)
        return video_path
    except Exception as e:
        logger.error(f"视频生成失败: {e}")
        return None


def run_youtube_upload(video_path, title=None, description=None, tags=None):
    logger.info("="*60)
    logger.info("📋 阶段3: YouTube 上传")
    logger.info("="*60)
    try:
        from youtube_uploader import YouTubeUploader
        uploader = YouTubeUploader()
        success = uploader.run(video_path, title, description, tags)
        return success
    except Exception as e:
        logger.error(f"YouTube 上传失败: {e}")
        return False


def run_full_pipeline():
    logger.info("="*60)
    logger.info("🚀 Auto Content Factory - 全自动流水线")
    logger.info("   目标: Seedance 免费积分 → AI视频 → YouTube赚钱")
    logger.info("="*60)
    logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "seedance_register": None,
        "seedance_generate": None,
        "youtube_upload": None
    }

    if input("是否注册 Seedance? (y/n): ").lower() == 'y':
        results["seedance_register"] = run_seedance_register()

    if input("是否生成视频? (y/n): ").lower() == 'y':
        prompt = input("输入视频提示词 (留空使用随机): ").strip() or None
        style = input("选择风格 (cinematic/animation/cartoon): ").strip() or "cinematic"
        results["seedance_generate"] = run_seedance_generate(prompt, style)

    video_path = input("请输入视频路径 (留空使用刚生成的): ").strip()
    if not video_path and results["seedance_generate"]:
        video_path = results["seedance_generate"]

    if video_path:
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
        else:
            title = input("视频标题 (留空使用默认): ").strip() or None
            description = input("视频描述 (留空使用默认): ").strip() or None
            tags_input = input("标签 (逗号分隔, 留空使用默认): ").strip()
            tags = tags_input.split(",") if tags_input else None
            results["youtube_upload"] = run_youtube_upload(video_path, title, description, tags)
    else:
        logger.info("没有视频，跳过上传")

    logger.info("="*60)
    logger.info("📊 执行结果汇总")
    logger.info("="*60)
    for task, status in results.items():
        if status is None:
            icon = "⏭️ "
            text = "跳过"
        elif status:
            icon = "✅"
            text = "成功"
        else:
            icon = "❌"
            text = "失败"
        logger.info(f"  {icon} {task}: {text}")
    logger.info(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Auto Content Factory - 自动化内容工厂",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --mode full              # 完整流程 (交互模式)
  python main.py --mode register          # 仅注册 Seedance
  python main.py --mode generate          # 仅生成视频
  python main.py --mode upload --video path/to/video.mp4  # 仅上传 YouTube

示例:
  python main.py --mode generate --prompt "A sunset over mountains"
  python main.py --mode upload --video ./output.mp4 --title "My AI Video"
        """
    )

    parser.add_argument(
        "--mode",
        choices=["full", "register", "generate", "upload"],
        default="full",
        help="运行模式"
    )
    parser.add_argument("--video", help="视频文件路径 (upload模式必需)")
    parser.add_argument("--prompt", help="视频生成提示词 (generate模式)")
    parser.add_argument("--style", default="cinematic", help="视频风格")
    parser.add_argument("--title", help="YouTube视频标题")
    parser.add_argument("--description", help="YouTube视频描述")
    parser.add_argument("--tags", help="YouTube视频标签 (逗号分隔)")

    args = parser.parse_args()

    setup_directories()

    if args.mode == "full":
        run_full_pipeline()

    elif args.mode == "register":
        success = run_seedance_register()
        sys.exit(0 if success else 1)

    elif args.mode == "generate":
        video_path = run_seedance_generate(args.prompt, args.style)
        if video_path:
            print(f"\n✅ 视频已生成: {video_path}")
            sys.exit(0)
        else:
            print("\n❌ 视频生成失败")
            sys.exit(1)

    elif args.mode == "upload":
        if not args.video:
            logger.error("upload 模式需要指定 --video 参数")
            sys.exit(1)

        if not os.path.exists(args.video):
            logger.error(f"视频文件不存在: {args.video}")
            sys.exit(1)

        tags = args.tags.split(",") if args.tags else None
        success = run_youtube_upload(args.video, args.title, args.description, tags)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
