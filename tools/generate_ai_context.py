#!/usr/bin/env python3
"""Generate a compact AI_CONTEXT.md from explicitly selected source headings."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
OUTPUT_NOTICE = "AUTO-GENERATED FILE\nDO NOT EDIT MANUALLY"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic AI_CONTEXT.md")
    parser.add_argument("target", type=Path, help="Product root")
    parser.add_argument(
        "--config",
        type=Path,
        help="Config path (default: <target>/AI_CONTEXT_SOURCES.json)",
    )
    parser.add_argument("--output", type=Path, help="Output path (default: <target>/AI_CONTEXT.md)")
    parser.add_argument("--check", action="store_true", help="Do not write; fail if output is stale")
    return parser.parse_args(argv)


def load_config(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError(f"configを読み込めません: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"config JSONが不正です: line {exc.lineno}") from exc
    if not isinstance(value, dict):
        raise ValueError("configのrootはobjectである必要があります")
    for key in ("product", "profile", "sections"):
        if key not in value:
            raise ValueError(f"configに{key}がありません")
    if not isinstance(value["sections"], list) or not value["sections"]:
        raise ValueError("sectionsは空でない配列にしてください")
    return value


def extract_heading(path: Path, wanted: str) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ValueError(f"sourceを読み込めません: {path}: {exc}") from exc

    start: int | None = None
    level = 0
    normalized = wanted.strip().casefold()
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if not match:
            continue
        title = match.group(2).strip().rstrip("#").strip().casefold()
        if start is None and title == normalized:
            start = index + 1
            level = len(match.group(1))
            continue
        if start is not None and len(match.group(1)) <= level:
            content = "\n".join(lines[start:index]).strip()
            return content or None
    if start is not None:
        content = "\n".join(lines[start:]).strip()
        return content or None
    return None


def normalize_content(content: str) -> str:
    lines = [line.rstrip() for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def generate(target: Path, config: dict[str, Any]) -> str:
    sections: list[tuple[str, str]] = []
    used_sources: list[str] = []
    for index, item in enumerate(config["sections"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"sections[{index}]はobjectにしてください")
        output = item.get("output")
        source = item.get("source")
        heading = item.get("heading")
        if not all(isinstance(value, str) and value.strip() for value in (output, source, heading)):
            raise ValueError(f"sections[{index}]のoutput/source/headingが不正です")
        path = (target / source).resolve()
        content = extract_heading(path, heading)
        if content is None:
            if item.get("required", True):
                raise ValueError(f"見出しがありません: {source} > {heading}")
            content = str(item.get("fallback", "なし"))
        sections.append((output.strip(), normalize_content(content)))
        if source not in used_sources:
            used_sources.append(source)

    references = config.get("source_references", used_sources)
    if not isinstance(references, list) or not all(isinstance(value, str) for value in references):
        raise ValueError("source_referencesは文字列の配列にしてください")

    body_lines = [
        f"# AI Context: {config['product']}",
        "",
        f"- Profile: `{config['profile']}`",
        f"- Standards version: `{config.get('standards_version', 'unspecified')}`",
    ]
    for title, content in sections:
        body_lines.extend(("", f"## {title}", "", content))

    quality_command = config.get("quality_check_command")
    if isinstance(quality_command, str) and quality_command.strip():
        body_lines.extend(("", "## Quality Check Command", "", "```powershell", quality_command.strip(), "```"))

    body_lines.extend(("", "## Source References", ""))
    body_lines.extend(f"- `{value}`" for value in references)
    body = "\n".join(body_lines).rstrip() + "\n"
    content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    header = f"<!--\n{OUTPUT_NOTICE}\nContent hash: {content_hash}\n-->\n\n"
    return header + body


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    target = args.target.resolve()
    config_path = (args.config or target / "AI_CONTEXT_SOURCES.json").resolve()
    output_path = (args.output or target / "AI_CONTEXT.md").resolve()
    try:
        config = load_config(config_path)
        rendered = generate(target, config)
    except ValueError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    current = output_path.read_text(encoding="utf-8-sig") if output_path.exists() else None
    if args.check:
        if current == rendered:
            print(f"PASS {output_path} is current")
            return 0
        print(f"FAIL {output_path} is missing or stale", file=sys.stderr)
        return 1

    if current == rendered:
        print(f"PASS unchanged: {output_path}")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"PASS generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
