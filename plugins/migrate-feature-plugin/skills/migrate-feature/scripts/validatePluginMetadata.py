#!/usr/bin/env python3
"""校验插件 manifest、Marketplace 注册和 README 版本是否一致。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


# scripts -> migrate-feature -> skills -> migrate-feature-plugin -> plugins -> repo
ROOT = Path(__file__).resolve().parents[5]
PLUGIN_ROOT = ROOT / "plugins" / "migrate-feature-plugin"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
README_PATH = ROOT / "README.md"


def read_json(path: Path) -> dict[str, Any]:
    """读取 JSON 对象。"""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} 顶层必须是 JSON 对象")
    return value


def validate() -> list[str]:
    """返回元数据不一致项。"""

    errors: list[str] = []
    try:
        manifest = read_json(MANIFEST_PATH)
        marketplace = read_json(MARKETPLACE_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"读取元数据失败：{error}"]

    plugin_name = manifest.get("name")
    plugin_version = manifest.get("version")
    if not isinstance(plugin_name, str) or not plugin_name.strip():
        errors.append("plugin.json 缺少有效 name")
    if not isinstance(plugin_version, str) or not re.fullmatch(
        r"\d+\.\d+\.\d+", plugin_version
    ):
        errors.append("plugin.json version 必须是三段式版本号")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        errors.append("marketplace.json 缺少 plugins 数组")
        plugins = []

    registration = next(
        (
            item
            for item in plugins
            if isinstance(item, dict) and item.get("name") == plugin_name
        ),
        None,
    )
    if registration is None:
        errors.append(f"Marketplace 未注册插件：{plugin_name}")
    else:
        source = registration.get("source")
        if not isinstance(source, dict) or source.get("source") != "local":
            errors.append("Marketplace 插件 source 必须是 local")
        elif source.get("path") != "./plugins/migrate-feature-plugin":
            errors.append("Marketplace 插件 source.path 与插件目录不一致")

    skills_path = PLUGIN_ROOT / str(manifest.get("skills", ""))
    if not skills_path.is_dir():
        errors.append(f"插件 skills 路径不存在：{skills_path}")

    try:
        readme = README_PATH.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"读取 README 失败：{error}")
    else:
        readme_version = re.search(r"当前版本：`([^`]+)`", readme)
        if readme_version is None:
            errors.append("README 缺少当前版本")
        elif readme_version.group(1) != plugin_version:
            errors.append(
                "README 版本与 plugin.json 不一致："
                f"{readme_version.group(1)} != {plugin_version}"
            )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"插件元数据校验失败，共 {len(errors)} 项：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("插件元数据校验通过：manifest、Marketplace、skills 路径和 README 版本一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
