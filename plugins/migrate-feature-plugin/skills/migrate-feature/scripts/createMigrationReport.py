#!/usr/bin/env python3
"""从单一机器规范源创建 Web 与客户端功能迁移报告。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from migrationSpec import (
    GATES,
    MODES,
    PLATFORMS,
    SCORE_ITEMS,
    STAGES,
    specification_errors,
)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="生成包含完整阶段、迁移拓扑与平台 Checklist 的迁移报告。"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=sorted(MODES),
        help="迁移模式",
    )
    parser.add_argument(
        "--platform",
        required=True,
        choices=sorted(PLATFORMS),
        help="目标运行平台",
    )
    parser.add_argument("--source", required=True, help="源项目、页面或功能路径")
    parser.add_argument("--target", required=True, help="目标项目、页面或功能路径")
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


def render_checklist(checklist: list[dict[str, str]]) -> str:
    """渲染带稳定 ID 的 Checklist。"""

    return "\n".join(
        f"- [ ] [{checklist_item['id']}] {checklist_item['text']}"
        for checklist_item in checklist
    )


def render_stage_sections() -> str:
    """渲染九阶段动作、完成条件与 Checklist。"""

    sections: list[str] = []
    for index, stage in enumerate(STAGES, start=1):
        gates = "、".join(stage["gates"])
        sections.append(
            "\n".join(
                [
                    f"### {index}. {stage['title']}（{stage['id']}）",
                    "",
                    f"- 动作：{stage['action']}",
                    f"- 完成条件：{stage['completion']}",
                    f"- 对应门禁：{gates}",
                    "",
                    render_checklist(stage["checklist"]),
                ]
            )
        )
    return "\n\n".join(sections)


def render_gate_rows() -> str:
    """渲染硬门禁表格行。"""

    return "\n".join(
        f"| {gate_id} | {gate_name} | TODO | TODO |"
        for gate_id, gate_name in GATES
    )


def render_score_rows() -> str:
    """渲染计分表格行。"""

    return "\n".join(
        f"| {item_id} | {category} | {item_name} | {maximum} | "
        f"UNVERIFIED | 0 | TODO |"
        for item_id, category, item_name, maximum in SCORE_ITEMS
    )


def build_report(mode: str, platform: str, source: str, target: str) -> str:
    """生成迁移报告正文。"""

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    mode_spec = MODES[mode]
    platform_spec = PLATFORMS[platform]

    return f"""# Web 与客户端功能迁移报告

本报告由单一机器规范源生成。逐项完成并保留证据；校验脚本返回 0 才是完整 PASS，返回 3 表示代码级完成但运行时视觉待验收。

## 0. 机器校验摘要

- migration_mode: {mode}
- platform_mode: {platform}
- source: {source}
- target: {target}
- generated_at_utc: {generated_at}
- source_baseline: TODO
- target_baseline: TODO
- visual_baseline: TODO
- target_rules: TODO
- target_structure_mapping: TODO
- conflict_scan_evidence: TODO
- rollback_start_commit: TODO
- rollback_entry_disable: TODO
- rollback_shared_modules: TODO
- rollback_api_analytics: TODO
- rollback_cache_cleanup: TODO
- p0_open: TODO
- p1_open: TODO
- accepted_p2: TODO
- runtime_visual_verified: TODO
- runtime_visual_surface: TODO
- runtime_visual_environment: TODO
- runtime_visual_unit: TODO
- runtime_visual_max_error: TODO
- runtime_visual_evidence: TODO
- raw_score: TODO
- applicable_max_score: TODO
- total_score: TODO
- final_conclusion: TODO

执行锚点：行为等价（parity）→ 目标复用 → 目标优先（target-first）→ 平台原生适配 → 兼容时参考源命名。

## 1. 范围与基线

| 项目 | 内容 | 证据 |
| --- | --- | --- |
| 迁移范围 | TODO | TODO |
| 不迁移范围 | TODO | TODO |
| 源运行基准 | TODO | TODO |
| 目标运行入口 | TODO | TODO |
| 允许修改范围 | TODO | TODO |

## 2. 调用链、UI、平台与能力映射

| 编号 | 触发/状态 | 输入 | 核心处理 | 输出/副作用 | 源证据 | 目标证据 |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | TODO | TODO | TODO | TODO | TODO | TODO |

| 编号 | 运行环境/视口/主题/语言 | UI 状态 | 关键结构与几何 | 交互 | 源证据 | 目标证据 |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | TODO | TODO | TODO | TODO | TODO | TODO |

| 源职责/路径 | 目标已有能力 | 策略 | 最终目标路径 | 目标规范依据 | 消费者与兼容证据 |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | 复用/适配/迁入/阻塞 | TODO | TODO | TODO |

## 3. 九阶段执行

{render_stage_sections()}

## 4. {mode_spec['title']}

{render_checklist(mode_spec['checklist'])}

专项证据：TODO

## 5. {platform_spec['title']}

{render_checklist(platform_spec['checklist'])}

平台证据：TODO

## 6. 风险与差异

| 编号 | 等级 | 风险或差异 | 证据 | 处理 | 状态 | 复验 |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | TODO | TODO | TODO | TODO | TODO | TODO |

## 7. 验证矩阵

| 编号 | 层级 | 方法/命令/环境 | 预期 | 结果 | 证据 |
| --- | --- | --- | --- | --- | --- |
| V1 | 静态 | TODO | 迁移新增错误为 0 | TODO | TODO |
| V2 | 功能 | TODO | 主流程和关键分支行为等价 | TODO | TODO |
| V3 | 视觉 | TODO | 关键尺寸和位置误差 ≤1 逻辑显示单位 | TODO | TODO |
| V4 | 边界 | TODO | 空、错、慢、并发、导航行为等价 | TODO | TODO |
| V5 | 消费者 | TODO | 目标既有消费者无新增回归 | TODO | TODO |

## 8. 硬门禁

完整验收时门禁状态填写 PASS 或 FAIL；代码级完成时 G6、G8 必须填写 PENDING_RUNTIME，其余门禁仍必须 PASS。

| ID | 门禁 | 状态 | 证据 |
| --- | --- | --- | --- |
{render_gate_rows()}

## 9. 证据评分

状态填写 PASS、PARTIAL、FAIL、UNVERIFIED 或 N/A：

- PASS：得满分并提供证据。
- PARTIAL：仅限用户接受的 P2，得分低于满分。
- FAIL/UNVERIFIED：记 0 分并阻断验收。
- N/A：记 0 原始分，提供不适用证据，并从适用满分分母剔除。
- 运行环境缺失使用 `UNVERIFIED: 原因; evidence=阻塞证据`，不得标记 N/A。
- 归一化总分：raw_score / applicable_max_score × 100。

| ID | 类别 | 评分项 | 满分 | 状态 | 原始得分 | 证据 |
| --- | --- | --- | ---: | --- | ---: | --- |
{render_score_rows()}

## 10. 回滚与归档

| 回滚项 | 当前状态/值 | 回滚动作 | 验证方式 | 证据 |
| --- | --- | --- | --- | --- |
| 目标起始提交 | TODO | TODO | TODO | TODO |
| 路由/导航/页面/screen/window/deep link/入口 | TODO | TODO | TODO | TODO |
| 公共组件/store/view model/hook/service/bridge | TODO | TODO | TODO | TODO |
| API/IPC/权限/鉴权/实验/埋点 | TODO | TODO | TODO | TODO |
| cache/storage/数据库/文件/Keychain/Keystore | TODO | TODO | TODO | TODO |

最终结论与交付说明：TODO
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
        output_path = Path(args.output).expanduser().resolve()
        if output_path.exists() and not args.force:
            raise FileExistsError(
                f"输出文件已存在：{output_path}；确认覆盖后再使用 --force"
            )
        if not output_path.parent.exists():
            raise FileNotFoundError(f"输出目录不存在：{output_path.parent}")
        output_path.write_text(
            build_report(args.mode, args.platform, source, target),
            encoding="utf-8",
        )
    except (OSError, ValueError) as error:
        print(f"创建报告失败：{error}", file=sys.stderr)
        return 1

    print(f"已创建迁移报告：{output_path}")
    print(f"迁移模式：{args.mode}")
    print(f"平台模式：{args.platform}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
