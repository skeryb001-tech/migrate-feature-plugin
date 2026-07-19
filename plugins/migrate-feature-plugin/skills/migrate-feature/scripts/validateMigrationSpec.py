#!/usr/bin/env python3
"""校验前端功能迁移机器规范源的完整性。"""

from __future__ import annotations

import sys

from migrationSpec import specification_errors


def main() -> int:
    """校验规范并返回进程退出码。"""

    errors = specification_errors()
    if errors:
        print(f"迁移机器规范校验失败，共 {len(errors)} 项：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("迁移机器规范校验通过：阶段、门禁、Checklist 与评分权重完整。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
