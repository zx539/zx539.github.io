#!/usr/bin/env python3
"""Create a draft in the repository, without requiring Hugo or third-party packages."""

import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BEIJING = timezone(timedelta(hours=8))


def parse_date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except ValueError as error:
        raise argparse.ArgumentTypeError("日期格式应为 YYYY-MM-DD，例如 2026-10-30") from error


def create_draft(kind, day, slug=None, title=None):
    if kind == "weekly":
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        path = ROOT / "content" / "weekly" / f"{start.isoformat()}.md"
        title = title or f"周报：{start:%Y.%m.%d}—{end:%Y.%m.%d}"
        day = start
        body = """## 工作成果

<!-- 本周完成了什么？附上项目、代码或文章链接。 -->

## 学习记录

<!-- 可以按日期记录：学到了什么，如何实践，有哪些收获？ -->

## 健身日记

<!-- 可以按日期记录训练内容、运动感受和恢复情况。 -->

## 问题与复盘

<!-- 遇到了哪些问题？下次准备怎样调整？ -->

## 下周计划

- [ ]
"""
        extra = ""
    else:
        if not slug or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("博客和每日一景需要名称，请使用小写英文、数字和连字符，例如 weekend-walk")
        if kind == "photo":
            path = ROOT / "content" / "photos" / f"{day.isoformat()}-{slug}" / "index.md"
            title = title or f"每日一景：{day:%Y.%m.%d}"
            extra = 'cover: ""\ncover_alt: ""\n'
            body = """<!-- 将照片复制到当前文件夹，设置 cover 为封面文件名，并填写标题、摘要和图片描述。 -->
<!-- cover 留空时，使用当前文件夹中按文件名排序的第一张图片。 -->

写下这一天的风景与故事。

<!-- 在下方添加照片，例如：![傍晚的天空](sky.jpg) -->
<!-- 每张照片都需要在正文中用 Markdown 引用，才会出现在完整图文中。 -->
"""
        else:
            path = ROOT / "content" / "posts" / f"{slug}.md"
            title = title or slug.replace("-", " ")
            extra = "tags: []\n"
            body = "写下你的经验与思考。\n"
    header = (
        "---\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f'date: "{day.isoformat()}T00:00:00+08:00"\n'
        "draft: true\n"
        'summary: ""\n'
        f"{extra}---\n\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(header + body)
    return path


def main():
    parser = argparse.ArgumentParser(description="新建周报、每日一景或博客 Markdown 草稿")
    parser.add_argument("kind", choices=("weekly", "photo", "post"))
    parser.add_argument("slug", nargs="?", help="博客或每日一景的英文名称；周报不需要")
    parser.add_argument("--date", type=parse_date, default=datetime.now(BEIJING).date(), help="记录日期，默认北京时间今天；周报自动归到该周周一")
    parser.add_argument("--title", help="自定义标题")
    args = parser.parse_args()
    if args.kind == "weekly" and args.slug:
        parser.error("周报无需名称，请使用 --date 指定所属周")
    try:
        path = create_draft(args.kind, args.date, args.slug, args.title)
    except FileExistsError:
        parser.exit(1, "文件已存在，已保留原内容；请直接编辑现有文件。\n")
    except ValueError as error:
        parser.error(str(error))
    print(f"已创建：{path.relative_to(ROOT)}")
    print("填写内容后，将 draft 改为 false，再构建并发布网站。")


if __name__ == "__main__":
    main()
