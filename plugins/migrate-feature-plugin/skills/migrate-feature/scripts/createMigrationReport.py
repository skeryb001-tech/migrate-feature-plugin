#!/usr/bin/env python3
"""为高风险或正式验收场景创建精简迁移报告。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from migrationSpec import (
    CHECKPOINTS,
    MODES,
    PARITY_MODES,
    PLATFORMS,
    specification_errors,
)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="为需要增强验收的迁移生成 C1-C4 精简报告。"
    )
    parser.add_argument("--mode", required=True, choices=sorted(MODES))
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    parser.add_argument("--source", required=True, help="源项目、页面或功能入口")
    parser.add_argument("--target", required=True, help="目标项目、页面或功能入口")
    parser.add_argument("--reason", required=True, help="升级为增强验收的原因")
    parser.add_argument(
        "--parity-mode",
        choices=sorted(PARITY_MODES),
        default="ADAPTED",
        help="一致性模式；完整/原样/一比一迁移使用 STRICT",
    )
    parser.add_argument("--output", required=True, help="输出 Markdown 文件")
    parser.add_argument(
        "--force",
        action="store_true",
        help="允许覆盖已有报告；默认保护已有报告",
    )
    return parser.parse_args()


def sanitize_value(value: str, label: str) -> str:
    """校验单行字段值。"""

    sanitized = value.strip()
    if not sanitized:
        raise ValueError(f"{label}不能为空")
    if "\n" in sanitized or "\r" in sanitized:
        raise ValueError(f"{label}必须是单行值")
    return sanitized


def render_checkpoint_rows() -> str:
    """渲染四个稳定检查点。"""

    return "\n".join(
        f"| {checkpoint_id} | {title} | TODO | TODO |"
        for checkpoint_id, title, _ in CHECKPOINTS
    )


def build_report(
    mode: str,
    platform: str,
    source: str,
    target: str,
    reason: str,
    parity_mode: str = "ADAPTED",
) -> str:
    """生成增强迁移报告正文。"""

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return f"""# 功能迁移增强验收报告

仅在高风险、跨运行时、共享公共契约或正式一比一验收场景使用。本报告不采用九阶段清单或 100 分评分。机器摘要和 C1-C4 为必填项；其余表格按实际范围填写、合并或删除。

## 0. 机器摘要

- report_schema: 3
- migration_mode: {mode}
- platform_mode: {platform}
- parity_mode: {parity_mode}
- source: {source}
- target: {target}
- generated_at_utc: {generated_at}
- enhanced_reason: {reason}
- visible_ui: TODO
- source_inventory: file=source-inventory.json
- feature_matrix: file=feature-matrix.json
- rendering_contract: file=rendering-contract.json
- route_activation: TODO
- unimplemented_items: TODO
- adapted_items: TODO
- source_baseline: TODO
- target_baseline: TODO
- target_rules: TODO
- migration_scope: TODO
- target_mapping: TODO
- blocking_issues: TODO
- runtime_required: TODO
- runtime_verified: TODO
- runtime_environment: TODO
- runtime_evidence: TODO
- visual_required: TODO
- visual_verified: TODO
- visual_surface: TODO
- visual_unit: TODO
- visual_environment: TODO
- visual_evidence: TODO
- rollback_plan: TODO
- final_conclusion: TODO

取值规则：`visible_ui`、`runtime_required` / `visual_required` 使用 `YES|NO`；对应 `verified` 使用 `YES|NO|NOT_REQUIRED`；`final_conclusion` 使用 `PASS|CODE_ONLY|BLOCKED`。严格模式的 `source_inventory` 和 `feature_matrix` 必须引用报告目录下的 JSON 证据文件；`visible_ui=YES` 时 `rendering_contract` 也必须引用 JSON 证据文件。

## 1. 范围与调用链

| 入口/状态 | 输入 | 核心处理与状态所有者 | 输出/副作用 | 源证据 | 目标证据 |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO | TODO |

## 2. 目标映射与风险

| 源职责 | 目标已有能力 | 决策 | 最终落点 | 消费者/冲突 | 证据 |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | 复用/适配/迁入/阻塞 | TODO | TODO | TODO |

| 风险或差异 | 是否阻断 | 处理 | 复验 | 残余风险 |
| --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO |

## 3. 四个检查点

状态使用 `PASS|PENDING|BLOCKED`。每项证据应包含可复现命令、调用链、运行记录、消费者搜索、截图或 diff 中的适用内容。

| ID | 检查点 | 状态 | 证据 |
| --- | --- | --- | --- |
{render_checkpoint_rows()}

## 4. 验证记录

| 层级 | 是否需要 | 方法/环境 | 结果 | 证据或阻塞原因 |
| --- | --- | --- | --- | --- |
| 静态 | TODO | TODO | TODO | TODO |
| 功能/契约 | TODO | TODO | TODO | TODO |
| 目标运行时 | TODO | TODO | TODO | TODO |
| 视觉 | TODO | TODO | TODO | TODO |
| 共享消费者 | TODO | TODO | TODO | TODO |

视觉验收仅在 `visual_required=YES` 时需要。此时固定数据、设备/视口、scale、主题、语言和字体，记录真实目标平台版本，并在 `visual_evidence` 中包含 `screenshot=`、`rendered_style=`、`viewport=` 和 `geometry=`。

## 5. 回滚与交付

| 项目 | 内容 | 验证/证据 |
| --- | --- | --- |
| 入口关闭 | TODO | TODO |
| 共享能力恢复 | TODO | TODO |
| API/bridge/权限/埋点恢复 | TODO | TODO |
| 持久化清理 | TODO | TODO |
| 用户可感知差异 | TODO | TODO |

最终说明：TODO
"""


def main() -> int:
    """创建报告并返回进程退出码。"""

    args = parse_args()
    try:
        spec_errors = specification_errors()
        if spec_errors:
            raise ValueError("机器规范源无效：" + "；".join(spec_errors))
        source = sanitize_value(args.source, "source")
        target = sanitize_value(args.target, "target")
        reason = sanitize_value(args.reason, "reason")
        output_path = Path(args.output).expanduser().resolve()
        if output_path.exists() and not args.force:
            raise FileExistsError(
                f"输出文件已存在：{output_path}；确认覆盖后再使用 --force"
            )
        if not output_path.parent.exists():
            raise FileNotFoundError(f"输出目录不存在：{output_path.parent}")
        output_path.write_text(
            build_report(
                args.mode,
                args.platform,
                source,
                target,
                reason,
                args.parity_mode,
            ),
            encoding="utf-8",
        )
    except (OSError, ValueError) as error:
        print(f"创建报告失败：{error}", file=sys.stderr)
        return 1

    print(f"已创建增强迁移报告：{output_path}")
    print(f"迁移模式：{args.mode}")
    print(f"平台模式：{args.platform}")
    print(f"一致性模式：{args.parity_mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
