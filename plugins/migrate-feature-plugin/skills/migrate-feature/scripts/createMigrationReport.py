#!/usr/bin/env python3
"""创建可被自动校验的前端功能迁移报告。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


SCORE_ITEMS = [
    ("S01", "静态代码", "语法与类型", 4),
    ("S02", "静态代码", "lint、格式与工程检查", 3),
    ("S03", "静态代码", "路径、命名、导出与自动导入冲突", 4),
    ("S04", "静态代码", "残留引用、shim 与死代码", 2),
    ("S05", "静态代码", "目标规范、结构与无关改动", 2),
    ("F01", "功能逻辑", "主流程", 10),
    ("F02", "功能逻辑", "关键分支与失败分支", 8),
    ("F03", "功能逻辑", "API 与数据契约", 6),
    ("F04", "功能逻辑", "状态、缓存与恢复", 4),
    ("F05", "功能逻辑", "权限、支付与实验", 3),
    ("F06", "功能逻辑", "埋点与副作用次数", 4),
    ("U01", "视觉还原", "结构与内容", 5),
    ("U02", "视觉还原", "盒模型与响应式", 7),
    ("U03", "视觉还原", "颜色、透明度与视觉 token", 6),
    ("U04", "视觉还原", "交互与无障碍", 5),
    ("U05", "视觉还原", "全部关键 UI 状态", 5),
    ("U06", "视觉还原", "动效与资源", 2),
    ("B01", "边界场景", "空数据与极端数据", 3),
    ("B02", "边界场景", "异常与网络边界", 4),
    ("B03", "边界场景", "重复、并发与取消", 3),
    ("B04", "边界场景", "导航、刷新与恢复", 3),
    ("B05", "边界场景", "设备、主题与 i18n", 2),
    ("A01", "归档完整", "能力、文件映射与风险", 2),
    ("A02", "归档完整", "验证证据与客观评分", 2),
    ("A03", "归档完整", "差异、回滚与后续项", 1),
]


GATES = [
    ("G0", "准入门禁"),
    ("G1", "资产门禁"),
    ("G2", "冲突门禁"),
    ("G3", "目标结构与规范门禁"),
    ("G4", "底层能力门禁"),
    ("G5", "逻辑门禁"),
    ("G6", "UI 门禁"),
    ("G7", "共享消费者门禁"),
    ("G8", "验收门禁"),
    ("G9", "归档与回滚门禁"),
]


MODE_CHECKLISTS = {
    "cross-project": [
        "两个工程及相关 package 的规范、框架、版本和 package 边界已对比",
        "包管理器、锁文件、依赖、别名、环境变量和构建配置已对比",
        "请求层、鉴权、数据契约、错误格式和运行时配置已适配目标",
        "目标 UI 系统、设计 token、i18n、资源和现有依赖已优先复用",
        "迁入代码按目标目录、模块分层、命名和测试结构落盘",
        "monorepo 反向依赖、共享消费者、生产构建和 SSR 已回归",
        "资产许可、公开配置和 secret 边界已确认",
    ],
    "cross-page": [
        "源页面迁移后需保留或替换的行为边界已明确并回归",
        "params、query、hash、layout、middleware、page meta 与 keep-alive 已对比",
        "组件私有、页面私有、会话共享和全局状态边界已记录",
        "A→B→A、前进后退、刷新、不同业务 id 和并行页面已验证",
        "修改共享模块前已扫描全部直接、间接、动态和自动导入消费者",
        "watcher、轮询、计时器、请求、observer 和事件监听会在离开后清理",
        "源页面、目标页面和关键既有消费者已完成聚焦回归",
    ],
}


COMMON_STAGE_CHECKLISTS = [
    ("阶段一：梳理盘点", [
        "真实调用链、UI 状态矩阵、目标复用候选和风险清单已完成",
        "源职责到目标目录/分层的预映射与冲突扫描已完成",
    ]),
    ("阶段二：环境准备", [
        "生效规范、包管理器、依赖、配置、验证条件和回滚方式已确认",
        "P0 为 0，当前阶段 P1 为 0",
    ]),
    ("阶段三：底层能力落地", [
        "已按复用、适配、迁入、阻塞顺序处理底层能力",
        "类型、API、状态、UI 基础能力和资源可独立验证",
    ]),
    ("阶段四：业务逻辑落地", [
        "输入输出、状态机、请求时序、异常、权限和埋点与源一致",
        "没有重复请求、订阅、计时器、写入或埋点",
    ]),
    ("阶段五：页面与功能复刻", [
        "全部关键 UI 状态、交互、响应式和动效已实现",
        "UI 结果以源为准，组件、token、i18n 和样式规范以目标为准",
    ]),
    ("阶段六：差异化适配", [
        "最终目录、分层、文件名和代码风格符合目标项目",
        "同名文件未覆盖，重命名后全部引用与自动导入已更新",
    ]),
    ("阶段七：多层校验", [
        "静态、功能、视觉、边界、副作用和消费者回归已执行",
        "每个结果都有可复现证据",
    ]),
    ("阶段八：回归验收", [
        "评分只基于证据，未验证项为 0 分，部分得分仅限已接受 P2",
        "总分和全部硬门禁满足交付要求",
    ]),
    ("阶段九：归档沉淀", [
        "映射、风险、命令、证据、差异、评分和回滚均可追溯",
        "报告不包含密钥、token、cookie 或生产敏感数据",
    ]),
]


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="生成 cross-project 或 cross-page 模式的迁移报告模板。"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=sorted(MODE_CHECKLISTS),
        help="迁移模式",
    )
    parser.add_argument("--source", required=True, help="源项目、页面或功能路径")
    parser.add_argument("--target", required=True, help="目标项目、页面或功能路径")
    parser.add_argument("--output", required=True, help="输出 Markdown 文件")
    parser.add_argument(
        "--force",
        action="store_true",
        help="允许覆盖已有报告；默认禁止覆盖",
    )
    return parser.parse_args()


def sanitize_value(value: str, label: str) -> str:
    """校验单行字段值。

    @param value: 原始字段值。
    @param label: 字段名称。
    @returns: 去除首尾空白后的值。
    """

    sanitized = value.strip()
    if not sanitized:
        raise ValueError(f"{label}不能为空")
    if "\n" in sanitized or "\r" in sanitized:
        raise ValueError(f"{label}必须是单行值")
    return sanitized


def render_checklist(items: list[str]) -> str:
    """渲染 Markdown Checklist。"""

    return "\n".join(f"- [ ] {item}" for item in items)


def render_stage_checklists() -> str:
    """渲染九阶段共同 Checklist。"""

    sections: list[str] = []
    for heading, items in COMMON_STAGE_CHECKLISTS:
        sections.append(f"### {heading}\n\n{render_checklist(items)}")
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


def build_report(mode: str, source: str, target: str) -> str:
    """生成报告正文。

    @param mode: 迁移模式。
    @param source: 源路径。
    @param target: 目标路径。
    @returns: Markdown 报告。
    """

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    mode_title = "跨项目专项 Checklist" if mode == "cross-project" else "跨页面专项 Checklist"
    mode_checklist = render_checklist(MODE_CHECKLISTS[mode])

    return f"""# 前端功能迁移报告

本报告由脚本生成。完成所有 Checklist，把占位值替换为真实结论，并保留可复现证据后再运行校验脚本。

## 0. 机器校验摘要

- migration_mode: {mode}
- source: {source}
- target: {target}
- generated_at_utc: {generated_at}
- source_baseline: TODO
- target_baseline: TODO
- visual_baseline: TODO
- target_rules: TODO
- target_structure_mapping: TODO
- rollback_start_commit: TODO
- rollback_entry_disable: TODO
- rollback_shared_modules: TODO
- rollback_api_analytics: TODO
- rollback_cache_cleanup: TODO
- p0_open: TODO
- p1_open: TODO
- accepted_p2: TODO
- total_score: TODO
- final_conclusion: TODO

固定优先级：源行为一致 → 目标能力复用 → 目标规范与代码结构 → 仅在兼容时参考源结构与文件名。

## 1. 范围、基线与准入

- [ ] 源与目标路径、入口、范围和只读/可写边界明确
- [ ] 源逻辑、功能、交互和 UI 的权威基准明确
- [ ] 目标生效规范、目录结构、模块分层和命名规则已读取
- [ ] 目标已有能力、同类实现和工作区已有改动已盘点
- [ ] API、权限、数据、埋点、缓存、持久化和依赖边界明确
- [ ] 回滚方案可在不破坏目标既有能力的前提下执行

| 项目 | 内容 | 证据 |
| --- | --- | --- |
| 迁移范围 | TODO | TODO |
| 不迁移范围 | TODO | TODO |
| 源运行基准 | TODO | TODO |
| 目标运行入口 | TODO | TODO |
| 允许修改范围 | TODO | TODO |

## 2. 调用链与 UI 状态

| 编号 | 触发/状态 | 输入 | 核心处理 | 输出/副作用 | 源证据 | 目标证据 |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | TODO | TODO | TODO | TODO | TODO | TODO |

| 编号 | 视口/主题/语言 | UI 状态 | 关键结构与盒模型 | 交互 | 源证据 | 目标证据 |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | TODO | TODO | TODO | TODO | TODO | TODO |

## 3. 能力、目录与消费者映射

| 源职责/路径 | 目标已有能力 | 策略 | 最终目标路径 | 目标规范依据 | 消费者与兼容证据 |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | 复用/适配/迁入/阻塞 | TODO | TODO | TODO |

同名文件只能复用、最小合并或语义化重命名，禁止覆盖。最终目录、模块分层、文件名和代码风格必须以目标项目为准。

## 4. {mode_title}

{mode_checklist}

专项证据：TODO

## 5. 九阶段 Checklist

{render_stage_checklists()}

## 6. 风险与差异

| 编号 | 等级 | 风险或差异 | 证据 | 处理 | 状态 | 复验 |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | TODO | TODO | TODO | TODO | TODO | TODO |

## 7. 验证矩阵

| 编号 | 层级 | 方法/命令/环境 | 预期 | 结果 | 证据 |
| --- | --- | --- | --- | --- | --- |
| V1 | 静态 | TODO | 目标项目新增错误为 0 | TODO | TODO |
| V2 | 功能 | TODO | 主流程和关键分支与源一致 | TODO | TODO |
| V3 | 视觉 | TODO | 达到默认 UI 误差要求 | TODO | TODO |
| V4 | 边界 | TODO | 空、错、慢、并发、导航行为一致 | TODO | TODO |
| V5 | 消费者 | TODO | 目标既有消费者无新增回归 | TODO | TODO |

## 8. 硬门禁

状态只能填写 PASS 或 FAIL。证据必须是命令、测试、截图、调用链、diff 或可复现说明。

| ID | 门禁 | 状态 | 证据 |
| --- | --- | --- | --- |
{render_gate_rows()}

## 9. 客观评分

状态只能填写 PASS、PARTIAL、FAIL、UNVERIFIED 或 N/A。

- PASS：得满分并提供证据。
- PARTIAL：仅限用户已接受的 P2；证据使用“P2-编号; accepted=是; 证据”格式。
- FAIL 或 UNVERIFIED：必须为 0 分，最终校验不通过。
- N/A：必须为 0 分，证据使用“N/A: 原因; evidence=证明材料”格式。

| ID | 类别 | 评分项 | 满分 | 状态 | 得分 | 证据 |
| --- | --- | --- | ---: | --- | ---: | --- |
{render_score_rows()}

## 10. 回滚方案

- [ ] 起始提交和本次改动边界可定位
- [ ] 新路由、页面入口、菜单或开关可关闭
- [ ] 公共组件、store、composable、service、type 和导出可恢复
- [ ] API、权限、实验和埋点可恢复
- [ ] 缓存、storage、IndexedDB 和持久化数据有安全清理步骤
- [ ] 回滚不会删除目标原有数据、文件或用户改动

回滚演练或静态验证证据：TODO

## 11. 最终归档

- [ ] 改动文件、源到目标映射和重命名记录完整
- [ ] P0/P1/P2、差异、跳过项和残余风险完整
- [ ] 验证命令、环境、结果、截图和评分证据完整
- [ ] 用户可感知影响、共享消费者和性能影响完整
- [ ] 报告不包含密钥、cookie、token、个人数据或生产敏感响应

最终结论与交付说明：TODO
"""


def main() -> int:
    """创建报告并返回进程退出码。"""

    args = parse_args()
    try:
        source = sanitize_value(args.source, "source")
        target = sanitize_value(args.target, "target")
        output_path = Path(args.output).expanduser().resolve()
        if output_path.exists() and not args.force:
            raise FileExistsError(
                f"输出文件已存在：{output_path}；确认覆盖后再使用 --force"
            )
        if not output_path.parent.exists():
            raise FileNotFoundError(f"输出目录不存在：{output_path.parent}")
        report = build_report(args.mode, source, target)
        output_path.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"创建报告失败：{error}", file=sys.stderr)
        return 1

    print(f"已创建迁移报告：{output_path}")
    print(f"迁移模式：{args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
