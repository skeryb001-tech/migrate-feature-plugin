#!/usr/bin/env python3
"""校验迁移报告的占位符、证据、计分和硬门禁。"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

from createMigrationReport import GATES, SCORE_ITEMS


REQUIRED_FIELDS = [
    "migration_mode",
    "source",
    "target",
    "source_baseline",
    "target_baseline",
    "visual_baseline",
    "target_rules",
    "target_structure_mapping",
    "rollback_start_commit",
    "rollback_entry_disable",
    "rollback_shared_modules",
    "rollback_api_analytics",
    "rollback_cache_cleanup",
    "p0_open",
    "p1_open",
    "accepted_p2",
    "total_score",
    "final_conclusion",
]

EVIDENCE_FIELDS = [
    "source_baseline",
    "target_baseline",
    "visual_baseline",
    "target_rules",
    "target_structure_mapping",
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


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description=(
            "校验 createMigrationReport.py 生成的迁移报告。"
            "总分低于 95、存在 P0/P1、硬门禁失败、无证据得分或未验证项时返回非 0。"
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
    """判断证据字段是否完整。

    N/A 必须使用“N/A: 原因; evidence=证明材料”格式。
    """

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


def collect_gate_rows(content: str) -> dict[str, list[str]]:
    """提取硬门禁表格行。"""

    expected_ids = {gate_id for gate_id, _ in GATES}
    rows: dict[str, list[str]] = {}
    for line in content.splitlines():
        cells = split_markdown_row(line)
        if cells and cells[0] in expected_ids:
            rows[cells[0]] = cells
    return rows


def collect_score_rows(content: str) -> dict[str, list[str]]:
    """提取评分表格行。"""

    expected_ids = {item_id for item_id, *_ in SCORE_ITEMS}
    rows: dict[str, list[str]] = {}
    for line in content.splitlines():
        cells = split_markdown_row(line)
        if cells and cells[0] in expected_ids:
            rows[cells[0]] = cells
    return rows


def find_duplicate_table_ids(content: str, expected_ids: set[str]) -> list[str]:
    """查找重复出现的受控表格 ID。"""

    counts = {item_id: 0 for item_id in expected_ids}
    for line in content.splitlines():
        cells = split_markdown_row(line)
        if cells and cells[0] in counts:
            counts[cells[0]] += 1
    return sorted(item_id for item_id, count in counts.items() if count > 1)


def validate_fields(
    content: str,
    fields: dict[str, str],
    errors: list[str],
) -> tuple[int | None, int | None, int | None, float | None]:
    """校验摘要字段并返回关键数值。"""

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
    if mode not in {"cross-project", "cross-page"}:
        errors.append(f"migration_mode 非法：{mode!r}")
    expected_heading = (
        "## 4. 跨项目专项 Checklist"
        if mode == "cross-project"
        else "## 4. 跨页面专项 Checklist"
    )
    if mode in {"cross-project", "cross-page"} and expected_heading not in content:
        errors.append(f"缺少模式专项章节：{expected_heading}")

    for field_name in ("source", "target"):
        value = fields.get(field_name, "").strip()
        if (
            not value
            or PLACEHOLDER_PATTERN.search(value)
            or value.upper().startswith("N/A")
        ):
            errors.append(f"{field_name} 必须是明确的源/目标路径或入口")

    for field_name in EVIDENCE_FIELDS:
        value = fields.get(field_name, "")
        if not has_valid_evidence(value):
            errors.append(f"{field_name} 缺少有效证据或 N/A 说明")

    p0_open = parse_int(fields.get("p0_open", ""), "p0_open", errors)
    p1_open = parse_int(fields.get("p1_open", ""), "p1_open", errors)
    accepted_p2 = parse_int(fields.get("accepted_p2", ""), "accepted_p2", errors)
    total_score = parse_score(fields.get("total_score", ""), "total_score", errors)

    if p0_open is not None and p0_open != 0:
        errors.append(f"存在未解决 P0：{p0_open}")
    if p1_open is not None and p1_open != 0:
        errors.append(f"存在未解决 P1：{p1_open}")
    if fields.get("final_conclusion", "").strip().upper() not in {"PASS", "合格"}:
        errors.append("final_conclusion 必须为 PASS 或 合格")

    return p0_open, p1_open, accepted_p2, total_score


def validate_gates(content: str, errors: list[str]) -> None:
    """校验全部硬门禁。"""

    rows = collect_gate_rows(content)
    duplicate_ids = find_duplicate_table_ids(
        content,
        {gate_id for gate_id, _ in GATES},
    )
    if duplicate_ids:
        errors.append(f"硬门禁 ID 重复：{', '.join(duplicate_ids)}")
    for gate_id, gate_name in GATES:
        cells = rows.get(gate_id)
        if cells is None:
            errors.append(f"缺少硬门禁行：{gate_id} {gate_name}")
            continue
        if len(cells) != 4:
            errors.append(f"{gate_id} 表格列数错误，应为 4 列")
            continue
        status = cells[2].strip().upper()
        evidence = cells[3].strip()
        if status != "PASS":
            errors.append(f"{gate_id} 未通过，当前状态：{cells[2]!r}")
        if not has_valid_evidence(evidence):
            errors.append(f"{gate_id} 缺少有效证据")


def validate_scores(
    content: str,
    accepted_p2: int | None,
    declared_total: float | None,
    errors: list[str],
) -> None:
    """校验逐项得分和总分。"""

    rows = collect_score_rows(content)
    duplicate_ids = find_duplicate_table_ids(
        content,
        {item_id for item_id, *_ in SCORE_ITEMS},
    )
    if duplicate_ids:
        errors.append(f"评分 ID 重复：{', '.join(duplicate_ids)}")
    calculated_total = 0.0
    partial_count = 0

    for item_id, category, item_name, expected_maximum in SCORE_ITEMS:
        cells = rows.get(item_id)
        if cells is None:
            errors.append(f"缺少评分行：{item_id} {item_name}")
            continue
        if len(cells) != 7:
            errors.append(f"{item_id} 表格列数错误，应为 7 列")
            continue

        if cells[1] != category or cells[2] != item_name:
            errors.append(f"{item_id} 类别或评分项被修改，无法可靠计分")

        maximum = parse_score(cells[3], f"{item_id} 满分", errors)
        score = parse_score(cells[5], f"{item_id} 得分", errors)
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

        if status == "PASS":
            if not math.isclose(score, expected_maximum, abs_tol=1e-9):
                errors.append(f"{item_id} 状态 PASS 时必须得满分")
            if not has_valid_evidence(evidence):
                errors.append(f"{item_id} PASS 但缺少有效证据")
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
        elif status in {"FAIL", "UNVERIFIED"}:
            if not math.isclose(score, 0.0, abs_tol=1e-9):
                errors.append(f"{item_id} {status} 必须记 0 分")
            errors.append(f"{item_id} 仍为 {status}，最终验收不能通过")
        elif status == "N/A":
            if not math.isclose(score, 0.0, abs_tol=1e-9):
                errors.append(f"{item_id} N/A 必须记 0 分")
            if not has_valid_evidence(evidence):
                errors.append(
                    f"{item_id} N/A 必须说明原因并提供 evidence=证明材料"
                )
        else:
            errors.append(f"{item_id} 状态非法：{cells[4]!r}")

        calculated_total += score

    if accepted_p2 is not None and partial_count > accepted_p2:
        errors.append(
            f"PARTIAL 项数量为 {partial_count}，超过 accepted_p2={accepted_p2}"
        )

    if declared_total is not None:
        if not math.isclose(declared_total, calculated_total, abs_tol=1e-9):
            errors.append(
                f"total_score={declared_total:g} 与逐项合计 {calculated_total:g} 不一致"
            )
        if declared_total < 95:
            errors.append(f"总分 {declared_total:g} 低于合格线 95")
        if declared_total > 100:
            errors.append(f"总分 {declared_total:g} 不能超过 100")


def validate_report(content: str) -> list[str]:
    """执行全部报告校验。

    @returns: 错误信息列表；空列表表示通过。
    """

    errors: list[str] = []

    placeholder_lines = [
        line_number
        for line_number, line in enumerate(content.splitlines(), start=1)
        if PLACEHOLDER_PATTERN.search(line)
    ]
    if placeholder_lines:
        preview = ", ".join(str(number) for number in placeholder_lines[:10])
        suffix = " 等" if len(placeholder_lines) > 10 else ""
        errors.append(f"仍有占位符，行号：{preview}{suffix}")

    unchecked_lines = [
        line_number
        for line_number, line in enumerate(content.splitlines(), start=1)
        if re.match(r"^\s*- \[ \]\s+", line)
    ]
    if unchecked_lines:
        preview = ", ".join(str(number) for number in unchecked_lines[:10])
        suffix = " 等" if len(unchecked_lines) > 10 else ""
        errors.append(f"仍有未完成 Checklist，行号：{preview}{suffix}")

    fields = parse_fields(content)
    _, _, accepted_p2, total_score = validate_fields(content, fields, errors)
    validate_gates(content, errors)
    validate_scores(content, accepted_p2, total_score, errors)
    return errors


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

    errors = validate_report(content)
    if errors:
        print(f"迁移报告校验失败，共 {len(errors)} 项：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"迁移报告校验通过：{report_path}")
    print("总分、P0/P1、硬门禁、证据与计分规则均满足要求。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
