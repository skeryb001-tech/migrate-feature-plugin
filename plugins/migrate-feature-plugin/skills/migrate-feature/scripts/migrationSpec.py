#!/usr/bin/env python3
"""增强迁移报告的单一机器规范源。"""

from __future__ import annotations

import re
from typing import TypedDict


class PlatformSpec(TypedDict):
    """目标平台的运行时视觉约束。"""

    title: str
    runtime_surfaces: list[str]
    runtime_units: list[str]
    runtime_patterns: list[str]
    runtime_unit_patterns: dict[str, list[str]]


CHECKPOINTS = [
    (
        "C1",
        "范围",
        "真实入口、调用链、可观察结果和允许修改边界已明确",
    ),
    (
        "C2",
        "映射",
        "目标落点、复用决策、冲突和共享消费者影响已明确",
    ),
    (
        "C3",
        "等价",
        "主流程、关键分支、数据契约和适用的 UI/生命周期行为等价",
    ),
    (
        "C4",
        "证据",
        "相关检查、未验证项、残余风险和回滚起点已记录",
    ),
]


MODES = {
    "cross-project": "跨项目",
    "cross-page": "同项目跨页面或视图",
}


PLATFORMS: dict[str, PlatformSpec] = {
    "web-frontend": {
        "title": "Web 前端",
        "runtime_surfaces": ["BROWSER"],
        "runtime_units": ["CSS_PX"],
        "runtime_patterns": [
            r"\b(?:Chrome|Chromium|Firefox|WebKit|Safari|Edge)\b.*\d",
        ],
        "runtime_unit_patterns": {"CSS_PX": [r".+"]},
    },
    "hybrid-client": {
        "title": "混合客户端",
        "runtime_surfaces": ["WEBVIEW", "APP_WINDOW"],
        "runtime_units": ["CSS_PX"],
        "runtime_patterns": [
            r"\b(?:Electron|Tauri|WKWebView|Android\s+WebView|WebView2)\b.*\d",
        ],
        "runtime_unit_patterns": {"CSS_PX": [r".+"]},
    },
    "native-client": {
        "title": "原生客户端",
        "runtime_surfaces": ["SIMULATOR", "EMULATOR", "DEVICE"],
        "runtime_units": ["PT", "DP", "LOGICAL_PX"],
        "runtime_patterns": [
            r"\b(?:iOS|iPadOS|macOS|tvOS|visionOS|Android|Windows|Linux)\b.*\d",
            r"\b(?:SwiftUI|UIKit|AppKit|Jetpack\s+Compose|Android\s+Views|Flutter|React\s+Native|WinUI|WPF|\.NET\s+MAUI|Qt)\b",
        ],
        "runtime_unit_patterns": {
            "PT": [r"\b(?:SwiftUI|UIKit|AppKit)\b"],
            "DP": [r"\b(?:Jetpack\s+Compose|Android\s+Views)\b"],
            "LOGICAL_PX": [
                r"\b(?:Flutter|React\s+Native|WinUI|WPF|\.NET\s+MAUI|Qt)\b"
            ],
        },
    },
}


def specification_errors() -> list[str]:
    """返回机器规范源自身的完整性错误。"""

    errors: list[str] = []
    checkpoint_ids = [checkpoint_id for checkpoint_id, *_ in CHECKPOINTS]
    if checkpoint_ids != ["C1", "C2", "C3", "C4"]:
        errors.append("检查点必须按 C1-C4 唯一且有序定义")

    if set(MODES) != {"cross-project", "cross-page"}:
        errors.append("迁移模式必须包含且只包含 cross-project、cross-page")

    expected_platforms = {"web-frontend", "hybrid-client", "native-client"}
    if set(PLATFORMS) != expected_platforms:
        errors.append(
            "平台模式必须包含且只包含 web-frontend、hybrid-client、native-client"
        )

    for platform_name, platform_spec in PLATFORMS.items():
        if not platform_spec["runtime_surfaces"]:
            errors.append(f"{platform_name} 必须定义运行时 surface")
        if not platform_spec["runtime_units"]:
            errors.append(f"{platform_name} 必须定义视觉测量单位")
        if not platform_spec["runtime_patterns"]:
            errors.append(f"{platform_name} 必须定义运行环境匹配规则")
        if set(platform_spec["runtime_unit_patterns"]) != set(
            platform_spec["runtime_units"]
        ):
            errors.append(f"{platform_name} 的单位与单位匹配规则必须一一对应")

        patterns = list(platform_spec["runtime_patterns"])
        patterns.extend(
            pattern
            for unit_patterns in platform_spec["runtime_unit_patterns"].values()
            for pattern in unit_patterns
        )
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as error:
                errors.append(f"{platform_name} 运行环境匹配规则非法：{error}")

    return errors
