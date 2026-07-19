#!/usr/bin/env python3
"""校验迁移报告并区分完整 PASS、CODE_ONLY 与失败。"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

from migrationSpec import (
    GATES,
    MODES,
    PLATFORMS,
    RUNTIME_VISUAL_CHECKLIST_IDS,
    RUNTIME_VISUAL_GATE_IDS,
    SCORE_ITEMS,
    STAGES,
    expected_checklist_ids,
    specification_errors,
)


REQUIRED_FIELDS = [
    "migration_mode",
    "platform_mode",
    "source",
    "target",
    "source_baseline",
    "target_baseline",
    "visual_baseline",
    "target_rules",
    "target_structure_mapping",
    "conflict_scan_evidence",
    "rollback_start_commit",
    "rollback_entry_disable",
    "rollback_shared_modules",
    "rollback_api_analytics",
    "rollback_cache_cleanup",
    "p0_open",
    "p1_open",
    "accepted_p2",
    "runtime_visual_verified",
    "runtime_visual_surface",
    "runtime_visual_environment",
    "runtime_visual_unit",
    "runtime_visual_max_error",
    "runtime_visual_evidence",
    "raw_score",
    "applicable_max_score",
    "total_score",
    "final_conclusion",
]

EVIDENCE_FIELDS = [
    "source_baseline",
    "target_baseline",
    "visual_baseline",
    "target_rules",
    "target_structure_mapping",
    "conflict_scan_evidence",
    "rollback_start_commit",
    "rollback_entry_disable",
    "rollback_shared_modules",
    "rollback_api_analytics",
    "rollback_cache_cleanup",
]

PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD)\b|待填写|待补充|<[^>]*(?:填写|补充)[^>]*>|__/\d+",
    re.IGNORECASE,
)

CHECKLIST_PATTERN = re.compile(
    r"^\s*- \[([ xX])\]\s+\[([A-Z0-9-]+)\]\s+(.+?)\s*$"
)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description=(
            "校验 createMigrationReport.py 生成的迁移报告。"
            "完整 PASS 返回 0，失败返回 1，运行时视觉待验收的 CODE_ONLY 返回 3。"
        )
    )
    parser.add_argument("report", help="待校验的 Markdown 迁移报告")
    return parser.parse_args()


def parse_fields(content: str) -> dict[str, str]:
    """解析机器校验摘要字段。"""

    fields: dict[str, str] = {}
    pattern = re.compile(r"^- ([a-z][a-z0-9_]*):\s*(.*)$", re.MULTILINE)
    for match in pattern.finditer(content):
        fields[match.group(1)] = match.group(2).strip()
    return fields


def split_markdown_row(line: str) -> list[str] | None:
    """拆分 Markdown 表格行并支持转义竖线。"""

    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None

    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for character in stripped[1:-1]:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return cells


def parse_int(value: str, label: str, errors: list[str]) -> int | None:
    """解析非负整数。"""

    try:
        parsed = int(value)
    except ValueError:
        errors.append(f"{label} 必须是非负整数，当前值：{value!r}")
        return None
    if parsed < 0:
        errors.append(f"{label} 必须是非负整数，当前值：{value!r}")
        return None
    return parsed


def parse_score(value: str, label: str, errors: list[str]) -> float | None:
    """解析非负有限分数。"""

    try:
        parsed = float(value)
    except ValueError:
        errors.append(f"{label} 必须是数字，当前值：{value!r}")
        return None
    if not math.isfinite(parsed) or parsed < 0:
        errors.append(f"{label} 必须是非负有限数字，当前值：{value!r}")
        return None
    return parsed


def has_valid_evidence(value: str) -> bool:
    """判断证据字段是否完整。"""

    stripped = value.strip()
    if not stripped or PLACEHOLDER_PATTERN.search(stripped):
        return False
    if stripped.upper().startswith("N/A"):
        return bool(
            re.match(
                r"^N/A:\s*[^;]+;\s*evidence=\s*.+$",
                stripped,
                flags=re.IGNORECASE,
            )
        )
    return len(stripped) >= 3


def has_unverified_evidence(value: str) -> bool:
    """判断待验证证据是否使用可复现格式。"""

    stripped = value.strip()
    if PLACEHOLDER_PATTERN.search(stripped):
        return False
    return bool(
        re.match(
            r"^UNVERIFIED:\s*[^;]+;\s*evidence=\s*.+$",
            stripped,
            flags=re.IGNORECASE,
        )
    )


def has_runtime_visual_evidence(value: str) -> bool:
    """判断完整视觉证据是否包含目标平台运行时信息。"""

    stripped = value.strip()
    if not has_valid_evidence(stripped) or stripped.upper().startswith("N/A"):
        return False
    required_patterns = (
        r"\bruntime\s*=",
        r"\bscreenshots?\s*=",
        r"\brendered_style\s*=",
        r"\bviewport\s*=",
        r"\bgeometry\s*=",
    )
    return all(
        re.search(pattern, stripped, flags=re.IGNORECASE)
        for pattern in required_patterns
    )


def expected_checklist_texts(mode: str, platform: str) -> dict[str, str]:
    """返回指定拓扑与平台的 Checklist 文本映射。"""

    result = {
        checklist_item["id"]: checklist_item["text"]
        for stage in STAGES
        for checklist_item in stage["checklist"]
    }
    result.update(
        {
            checklist_item["id"]: checklist_item["text"]
            for checklist_item in MODES[mode]["checklist"]
        }
    )
    result.update(
        {
            checklist_item["id"]: checklist_item["text"]
            for checklist_item in PLATFORMS[platform]["checklist"]
        }
    )
    return result


def validate_checklists(
    content: str,
    mode: str,
    platform: str,
    is_code_only: bool,
    errors: list[str],
) -> None:
    """校验完整阶段与模式 Checklist。"""

    if mode not in MODES or platform not in PLATFORMS:
        return

    expected_ids = expected_checklist_ids(mode, platform)
    expected_texts = expected_checklist_texts(mode, platform)
    rows: dict[str, tuple[bool, str]] = {}
    duplicates: set[str] = set()

    for line in content.splitlines():
        match = CHECKLIST_PATTERN.match(line)
        if not match:
            continue
        is_checked = match.group(1).lower() == "x"
        item_id = match.group(2)
        text = match.group(3).strip()
        if item_id in rows:
            duplicates.add(item_id)
        rows[item_id] = (is_checked, text)

    if duplicates:
        errors.append(f"Checklist ID 重复：{', '.join(sorted(duplicates))}")

    missing_ids = sorted(expected_ids - set(rows))
    if missing_ids:
        errors.append(f"缺少 Checklist：{', '.join(missing_ids)}")

    unexpected_ids = sorted(set(rows) - expected_ids)
    if unexpected_ids:
        errors.append(f"存在未知 Checklist ID：{', '.join(unexpected_ids)}")

    for item_id in sorted(expected_ids & set(rows)):
        is_checked, actual_text = rows[item_id]
        is_runtime_pending_item = item_id in RUNTIME_VISUAL_CHECKLIST_IDS
        if is_code_only and is_runtime_pending_item and is_checked:
            errors.append(f"待运行时视觉 Checklist 不得标记完成：{item_id}")
        elif not is_checked and not (is_code_only and is_runtime_pending_item):
            errors.append(f"Checklist 未完成：{item_id}")
        if actual_text != expected_texts[item_id]:
            errors.append(f"Checklist 文本被修改：{item_id}")


def collect_table_rows(
    content: str,
    expected_ids: set[str],
) -> tuple[dict[str, list[str]], list[str]]:
    """提取受控表格行并返回重复 ID。"""

    rows: dict[str, list[str]] = {}
    counts = {item_id: 0 for item_id in expected_ids}
    for line in content.splitlines():
        cells = split_markdown_row(line)
        if cells and cells[0] in expected_ids:
            counts[cells[0]] += 1
            rows[cells[0]] = cells
    duplicates = sorted(item_id for item_id, count in counts.items() if count > 1)
    return rows, duplicates


def validate_fields(
    content: str,
    fields: dict[str, str],
    errors: list[str],
) -> tuple[
    str,
    str,
    int | None,
    float | None,
    float | None,
    float | None,
    str,
    bool | None,
]:
    """校验摘要字段并返回评分所需值。"""

    for field_name in REQUIRED_FIELDS:
        if field_name not in fields or not fields[field_name]:
            errors.append(f"缺少机器校验字段：{field_name}")
        occurrences = len(
            re.findall(
                rf"^- {re.escape(field_name)}:",
                content,
                flags=re.MULTILINE,
            )
        )
        if occurrences > 1:
            errors.append(f"机器校验字段重复：{field_name}")

    mode = fields.get("migration_mode", "")
    if mode not in MODES:
        errors.append(f"migration_mode 非法：{mode!r}")
    elif f"## 4. {MODES[mode]['title']}" not in content:
        errors.append(f"缺少模式专项章节：{MODES[mode]['title']}")

    platform = fields.get("platform_mode", "")
    if platform not in PLATFORMS:
        errors.append(f"platform_mode 非法：{platform!r}")
    elif f"## 5. {PLATFORMS[platform]['title']}" not in content:
        errors.append(f"缺少平台专项章节：{PLATFORMS[platform]['title']}")

    for field_name in ("source", "target"):
        value = fields.get(field_name, "").strip()
        if (
            not value
            or PLACEHOLDER_PATTERN.search(value)
            or value.upper().startswith("N/A")
        ):
            errors.append(f"{field_name} 必须是明确的源/目标路径或入口")

    for field_name in EVIDENCE_FIELDS:
        evidence = fields.get(field_name, "")
        if not has_valid_evidence(evidence) or evidence.upper().startswith("N/A"):
            errors.append(f"{field_name} 缺少有效证据；硬门禁字段不能使用 N/A")

    conclusion = fields.get("final_conclusion", "").strip().upper()
    if conclusion not in {"PASS", "CODE_ONLY"}:
        errors.append("final_conclusion 必须为 PASS 或 CODE_ONLY")

    runtime_visual_value = fields.get(
        "runtime_visual_verified",
        "",
    ).strip().upper()
    runtime_visual_verified: bool | None
    if runtime_visual_value == "YES":
        runtime_visual_verified = True
    elif runtime_visual_value == "NO":
        runtime_visual_verified = False
    else:
        runtime_visual_verified = None
        errors.append("runtime_visual_verified 必须为 YES 或 NO")

    runtime_surface = fields.get("runtime_visual_surface", "").strip().upper()
    runtime_environment = fields.get(
        "runtime_visual_environment",
        "",
    ).strip()
    runtime_unit = fields.get("runtime_visual_unit", "").strip().upper()
    runtime_max_error_value = fields.get("runtime_visual_max_error", "").strip()
    runtime_evidence = fields.get("runtime_visual_evidence", "").strip()
    if runtime_visual_verified is True:
        if platform in PLATFORMS:
            platform_spec = PLATFORMS[platform]
            if runtime_surface not in platform_spec["runtime_surfaces"]:
                allowed_surfaces = ", ".join(platform_spec["runtime_surfaces"])
                errors.append(
                    f"{platform} 的 runtime_visual_surface 必须为 {allowed_surfaces}"
                )
            if runtime_unit not in platform_spec["runtime_units"]:
                allowed_units = ", ".join(platform_spec["runtime_units"])
                errors.append(
                    f"{platform} 的 runtime_visual_unit 必须为 {allowed_units}"
                )
            elif not any(
                re.search(
                    unit_pattern,
                    runtime_environment,
                    flags=re.IGNORECASE,
                )
                for unit_pattern in platform_spec["runtime_unit_patterns"][
                    runtime_unit
                ]
            ):
                errors.append(
                    f"runtime_visual_unit={runtime_unit} 与运行环境/UI 框架不匹配"
                )
            for runtime_pattern in platform_spec["runtime_patterns"]:
                if not re.search(
                    runtime_pattern,
                    runtime_environment,
                    flags=re.IGNORECASE,
                ):
                    errors.append(
                        f"runtime_visual_environment 不符合 {platform} 的真实运行环境要求"
                    )
        runtime_max_error = parse_score(
            runtime_max_error_value,
            "runtime_visual_max_error",
            errors,
        )
        if runtime_max_error is not None and runtime_max_error > 1:
            errors.append(
                "runtime_visual_max_error 必须小于等于 1 逻辑显示单位"
            )
        if not has_runtime_visual_evidence(runtime_evidence):
            errors.append(
                "runtime_visual_evidence 必须包含 runtime、screenshot、rendered_style、viewport 和 geometry 的目标平台渲染证据"
            )
        if conclusion != "PASS":
            errors.append("运行时视觉已验证时 final_conclusion 必须为 PASS")
    elif runtime_visual_verified is False:
        if runtime_surface != "UNVERIFIED":
            errors.append(
                "运行时视觉未验证时 runtime_visual_surface 必须为 UNVERIFIED"
            )
        if runtime_environment.upper() != "UNVERIFIED":
            errors.append(
                "运行时视觉未验证时 runtime_visual_environment 必须为 UNVERIFIED"
            )
        if runtime_unit != "UNVERIFIED":
            errors.append(
                "运行时视觉未验证时 runtime_visual_unit 必须为 UNVERIFIED"
            )
        if runtime_max_error_value.upper() != "UNVERIFIED":
            errors.append(
                "运行时视觉未验证时 runtime_visual_max_error 必须为 UNVERIFIED"
            )
        if not has_unverified_evidence(runtime_evidence):
            errors.append(
                "运行时视觉未验证时 evidence 必须使用 UNVERIFIED: 原因; evidence=阻塞证据"
            )
        if conclusion != "CODE_ONLY":
            errors.append("运行时视觉未验证时 final_conclusion 必须为 CODE_ONLY")

    p0_open = parse_int(fields.get("p0_open", ""), "p0_open", errors)
    p1_open = parse_int(fields.get("p1_open", ""), "p1_open", errors)
    accepted_p2 = parse_int(
        fields.get("accepted_p2", ""),
        "accepted_p2",
        errors,
    )
    raw_score = parse_score(fields.get("raw_score", ""), "raw_score", errors)
    applicable_max = parse_score(
        fields.get("applicable_max_score", ""),
        "applicable_max_score",
        errors,
    )
    total_score = parse_score(
        fields.get("total_score", ""),
        "total_score",
        errors,
    )

    if p0_open is not None and p0_open != 0:
        errors.append(f"存在未解决 P0：{p0_open}")
    if p1_open is not None and p1_open != 0:
        errors.append(f"存在未解决 P1：{p1_open}")
    return (
        mode,
        platform,
        accepted_p2,
        raw_score,
        applicable_max,
        total_score,
        conclusion,
        runtime_visual_verified,
    )


def validate_gates(
    content: str,
    is_code_only: bool,
    errors: list[str],
) -> None:
    """校验全部硬门禁。"""

    gate_ids = {gate_id for gate_id, _ in GATES}
    rows, duplicates = collect_table_rows(content, gate_ids)
    if duplicates:
        errors.append(f"硬门禁 ID 重复：{', '.join(duplicates)}")

    for gate_id, gate_name in GATES:
        cells = rows.get(gate_id)
        if cells is None:
            errors.append(f"缺少硬门禁行：{gate_id} {gate_name}")
            continue
        if len(cells) != 4:
            errors.append(f"{gate_id} 表格列数错误，应为 4 列")
            continue
        expected_status = (
            "PENDING_RUNTIME"
            if is_code_only and gate_id in RUNTIME_VISUAL_GATE_IDS
            else "PASS"
        )
        actual_status = cells[2].strip().upper()
        if actual_status != expected_status:
            errors.append(
                f"{gate_id} 状态应为 {expected_status}，当前状态：{cells[2]!r}"
            )
        evidence = cells[3].strip()
        if expected_status == "PENDING_RUNTIME":
            if not has_unverified_evidence(evidence):
                errors.append(
                    f"{gate_id} 待运行时证据必须使用 UNVERIFIED 格式"
                )
        elif not has_valid_evidence(evidence) or evidence.upper().startswith("N/A"):
            errors.append(f"{gate_id} 缺少有效证据；硬门禁不能使用 N/A")


def validate_scores(
    content: str,
    accepted_p2: int | None,
    declared_raw: float | None,
    declared_applicable_max: float | None,
    declared_total: float | None,
    is_code_only: bool,
    runtime_visual_verified: bool | None,
    errors: list[str],
) -> None:
    """校验逐项得分和 N/A 归一化总分。"""

    score_ids = {item_id for item_id, *_ in SCORE_ITEMS}
    rows, duplicates = collect_table_rows(content, score_ids)
    if duplicates:
        errors.append(f"评分 ID 重复：{', '.join(duplicates)}")

    calculated_raw = 0.0
    calculated_applicable_max = 0.0
    partial_count = 0
    pending_runtime_score_count = 0

    for item_id, category, item_name, expected_maximum in SCORE_ITEMS:
        cells = rows.get(item_id)
        if cells is None:
            errors.append(f"缺少评分行：{item_id} {item_name}")
            continue
        if len(cells) != 7:
            errors.append(f"{item_id} 表格列数错误，应为 7 列")
            continue
        if cells[1] != category or cells[2] != item_name:
            errors.append(f"{item_id} 类别或评分项被修改")

        maximum = parse_score(cells[3], f"{item_id} 满分", errors)
        score = parse_score(cells[5], f"{item_id} 原始得分", errors)
        status = cells[4].strip().upper()
        evidence = cells[6].strip()
        if maximum is None or score is None:
            continue
        if not math.isclose(maximum, expected_maximum, abs_tol=1e-9):
            errors.append(
                f"{item_id} 满分应为 {expected_maximum}，当前值为 {maximum:g}"
            )
        if score > expected_maximum:
            errors.append(f"{item_id} 得分不能超过满分 {expected_maximum}")

        if status == "N/A":
            if not math.isclose(score, 0.0, abs_tol=1e-9):
                errors.append(f"{item_id} N/A 的原始得分必须为 0")
            if not has_valid_evidence(evidence):
                errors.append(
                    f"{item_id} N/A 必须使用 N/A: 原因; evidence=证明材料"
                )
            continue

        calculated_applicable_max += expected_maximum
        calculated_raw += score

        if status == "PASS":
            if not math.isclose(score, expected_maximum, abs_tol=1e-9):
                errors.append(f"{item_id} PASS 时必须得满分")
            if not has_valid_evidence(evidence):
                errors.append(f"{item_id} PASS 但缺少有效证据")
            if item_id.startswith("U") and runtime_visual_verified is not True:
                errors.append(
                    f"{item_id} 缺少运行时视觉验证，不能标记 PASS"
                )
        elif status == "PARTIAL":
            partial_count += 1
            if not 0 < score < expected_maximum:
                errors.append(f"{item_id} PARTIAL 得分必须大于 0 且小于满分")
            if not has_valid_evidence(evidence):
                errors.append(f"{item_id} PARTIAL 但缺少有效证据")
            if not re.search(r"\bP2-[A-Za-z0-9_-]+\b", evidence, re.IGNORECASE):
                errors.append(f"{item_id} PARTIAL 证据缺少 P2 编号")
            if not re.search(
                r"accepted\s*=\s*(?:yes|true|是|已接受)",
                evidence,
                re.IGNORECASE,
            ):
                errors.append(f"{item_id} PARTIAL 证据缺少用户接受记录")
            if item_id.startswith("U") and runtime_visual_verified is not True:
                errors.append(
                    f"{item_id} 缺少运行时视觉验证，不能标记 PARTIAL"
                )
        elif status == "FAIL":
            if not math.isclose(score, 0.0, abs_tol=1e-9):
                errors.append(f"{item_id} FAIL 必须记 0 分")
            errors.append(f"{item_id} 仍为 FAIL，报告不合格")
        elif status == "UNVERIFIED":
            if not math.isclose(score, 0.0, abs_tol=1e-9):
                errors.append(f"{item_id} UNVERIFIED 必须记 0 分")
            if not has_unverified_evidence(evidence):
                errors.append(
                    f"{item_id} UNVERIFIED 必须说明原因并提供阻塞证据"
                )
            if is_code_only and item_id.startswith("U"):
                pending_runtime_score_count += 1
            else:
                errors.append(
                    f"{item_id} 仍为 UNVERIFIED；仅 CODE_ONLY 的视觉评分项可待运行时验证"
                )
        else:
            errors.append(f"{item_id} 状态非法：{cells[4]!r}")

    if is_code_only and pending_runtime_score_count == 0:
        errors.append("CODE_ONLY 至少需要一个视觉评分项标记为 UNVERIFIED")

    if accepted_p2 is not None and partial_count > accepted_p2:
        errors.append(
            f"PARTIAL 项数量为 {partial_count}，超过 accepted_p2={accepted_p2}"
        )

    if calculated_applicable_max <= 0:
        errors.append("适用满分必须大于 0")
        normalized_total = 0.0
    else:
        normalized_total = round(
            calculated_raw / calculated_applicable_max * 100,
            2,
        )

    comparisons = [
        ("raw_score", declared_raw, calculated_raw),
        (
            "applicable_max_score",
            declared_applicable_max,
            calculated_applicable_max,
        ),
        ("total_score", declared_total, normalized_total),
    ]
    for label, declared, calculated in comparisons:
        if declared is not None and not math.isclose(
            declared,
            calculated,
            abs_tol=0.01,
        ):
            errors.append(
                f"{label}={declared:g} 与计算值 {calculated:g} 不一致"
            )

    if declared_total is not None:
        if not is_code_only and declared_total < 95:
            errors.append(f"归一化总分 {declared_total:g} 低于合格线 95")
        if declared_total > 100:
            errors.append(f"归一化总分 {declared_total:g} 不能超过 100")


def validate_report(content: str) -> tuple[list[str], bool]:
    """执行全部报告校验。"""

    errors: list[str] = []
    errors.extend(specification_errors())

    placeholder_lines = [
        line_number
        for line_number, line in enumerate(content.splitlines(), start=1)
        if PLACEHOLDER_PATTERN.search(line)
    ]
    if placeholder_lines:
        preview = ", ".join(str(number) for number in placeholder_lines[:10])
        suffix = " 等" if len(placeholder_lines) > 10 else ""
        errors.append(f"仍有占位符，行号：{preview}{suffix}")

    fields = parse_fields(content)
    (
        mode,
        platform,
        accepted_p2,
        raw_score,
        applicable_max,
        total_score,
        conclusion,
        runtime_visual_verified,
    ) = validate_fields(content, fields, errors)
    is_code_only = conclusion == "CODE_ONLY" and runtime_visual_verified is False
    validate_checklists(content, mode, platform, is_code_only, errors)
    validate_gates(content, is_code_only, errors)
    validate_scores(
        content,
        accepted_p2,
        raw_score,
        applicable_max,
        total_score,
        is_code_only,
        runtime_visual_verified,
        errors,
    )
    return errors, is_code_only


def main() -> int:
    """校验报告并返回进程退出码。"""

    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    try:
        if not report_path.is_file():
            raise FileNotFoundError(f"报告文件不存在：{report_path}")
        content = report_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"读取报告失败：{error}", file=sys.stderr)
        return 2

    errors, is_code_only = validate_report(content)
    if errors:
        print(f"迁移报告校验失败，共 {len(errors)} 项：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    if is_code_only:
        print(f"迁移报告代码级校验通过：{report_path}")
        print(
            "运行时视觉验证仍待完成；G6/G8 保持 PENDING_RUNTIME，"
            "报告结论为 CODE_ONLY。"
        )
        return 3

    print(f"迁移报告校验通过：{report_path}")
    print(
        "完整 Checklist、P0/P1、硬门禁、运行时视觉证据与归一化评分均满足要求。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
