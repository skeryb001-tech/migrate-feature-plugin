#!/usr/bin/env python3
"""扫描源功能目录与目标目录之间的路径冲突。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_IGNORED_NAMES = {
    ".git",
    "node_modules",
    "dist",
    ".nuxt",
    "coverage",
}


@dataclass(frozen=True)
class Finding:
    """单个扫描结果。"""

    kind: str
    source: str
    target: str
    detail: str


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description=(
            "扫描源功能根目录映射到目标目录时的精确路径、大小写和路径类型冲突。"
            "相同路径且内容哈希一致的文件会标记为可复用候选，不视为冲突。"
        )
    )
    parser.add_argument("source", help="源功能根目录")
    parser.add_argument("target", help="目标落盘根目录")
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="NAME",
        help="额外忽略的目录名或文件名，可重复传入",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 输出结果，便于写入迁移报告",
    )
    return parser.parse_args()


def resolve_directory(raw_path: str, label: str) -> Path:
    """解析并校验目录。

    @param raw_path: 用户传入的目录。
    @param label: 错误信息中的目录名称。
    @returns: 解析后的绝对目录。
    """

    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"{label}不存在：{path}")
    if not path.is_dir():
        raise ValueError(f"{label}不是目录：{path}")
    return path


def should_ignore(path: Path, ignored_names: set[str]) -> bool:
    """判断路径名是否需要忽略。"""

    return path.name.casefold() in ignored_names


def walk_entries(root: Path, ignored_names: set[str]) -> Iterable[tuple[Path, bool]]:
    """遍历目录下未忽略的文件与目录。

    @returns: `(相对路径, 是否目录)` 序列。
    """

    for current_root, directory_names, file_names in os.walk(root, followlinks=False):
        current = Path(current_root)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if not should_ignore(current / name, ignored_names)
        )

        for directory_name in directory_names:
            yield (current / directory_name).relative_to(root), True

        for file_name in sorted(file_names):
            file_path = current / file_name
            if should_ignore(file_path, ignored_names):
                continue
            yield file_path.relative_to(root), False


def sha256(path: Path) -> str:
    """计算文件 SHA-256。

    @param path: 待计算文件。
    @returns: 十六进制哈希。
    """

    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_casefold_index(
    root: Path,
    ignored_names: set[str],
) -> dict[str, list[tuple[Path, bool]]]:
    """建立目标路径的大小写无关索引。"""

    index: dict[str, list[tuple[Path, bool]]] = {}
    for relative_path, is_directory in walk_entries(root, ignored_names):
        key = relative_path.as_posix().casefold()
        index.setdefault(key, []).append((relative_path, is_directory))
    return index


def find_blocking_ancestor(target_root: Path, relative_path: Path) -> Path | None:
    """查找阻止创建目标路径的非目录祖先。"""

    current = target_root
    for part in relative_path.parts[:-1]:
        current = current / part
        if os.path.lexists(current) and not current.is_dir():
            return current
    return None


def scan(
    source_root: Path,
    target_root: Path,
    ignored_names: set[str],
) -> tuple[list[Finding], list[Finding]]:
    """执行冲突扫描。

    @returns: `(冲突列表, 可复用列表)`。
    """

    conflicts: list[Finding] = []
    reusable: list[Finding] = []
    target_index = build_casefold_index(target_root, ignored_names)

    for relative_path, source_is_directory in walk_entries(source_root, ignored_names):
        source_path = source_root / relative_path
        target_path = target_root / relative_path
        relative_key = relative_path.as_posix().casefold()
        indexed_matches = target_index.get(relative_key, [])
        exact_exists = any(
            indexed_path == relative_path
            for indexed_path, _ in indexed_matches
        )

        blocker = find_blocking_ancestor(target_root, relative_path)
        if blocker is not None:
            conflicts.append(
                Finding(
                    kind="ancestor-type-conflict",
                    source=str(source_path),
                    target=str(blocker),
                    detail="目标祖先路径不是目录，无法按该相对路径落盘",
                )
            )
            continue

        if exact_exists:
            target_is_directory = target_path.is_dir()
            if source_is_directory != target_is_directory:
                conflicts.append(
                    Finding(
                        kind="path-type-conflict",
                        source=str(source_path),
                        target=str(target_path),
                        detail="源与目标同一路径的文件/目录类型不同",
                    )
                )
            elif not source_is_directory:
                try:
                    source_hash = sha256(source_path)
                    target_hash = sha256(target_path)
                except OSError as error:
                    conflicts.append(
                        Finding(
                            kind="hash-read-error",
                            source=str(source_path),
                            target=str(target_path),
                            detail=f"无法读取文件计算哈希：{error}",
                        )
                    )
                else:
                    if source_hash == target_hash:
                        reusable.append(
                            Finding(
                                kind="same-content",
                                source=str(source_path),
                                target=str(target_path),
                                detail=f"SHA-256={source_hash}",
                            )
                        )
                    else:
                        conflicts.append(
                            Finding(
                                kind="exact-path-conflict",
                                source=str(source_path),
                                target=str(target_path),
                                detail=(
                                    "路径相同但内容不同；禁止覆盖，先复用/合并或语义化重命名"
                                ),
                            )
                        )

        for indexed_path, indexed_is_directory in indexed_matches:
            if indexed_path == relative_path:
                continue
            target_variant = target_root / indexed_path
            source_type = "目录" if source_is_directory else "文件"
            target_type = "目录" if indexed_is_directory else "文件"
            conflicts.append(
                Finding(
                    kind="case-insensitive-conflict",
                    source=str(source_path),
                    target=str(target_variant),
                    detail=(
                        f"大小写无关路径相同（源为{source_type}，目标为{target_type}），"
                        "可能在 macOS/Windows/CI 或自动导入中冲突"
                    ),
                )
            )

    conflicts.sort(key=lambda item: (item.kind, item.source, item.target))
    reusable.sort(key=lambda item: (item.source, item.target))
    return conflicts, reusable


def print_text(
    source_root: Path,
    target_root: Path,
    conflicts: list[Finding],
    reusable: list[Finding],
) -> None:
    """输出人类可读报告。"""

    print(f"源目录：{source_root}")
    print(f"目标目录：{target_root}")
    print(f"冲突：{len(conflicts)}")
    print(f"相同内容可复用：{len(reusable)}")

    if reusable:
        print("\n[REUSE] 相同路径且内容一致")
        for item in reusable:
            print(f"- {item.source} -> {item.target}")
            print(f"  {item.detail}")

    if conflicts:
        print("\n[BLOCKED] 必须处理的冲突")
        for item in conflicts:
            print(f"- [{item.kind}] {item.source} -> {item.target}")
            print(f"  {item.detail}")
    else:
        print("\n[PASS] 未发现阻断性路径冲突。")


def print_json(
    source_root: Path,
    target_root: Path,
    conflicts: list[Finding],
    reusable: list[Finding],
) -> None:
    """输出 JSON 报告。"""

    payload = {
        "source": str(source_root),
        "target": str(target_root),
        "conflictCount": len(conflicts),
        "reusableCount": len(reusable),
        "conflicts": [asdict(item) for item in conflicts],
        "reusable": [asdict(item) for item in reusable],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    """运行命令并返回进程退出码。"""

    args = parse_args()
    try:
        source_root = resolve_directory(args.source, "源目录")
        target_root = resolve_directory(args.target, "目标目录")
        if source_root == target_root:
            raise ValueError("源目录与目标目录不能是同一目录")

        ignored_names = {
            name.strip().casefold()
            for name in DEFAULT_IGNORED_NAMES.union(args.ignore)
            if name.strip()
        }
        conflicts, reusable = scan(source_root, target_root, ignored_names)
    except (OSError, ValueError) as error:
        print(f"扫描失败：{error}", file=sys.stderr)
        return 2

    if args.json:
        print_json(source_root, target_root, conflicts, reusable)
    else:
        print_text(source_root, target_root, conflicts, reusable)
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
