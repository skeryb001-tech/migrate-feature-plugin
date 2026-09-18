#!/usr/bin/env python3
"""校验增强迁移报告的四个检查点和条件式运行时证据。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from migrationSpec import (
    CHECKPOINTS,
    MODES,
    PARITY_MODES,
    PLATFORMS,
    specification_errors,
)


REQUIRED_FIELDS = {
    "report_schema",
    "migration_mode",
    "platform_mode",
    "parity_mode",
    "source",
    "target",
    "generated_at_utc",
    "enhanced_reason",
    "source_inventory",
    "feature_matrix",
    "route_activation",
    "unimplemented_items",
    "adapted_items",
    "source_baseline",
    "target_baseline",
    "target_rules",
    "migration_scope",
    "target_mapping",
    "blocking_issues",
    "runtime_required",
    "runtime_verified",
    "runtime_environment",
    "runtime_evidence",
    "visual_required",
    "visual_verified",
    "visual_surface",
    "visual_unit",
    "visual_environment",
    "visual_evidence",
    "rollback_plan",
    "final_conclusion",
}

PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD)\b|<[^>]+>", re.IGNORECASE)
VISUAL_EVIDENCE_KEYS = ("screenshot=", "rendered_style=", "viewport=", "geometry=")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验增强迁移报告")
    parser.add_argument("report", help="待校验的 Markdown 报告")
    return parser.parse_args()


def parse_fields(content: str) -> dict[str, str]:
    """提取机器摘要中的单行字段。"""

    fields: dict[str, str] = {}
    for match in re.finditer(r"^- ([a-z][a-z0-9_]*):\s*(.*)$", content, re.MULTILINE):
        fields[match.group(1)] = match.group(2).strip()
    return fields


def split_markdown_row(line: str) -> list[str] | None:
    """拆分简单 Markdown 表格行。"""

    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def has_evidence(value: str) -> bool:
    """判断字段是否包含非占位内容。"""

    stripped = value.strip()
    return bool(stripped) and not PLACEHOLDER_PATTERN.search(stripped)


def starts_with_evidence_kind(value: str, kind: str) -> bool:
    return value.strip().upper().startswith(f"{kind}:") and "evidence=" in value.lower()


def parse_yes_no(value: str, field_name: str, errors: list[str]) -> bool | None:
    normalized = value.strip().upper()
    if normalized == "YES":
        return True
    if normalized == "NO":
        return False
    errors.append(f"{field_name} 必须为 YES 或 NO")
    return None


def parse_verified(
    value: str,
    field_name: str,
    errors: list[str],
) -> str:
    normalized = value.strip().upper()
    if normalized not in {"YES", "NO", "NOT_REQUIRED"}:
        errors.append(f"{field_name} 必须为 YES、NO 或 NOT_REQUIRED")
    return normalized


def validate_checkpoints(content: str, errors: list[str]) -> None:
    """校验 C1-C4 唯一、文本稳定且完成。"""

    expected = {checkpoint_id: title for checkpoint_id, title, _ in CHECKPOINTS}
    rows: dict[str, list[str]] = {}
    duplicates: set[str] = set()
    for line in content.splitlines():
        cells = split_markdown_row(line)
        if not cells or cells[0] not in expected:
            continue
        if cells[0] in rows:
            duplicates.add(cells[0])
        rows[cells[0]] = cells

    if duplicates:
        errors.append("检查点重复：" + ", ".join(sorted(duplicates)))

    for checkpoint_id, title, _ in CHECKPOINTS:
        cells = rows.get(checkpoint_id)
        if cells is None:
            errors.append(f"缺少检查点：{checkpoint_id}")
            continue
        if len(cells) != 4:
            errors.append(f"{checkpoint_id} 表格列数错误，应为 4 列")
            continue
        if cells[1] != title:
            errors.append(f"{checkpoint_id} 标题被修改")
        if cells[2].upper() != "PASS":
            errors.append(f"{checkpoint_id} 尚未通过：{cells[2]!r}")
        if not has_evidence(cells[3]):
            errors.append(f"{checkpoint_id} 缺少有效证据")


def validate_runtime(
    fields: dict[str, str],
    platform: str,
    errors: list[str],
) -> bool:
    """校验条件式运行时字段，返回是否仍待运行时验证。"""

    required = parse_yes_no(fields.get("runtime_required", ""), "runtime_required", errors)
    verified = parse_verified(fields.get("runtime_verified", ""), "runtime_verified", errors)
    environment = fields.get("runtime_environment", "").strip()
    evidence = fields.get("runtime_evidence", "").strip()

    if required is False:
        if verified != "NOT_REQUIRED":
            errors.append("runtime_required=NO 时 runtime_verified 必须为 NOT_REQUIRED")
        if environment.upper() != "NOT_REQUIRED":
            errors.append("不需要运行时验证时 runtime_environment 必须为 NOT_REQUIRED")
        if not starts_with_evidence_kind(evidence, "NOT_REQUIRED"):
            errors.append("不需要运行时验证时须说明原因并提供 evidence")
        return False

    if required is True and verified == "YES":
        if not has_evidence(environment):
            errors.append("runtime_environment 缺少真实运行环境")
        if not has_evidence(evidence):
            errors.append("runtime_evidence 缺少运行记录")
        return False

    if required is True and verified == "NO":
        if environment.upper() != "UNVERIFIED":
            errors.append("运行时待验证时 runtime_environment 必须为 UNVERIFIED")
        if not starts_with_evidence_kind(evidence, "UNVERIFIED"):
            errors.append("运行时待验证时须说明阻塞原因并提供 evidence")
        return True

    if required is True and verified == "NOT_REQUIRED":
        errors.append("runtime_required=YES 时 runtime_verified 不能为 NOT_REQUIRED")
    return False


def validate_visual(
    fields: dict[str, str],
    platform: str,
    errors: list[str],
) -> bool:
    """校验条件式视觉字段，返回是否仍待视觉验证。"""

    required = parse_yes_no(fields.get("visual_required", ""), "visual_required", errors)
    verified = parse_verified(fields.get("visual_verified", ""), "visual_verified", errors)
    surface = fields.get("visual_surface", "").strip().upper()
    unit = fields.get("visual_unit", "").strip().upper()
    environment = fields.get("visual_environment", "").strip()
    evidence = fields.get("visual_evidence", "").strip()

    if required is False:
        for field_name, value in (
            ("visual_surface", surface),
            ("visual_unit", unit),
            ("visual_environment", environment.upper()),
        ):
            if value != "NOT_REQUIRED":
                errors.append(f"不需要视觉验证时 {field_name} 必须为 NOT_REQUIRED")
        if verified != "NOT_REQUIRED":
            errors.append("visual_required=NO 时 visual_verified 必须为 NOT_REQUIRED")
        if not starts_with_evidence_kind(evidence, "NOT_REQUIRED"):
            errors.append("不需要视觉验证时须说明原因并提供 evidence")
        return False

    if required is True and verified == "NO":
        for field_name, value in (
            ("visual_surface", surface),
            ("visual_unit", unit),
            ("visual_environment", environment.upper()),
        ):
            if value != "UNVERIFIED":
                errors.append(f"视觉待验证时 {field_name} 必须为 UNVERIFIED")
        if not starts_with_evidence_kind(evidence, "UNVERIFIED"):
            errors.append("视觉待验证时须说明阻塞原因并提供 evidence")
        return True

    if required is True and verified == "YES":
        if platform in PLATFORMS:
            platform_spec = PLATFORMS[platform]
            if surface not in platform_spec["runtime_surfaces"]:
                errors.append(
                    f"{platform} 的 visual_surface 必须为 "
                    + "、".join(platform_spec["runtime_surfaces"])
                )
            if unit not in platform_spec["runtime_units"]:
                errors.append(
                    f"{platform} 的 visual_unit 必须为 "
                    + "、".join(platform_spec["runtime_units"])
                )
            else:
                patterns = platform_spec["runtime_unit_patterns"][unit]
                if not any(re.search(pattern, environment, re.IGNORECASE) for pattern in patterns):
                    errors.append(f"visual_unit={unit} 与运行环境/UI 框架不匹配")
            for pattern in platform_spec["runtime_patterns"]:
                if not re.search(pattern, environment, re.IGNORECASE):
                    errors.append(f"visual_environment 不符合 {platform} 的真实运行环境要求")
        if not all(key in evidence.lower() for key in VISUAL_EVIDENCE_KEYS):
            errors.append(
                "visual_evidence 必须包含 screenshot、rendered_style、viewport 和 geometry"
            )
        return False

    if required is True and verified == "NOT_REQUIRED":
        errors.append("visual_required=YES 时 visual_verified 不能为 NOT_REQUIRED")
    return False


def parse_non_negative_int(value: str, field_name: str, errors: list[str]) -> int:
    """解析严格迁移的非负计数字段。"""

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} 必须为非负整数")
        return -1
    if parsed < 0:
        errors.append(f"{field_name} 必须为非负整数")
        return -1
    return parsed


def validate_parity(fields: dict[str, str], errors: list[str]) -> tuple[bool, int]:
    """校验适配/严格一致性字段，返回待补路由证据和未实现项数量。"""

    parity_mode = fields.get("parity_mode", "").strip().upper()
    if parity_mode not in PARITY_MODES:
        errors.append("parity_mode 必须为 ADAPTED 或 STRICT")
        return False, -1

    unimplemented_items = parse_non_negative_int(
        fields.get("unimplemented_items", ""), "unimplemented_items", errors
    )
    parse_non_negative_int(fields.get("adapted_items", ""), "adapted_items", errors)

    if parity_mode != "STRICT":
        return False, unimplemented_items

    for field_name in ("source_inventory", "feature_matrix"):
        if not has_evidence(fields.get(field_name, "")):
            errors.append(f"严格模式字段 {field_name} 缺少源依赖闭包或功能矩阵证据")

    route_activation = fields.get("route_activation", "").strip().upper()
    if route_activation not in {"PASS", "PENDING", "BLOCKED"}:
        errors.append("严格模式 route_activation 必须为 PASS、PENDING 或 BLOCKED")
    if route_activation == "BLOCKED":
        errors.append("严格模式目标入口未激活或路由存在阻断项")
    if unimplemented_items > 0:
        errors.append(f"严格模式仍有 {unimplemented_items} 个未实现项")
    return route_activation == "PENDING", unimplemented_items


def validate_report(content: str) -> tuple[list[str], bool]:
    """返回校验错误及是否为合法 CODE_ONLY。"""

    errors = specification_errors()
    fields = parse_fields(content)

    missing_fields = sorted(REQUIRED_FIELDS - set(fields))
    if missing_fields:
        errors.append("缺少机器字段：" + ", ".join(missing_fields))

    for field_name in REQUIRED_FIELDS & set(fields):
        occurrences = len(
            re.findall(
                rf"^- {re.escape(field_name)}:",
                content,
                flags=re.MULTILINE,
            )
        )
        if occurrences > 1:
            errors.append(f"机器字段重复：{field_name}")
        if not has_evidence(fields[field_name]):
            errors.append(f"机器字段仍为空或包含占位符：{field_name}")

    if fields.get("report_schema") != "2":
        errors.append("report_schema 必须为 2")

    mode = fields.get("migration_mode", "")
    if mode not in MODES:
        errors.append(f"migration_mode 非法：{mode!r}")
    platform = fields.get("platform_mode", "")
    if platform not in PLATFORMS:
        errors.append(f"platform_mode 非法：{platform!r}")

    for field_name in ("source", "target", "enhanced_reason", "migration_scope", "target_mapping"):
        if not has_evidence(fields.get(field_name, "")):
            errors.append(f"{field_name} 缺少明确内容")
    for field_name in ("source", "target"):
        if fields.get(field_name, "").strip().upper() in {"N/A", "NOT_REQUIRED"}:
            errors.append(f"{field_name} 必须是明确路径或入口")

    try:
        blocking_issues = int(fields.get("blocking_issues", ""))
        if blocking_issues < 0:
            raise ValueError
    except ValueError:
        blocking_issues = -1
        errors.append("blocking_issues 必须为非负整数")

    validate_checkpoints(content, errors)
    parity_pending, unimplemented_items = validate_parity(fields, errors)
    runtime_pending = validate_runtime(fields, platform, errors)
    visual_pending = validate_visual(fields, platform, errors)
    if (
        fields.get("visual_required", "").strip().upper() == "YES"
        and fields.get("runtime_required", "").strip().upper() != "YES"
    ):
        errors.append("visual_required=YES 时 runtime_required 也必须为 YES")
    pending = parity_pending or runtime_pending or visual_pending

    conclusion = fields.get("final_conclusion", "").strip().upper()
    if conclusion not in {"PASS", "CODE_ONLY", "BLOCKED"}:
        errors.append("final_conclusion 必须为 PASS、CODE_ONLY 或 BLOCKED")
    elif unimplemented_items > 0:
        if conclusion != "BLOCKED":
            errors.append("严格模式存在未实现项时 final_conclusion 必须为 BLOCKED")
    elif blocking_issues > 0:
        if conclusion != "BLOCKED":
            errors.append("存在阻断项时 final_conclusion 必须为 BLOCKED")
        errors.append(f"仍有 {blocking_issues} 个阻断项")
    elif pending and conclusion != "CODE_ONLY":
        errors.append("必需运行时或视觉验收待补时 final_conclusion 必须为 CODE_ONLY")
    elif not pending and blocking_issues == 0 and conclusion != "PASS":
        errors.append("无阻断且必需验证均完成时 final_conclusion 必须为 PASS")

    return errors, pending and blocking_issues == 0 and conclusion == "CODE_ONLY"


def main() -> int:
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    try:
        content = report_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"读取报告失败：{error}", file=sys.stderr)
        return 2

    errors, is_code_only = validate_report(content)
    if errors:
        print(f"增强迁移报告校验失败，共 {len(errors)} 项：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    if is_code_only:
        print(f"增强迁移报告代码级校验通过：{report_path}")
        print("必需运行时或视觉证据仍待补，结论为 CODE_ONLY。")
        return 3

    print(f"增强迁移报告校验通过：{report_path}")
    print("C1-C4、阻断项和所有必需验证均满足要求。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
