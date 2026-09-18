#!/usr/bin/env python3
"""回归测试增强迁移报告的 PASS、CODE_ONLY 和失败分支。"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from createMigrationReport import build_report
from migrationSpec import CHECKPOINTS


SCRIPT_PATH = Path(__file__).with_name("validateMigrationReport.py")


RUNTIME_FIXTURES = {
    "web-frontend": {
        "surface": "BROWSER",
        "environment": "Chromium 126.0.0 on macOS 15.0",
        "unit": "CSS_PX",
    },
    "hybrid-client": {
        "surface": "APP_WINDOW",
        "environment": "Electron 32.1.0 on macOS 15.0",
        "unit": "CSS_PX",
    },
    "native-client": {
        "surface": "SIMULATOR",
        "environment": "iOS 18.0 Simulator with SwiftUI and Xcode 16.0",
        "unit": "PT",
    },
}


def replace_field(content: str, field_name: str, value: str) -> str:
    return re.sub(
        rf"^- {re.escape(field_name)}:.*$",
        f"- {field_name}: {value}",
        content,
        flags=re.MULTILINE,
    )


def complete_checkpoints(content: str) -> str:
    for checkpoint_id, title, _ in CHECKPOINTS:
        content = content.replace(
            f"| {checkpoint_id} | {title} | TODO | TODO |",
            f"| {checkpoint_id} | {title} | PASS | {checkpoint_id} focused evidence |",
        )
    return content


def build_completed_report(
    platform: str,
    *,
    runtime_required: bool,
    visual_required: bool,
    pending: bool = False,
    blocking_issues: int = 0,
) -> str:
    """构造可预测的增强报告。"""

    content = build_report(
        "cross-project",
        platform,
        "/source-a",
        "/target-b",
        "跨运行时正式验收",
    )

    if runtime_required:
        runtime_verified = "NO" if pending else "YES"
        runtime_environment = "UNVERIFIED" if pending else "target runtime 1.0"
        runtime_evidence = (
            "UNVERIFIED: target runtime unavailable; evidence=runner missing"
            if pending
            else "command=run target; result=critical flow passed"
        )
    else:
        runtime_verified = "NOT_REQUIRED"
        runtime_environment = "NOT_REQUIRED"
        runtime_evidence = (
            "NOT_REQUIRED: pure source mapping; evidence=call-chain shows no runtime change"
        )

    if visual_required:
        fixture = RUNTIME_FIXTURES[platform]
        visual_verified = "NO" if pending else "YES"
        visual_surface = "UNVERIFIED" if pending else fixture["surface"]
        visual_unit = "UNVERIFIED" if pending else fixture["unit"]
        visual_environment = "UNVERIFIED" if pending else fixture["environment"]
        visual_evidence = (
            "UNVERIFIED: visual runtime unavailable; evidence=runner missing"
            if pending
            else (
                "screenshot=/tmp/source.png,/tmp/target.png; "
                "rendered_style=/tmp/style.json; viewport=1440x900; "
                "geometry=/tmp/geometry.json"
            )
        )
    else:
        visual_verified = "NOT_REQUIRED"
        visual_surface = "NOT_REQUIRED"
        visual_unit = "NOT_REQUIRED"
        visual_environment = "NOT_REQUIRED"
        visual_evidence = (
            "NOT_REQUIRED: no visible UI change; evidence=changed files contain logic only"
        )

    if blocking_issues:
        conclusion = "BLOCKED"
    elif pending:
        conclusion = "CODE_ONLY"
    else:
        conclusion = "PASS"

    values = {
        "source_baseline": "commit=source123; command=test source",
        "target_baseline": "commit=target123; status=dirty files preserved",
        "target_rules": "target AGENTS.md and adjacent modules",
        "migration_scope": "upload trigger through service result",
        "target_mapping": "source responsibilities mapped to target modules",
        "blocking_issues": str(blocking_issues),
        "runtime_required": "YES" if runtime_required else "NO",
        "runtime_verified": runtime_verified,
        "runtime_environment": runtime_environment,
        "runtime_evidence": runtime_evidence,
        "visual_required": "YES" if visual_required else "NO",
        "visual_verified": visual_verified,
        "visual_surface": visual_surface,
        "visual_unit": visual_unit,
        "visual_environment": visual_environment,
        "visual_evidence": visual_evidence,
        "rollback_plan": "disable target entry and restore shared service from target123",
        "final_conclusion": conclusion,
    }
    for field_name, value in values.items():
        content = replace_field(content, field_name, value)
    return complete_checkpoints(content)


def run_validator(report: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        report_path = Path(directory) / "migration-report.md"
        report_path.write_text(report, encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT_PATH), str(report_path)],
            check=False,
            capture_output=True,
            text=True,
        )


def main() -> int:
    logic_pass = build_completed_report(
        "web-frontend",
        runtime_required=False,
        visual_required=False,
    )
    visual_pass = {
        platform: build_completed_report(
            platform,
            runtime_required=True,
            visual_required=True,
        )
        for platform in RUNTIME_FIXTURES
    }
    code_only = build_completed_report(
        "web-frontend",
        runtime_required=True,
        visual_required=True,
        pending=True,
    )
    blocked = build_completed_report(
        "web-frontend",
        runtime_required=False,
        visual_required=False,
        blocking_issues=1,
    )

    cases = [
        ("logic-only enhanced PASS", logic_pass, 0),
        ("web visual PASS", visual_pass["web-frontend"], 0),
        ("hybrid visual PASS", visual_pass["hybrid-client"], 0),
        ("native visual PASS", visual_pass["native-client"], 0),
        ("pending runtime CODE_ONLY", code_only, 3),
        (
            "pending runtime cannot claim PASS",
            replace_field(code_only, "final_conclusion", "PASS"),
            1,
        ),
        (
            "web visual rejects app window",
            replace_field(visual_pass["web-frontend"], "visual_surface", "APP_WINDOW"),
            1,
        ),
        (
            "visual evidence must include geometry",
            replace_field(
                visual_pass["web-frontend"],
                "visual_evidence",
                "screenshot=a; rendered_style=b; viewport=c",
            ),
            1,
        ),
        (
            "missing checkpoint",
            logic_pass.replace("| C4 | 证据 | PASS | C4 focused evidence |\n", ""),
            1,
        ),
        ("blocking issue returns failure", blocked, 1),
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
