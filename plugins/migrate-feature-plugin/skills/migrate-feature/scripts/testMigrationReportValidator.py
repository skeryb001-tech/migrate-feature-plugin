#!/usr/bin/env python3
"""回归测试迁移报告的 PASS、CODE_ONLY、失败与 N/A 归一化。"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from createMigrationReport import build_report
from migrationSpec import (
    GATES,
    RUNTIME_VISUAL_CHECKLIST_IDS,
    RUNTIME_VISUAL_GATE_IDS,
    SCORE_ITEMS,
)


SCRIPT_PATH = Path(__file__).with_name("validateMigrationReport.py")


def replace_field(content: str, field_name: str, value: str) -> str:
    """替换报告中的单行机器字段。"""

    return re.sub(
        rf"^- {re.escape(field_name)}:.*$",
        f"- {field_name}: {value}",
        content,
        flags=re.MULTILINE,
    )


def build_completed_report(is_code_only: bool) -> str:
    """构造可预测的完整 PASS 或 CODE_ONLY 报告。"""

    content = build_report("cross-project", "/source-a", "/target-b")
    na_ids = {"F05"}
    score_maximum = {item_id: maximum for item_id, *_, maximum in SCORE_ITEMS}
    applicable_max = sum(
        maximum
        for item_id, *_, maximum in SCORE_ITEMS
        if item_id not in na_ids
    )

    if is_code_only:
        raw_score = sum(
            maximum
            for item_id, *_, maximum in SCORE_ITEMS
            if item_id not in na_ids and not item_id.startswith("U")
        )
        runtime_verified = "NO"
        runtime_browser = "UNVERIFIED"
        runtime_max_error = "UNVERIFIED"
        runtime_evidence = (
            "UNVERIFIED: 测试环境没有浏览器渲染能力; "
            "evidence=browser command unavailable"
        )
        conclusion = "CODE_ONLY"
    else:
        raw_score = applicable_max
        runtime_verified = "YES"
        runtime_browser = "Chromium 126.0.0"
        runtime_max_error = "0.75"
        runtime_evidence = (
            "browser=Chromium 126.0.0 headless; "
            "screenshot=/tmp/source.png,/tmp/target.png; "
            "computed_style=/tmp/computed.json; viewport=1440x900,DPR=2,zoom=100%; "
            "geometry=/tmp/geometry.json"
        )
        conclusion = "PASS"

    total_score = round(raw_score / applicable_max * 100, 2)
    field_values = {
        "source_baseline": "commit=source123; test=pass",
        "target_baseline": "commit=target123; test=pass",
        "visual_baseline": "source screenshot=/tmp/source.png",
        "target_rules": "target AGENTS.md and adjacent modules",
        "target_structure_mapping": "source responsibilities mapped to target modules",
        "conflict_scan_evidence": "scanMigrationConflicts.py exit=0",
        "rollback_start_commit": "target123",
        "rollback_entry_disable": "remove target route entry",
        "rollback_shared_modules": "restore mapped shared modules",
        "rollback_api_analytics": "restore service and analytics mapping",
        "rollback_cache_cleanup": "clear feature cache by business id",
        "p0_open": "0",
        "p1_open": "0",
        "accepted_p2": "0",
        "runtime_visual_verified": runtime_verified,
        "runtime_visual_browser": runtime_browser,
        "runtime_visual_max_error_css_px": runtime_max_error,
        "runtime_visual_evidence": runtime_evidence,
        "raw_score": str(raw_score),
        "applicable_max_score": str(applicable_max),
        "total_score": str(total_score),
        "final_conclusion": conclusion,
    }
    for field_name, value in field_values.items():
        content = replace_field(content, field_name, value)

    checklist_pattern = re.compile(
        r"^- \[ \] \[([A-Z0-9-]+)\] (.+)$",
        flags=re.MULTILINE,
    )

    def complete_checklist(match: re.Match[str]) -> str:
        """完成非运行时待验证 Checklist。"""

        item_id = match.group(1)
        marker = " " if is_code_only and item_id in RUNTIME_VISUAL_CHECKLIST_IDS else "x"
        return f"- [{marker}] [{item_id}] {match.group(2)}"

    content = checklist_pattern.sub(complete_checklist, content)

    for gate_id, gate_name in GATES:
        if is_code_only and gate_id in RUNTIME_VISUAL_GATE_IDS:
            status = "PENDING_RUNTIME"
            evidence = (
                "UNVERIFIED: 测试环境没有浏览器渲染能力; "
                "evidence=browser command unavailable"
            )
        else:
            status = "PASS"
            evidence = f"{gate_id} focused verification passed"
        content = content.replace(
            f"| {gate_id} | {gate_name} | TODO | TODO |",
            f"| {gate_id} | {gate_name} | {status} | {evidence} |",
        )

    for item_id, category, item_name, maximum in SCORE_ITEMS:
        old_row = (
            f"| {item_id} | {category} | {item_name} | {maximum} | "
            "UNVERIFIED | 0 | TODO |"
        )
        if item_id in na_ids:
            status = "N/A"
            score = 0
            evidence = "N/A: 功能无该业务分支; evidence=source and target call-chain search"
        elif is_code_only and item_id.startswith("U"):
            status = "UNVERIFIED"
            score = 0
            evidence = (
                "UNVERIFIED: 测试环境没有浏览器渲染能力; "
                "evidence=browser command unavailable"
            )
        else:
            status = "PASS"
            score = score_maximum[item_id]
            evidence = f"{item_id} focused verification passed"
        new_row = (
            f"| {item_id} | {category} | {item_name} | {maximum} | "
            f"{status} | {score} | {evidence} |"
        )
        content = content.replace(old_row, new_row)

    return content.replace("TODO", "evidence")


def run_validator(report: str) -> subprocess.CompletedProcess[str]:
    """在临时文件上运行报告校验器。"""

    with tempfile.TemporaryDirectory() as directory:
        report_path = Path(directory) / "migration-report.md"
        report_path.write_text(report, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(report_path)],
            check=False,
            capture_output=True,
            text=True,
        )


def main() -> int:
    """执行三类报告结果回归测试。"""

    pass_report = build_completed_report(is_code_only=False)
    code_only_report = build_completed_report(is_code_only=True)
    invalid_report = replace_field(
        code_only_report,
        "final_conclusion",
        "PASS",
    )
    custom_renderer_report = replace_field(
        pass_report,
        "runtime_visual_browser",
        "Custom Raster Renderer 1.0",
    )
    over_threshold_report = replace_field(
        pass_report,
        "runtime_visual_max_error_css_px",
        "1.01",
    )
    runtime_na_report = replace_field(
        code_only_report,
        "runtime_visual_evidence",
        "N/A: 没有浏览器; evidence=browser unavailable",
    )
    cases = [
        ("PASS with N/A normalization", pass_report, 0),
        ("CODE_ONLY pending runtime", code_only_report, 3),
        ("invalid visual PASS claim", invalid_report, 1),
        ("custom renderer cannot satisfy browser gate", custom_renderer_report, 1),
        ("visual error above one CSS px", over_threshold_report, 1),
        ("missing runtime cannot use N/A", runtime_na_report, 1),
    ]

    failures: list[str] = []
    for name, report, expected_exit_code in cases:
        result = run_validator(report)
        if result.returncode != expected_exit_code:
            failures.append(
                f"{name}: expected={expected_exit_code}, actual={result.returncode}; "
                f"stdout={result.stdout!r}; stderr={result.stderr!r}"
            )
        else:
            print(f"PASS: {name} -> exit {result.returncode}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
