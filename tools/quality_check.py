#!/usr/bin/env python3
"""Deterministic, profile-aware checks for PEAKHEADZ product repositories."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


SEVERITY_ORDER = {"FAIL": 0, "WARN": 1, "PASS": 2}
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".bat", ".ps1", ".json", ".toml", ".ini",
    ".html", ".css", ".js", ".mjs", ".cjs", ".xml", ".webmanifest",
}
DEFAULT_EXCLUDES = {".git", ".venv", "venv", "build", "dist", "__pycache__", "node_modules"}
FORBIDDEN_CREDITS = {
    "vibe coding": re.compile(r"\bvibe[\s-]*cod(?:ing|ed)\b", re.IGNORECASE),
    "AI-generated": re.compile(r"\bAI[\s-]*generated\b", re.IGNORECASE),
    "Made with AI": re.compile(r"\bMade\s+with\s+AI\b", re.IGNORECASE),
    "Codex": re.compile(r"\bCodex\b", re.IGNORECASE),
}
INTERNAL_TERMS = re.compile(r"\b(?:traceback|stack\s*trace|exception|errno|debug)\b", re.IGNORECASE)
GENERIC_ERROR_VALUE = re.compile(r"[\"'](?:status_error|dialog_error_title)[\"']\s*:\s*[\"']エラー[\"']")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


class VisibleHTMLParser(HTMLParser):
    """Collect visible text without treating script/style source as user copy."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"script", "style", "template"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "template"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return "\n".join(self.parts)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PEAKHEADZ profile quality checks.")
    parser.add_argument("target", type=Path, help="Product root to inspect")
    parser.add_argument("--profile", choices=("app", "web"), required=True)
    parser.add_argument(
        "--config",
        type=Path,
        help="Config path (default: <target>/peakheadz_quality.json)",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON")
    return parser.parse_args(argv)


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"設定を読み込めません: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("設定のrootはobjectである必要があります")
    return value


def display_path(path: Path, target: Path) -> str:
    try:
        return path.resolve().relative_to(target.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def configured_paths(target: Path, values: Any) -> list[Path]:
    if not isinstance(values, list):
        return []
    return [target / value for value in values if isinstance(value, str) and value.strip()]


def configured_glob_paths(target: Path, values: Any) -> list[Path]:
    if not isinstance(values, list):
        return []
    paths: list[Path] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        paths.extend(path for path in target.glob(value) if path.is_file())
    return paths


def default_scan_paths(target: Path) -> list[Path]:
    paths: list[Path] = []
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in DEFAULT_EXCLUDES for part in path.relative_to(target).parts):
            continue
        paths.append(path)
    return paths


def unique_existing_files(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            continue
        seen.add(resolved)
        result.append(path)
    return sorted(result, key=lambda item: item.as_posix().casefold())


def add_required_file_findings(
    findings: list[Finding], target: Path, profile: str, config: dict[str, Any]
) -> None:
    defaults = ["README.md"] if profile == "web" else ["ORIGINAL.md", "README.md"]
    required = config.get("required_files", defaults)
    if not isinstance(required, list):
        findings.append(Finding("FAIL", "CFG002", "peakheadz_quality.json", "required_filesは配列にしてください"))
        return
    for value in required:
        if not isinstance(value, str) or not value.strip():
            findings.append(Finding("FAIL", "CFG003", "peakheadz_quality.json", "required_filesに不正な値があります"))
            continue
        path = target / value
        if path.is_file():
            findings.append(Finding("PASS", "CORE001", value, "必須ファイルがあります"))
        else:
            findings.append(Finding("FAIL", "CORE001", value, "必須ファイルがありません"))


def add_icon_findings(findings: list[Finding], target: Path, config: dict[str, Any]) -> None:
    values = config.get("icon_paths")
    if values is None:
        findings.append(Finding("WARN", "APP001", ".", "icon_pathsが未宣言のためアイコンを確認していません"))
        return
    paths = configured_paths(target, values)
    if not paths:
        findings.append(Finding("FAIL", "APP001", "peakheadz_quality.json", "icon_pathsに有効なpathがありません"))
        return
    existing = [path for path in paths if path.is_file()]
    if existing:
        shown = ", ".join(display_path(path, target) for path in existing)
        findings.append(Finding("PASS", "APP001", shown, "宣言されたアイコンがあります"))
    else:
        shown = ", ".join(display_path(path, target) for path in paths)
        findings.append(Finding("FAIL", "APP001", shown, "宣言されたアイコンがありません"))


def add_required_text_findings(findings: list[Finding], target: Path, config: dict[str, Any]) -> None:
    items = config.get("required_text", [])
    if not isinstance(items, list):
        findings.append(Finding("FAIL", "CFG004", "peakheadz_quality.json", "required_textは配列にしてください"))
        return
    cache: dict[Path, str] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("text"), str):
            findings.append(Finding("FAIL", "CFG005", "peakheadz_quality.json", f"required_text[{index}]が不正です"))
            continue
        path = target / item["path"]
        label = str(item.get("label") or item["text"])
        shown = display_path(path, target)
        if not path.is_file():
            findings.append(Finding("FAIL", "APP002", shown, f"{label}の確認先がありません"))
            continue
        try:
            text = cache.setdefault(path.resolve(), path.read_text(encoding="utf-8-sig", errors="replace"))
        except OSError as exc:
            findings.append(Finding("FAIL", "APP002", shown, f"{label}を確認できません: {exc}"))
            continue
        if item["text"] in text:
            findings.append(Finding("PASS", "CORE004", shown, f"{label}を確認しました"))
        else:
            findings.append(Finding("FAIL", "CORE004", shown, f"{label}がありません"))


def add_required_glob_text_findings(findings: list[Finding], target: Path, config: dict[str, Any]) -> None:
    items = config.get("required_text_globs", [])
    if not isinstance(items, list):
        findings.append(Finding("FAIL", "CFG007", "peakheadz_quality.json", "required_text_globsは配列にしてください"))
        return
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("glob"), str) or not isinstance(item.get("text"), str):
            findings.append(Finding("FAIL", "CFG008", "peakheadz_quality.json", f"required_text_globs[{index}]が不正です"))
            continue
        pattern = item["glob"]
        files = unique_existing_files(configured_glob_paths(target, [pattern]))
        label = str(item.get("label") or item["text"])
        if not files:
            findings.append(Finding("FAIL", "WEB001", pattern, f"{label}の検査対象がありません"))
            continue
        expected = item["text"]
        case_sensitive = bool(item.get("case_sensitive", True))
        missing: list[str] = []
        for path in files:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            found = expected in text if case_sensitive else expected.casefold() in text.casefold()
            if not found:
                missing.append(display_path(path, target))
        if missing:
            sample = ", ".join(missing[:5])
            suffix = "" if len(missing) <= 5 else f" ほか{len(missing) - 5}件"
            findings.append(Finding("FAIL", "WEB002", pattern, f"{label}がないfile: {sample}{suffix}"))
        else:
            findings.append(Finding("PASS", "WEB002", pattern, f"{label}を{len(files)} fileで確認しました"))


def add_source_findings(
    findings: list[Finding], target: Path, scan_paths: list[Path], user_text_paths: list[Path]
) -> None:
    for path in scan_paths:
        shown = display_path(path, target)
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as exc:
            findings.append(Finding("FAIL", "CORE002", shown, f"textを読み込めません: {exc}"))
            continue
        if path.suffix.lower() == ".py":
            try:
                ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                findings.append(Finding("FAIL", "APP003", shown, f"Python構文エラー: line {exc.lineno}"))
            else:
                findings.append(Finding("PASS", "APP003", shown, "Python構文を確認しました"))

        for label, pattern in FORBIDDEN_CREDITS.items():
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                findings.append(Finding("FAIL", "BRAND001", f"{shown}:{line}", f"利用者向け禁止クレジット候補: {label}"))

    user_set = {path.resolve() for path in user_text_paths}
    for path in scan_paths:
        if path.resolve() not in user_set:
            continue
        shown = display_path(path, target)
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        visible_text = text
        if path.suffix.lower() == ".py":
            try:
                tree = ast.parse(text, filename=str(path))
            except SyntaxError:
                tree = None
            if tree is not None:
                visible_text = "\n".join(
                    node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)
                )
        elif path.suffix.lower() == ".html":
            parser = VisibleHTMLParser()
            parser.feed(text)
            visible_text = parser.text()
        internal = INTERNAL_TERMS.search(visible_text)
        if internal:
            findings.append(Finding("WARN", "UX001", shown, f"利用者向け文字列の内部用語候補: {internal.group(0)}"))
        generic = GENERIC_ERROR_VALUE.search(text)
        if generic:
            line = text.count("\n", 0, generic.start()) + 1
            findings.append(Finding("WARN", "UX002", f"{shown}:{line}", "利用者向け表示が「エラー」だけになっている可能性があります"))


def run_checks(target: Path, profile: str, config_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not target.is_dir():
        return [Finding("FAIL", "CORE000", str(target), "対象directoryがありません")]
    try:
        config = load_config(config_path)
    except ValueError as exc:
        return [Finding("FAIL", "CFG001", display_path(config_path, target), str(exc))]

    configured_profile = config.get("profile")
    if configured_profile is not None and configured_profile != profile:
        findings.append(Finding("FAIL", "CFG006", display_path(config_path, target), f"設定profileは{configured_profile}、指定は{profile}です"))

    add_required_file_findings(findings, target, profile, config)
    if profile == "app":
        add_icon_findings(findings, target, config)
    add_required_text_findings(findings, target, config)
    add_required_glob_text_findings(findings, target, config)

    configured_scan = configured_paths(target, config.get("scan_paths")) + configured_glob_paths(target, config.get("scan_globs"))
    scan_paths = unique_existing_files(configured_scan or default_scan_paths(target))
    if not scan_paths:
        findings.append(Finding("WARN", "CORE003", ".", "text検査対象がありません"))
    user_text_paths = unique_existing_files(
        configured_paths(target, config.get("user_text_paths"))
        + configured_glob_paths(target, config.get("user_text_globs"))
    )
    if not user_text_paths:
        findings.append(Finding("WARN", "UX000", ".", "user_text_pathsが未宣言のためUI文章検査は限定的です"))
    add_source_findings(findings, target, scan_paths, user_text_paths)

    return sorted(
        findings,
        key=lambda item: (SEVERITY_ORDER[item.severity], item.code, item.path.casefold(), item.message),
    )


def emit(findings: list[Finding], as_json: bool) -> None:
    counts = {severity: sum(item.severity == severity for item in findings) for severity in ("PASS", "WARN", "FAIL")}
    if as_json:
        print(json.dumps({"summary": counts, "findings": [item.__dict__ for item in findings]}, ensure_ascii=False, indent=2))
        return
    for item in findings:
        print(f"{item.severity} {item.code} {item.path} - {item.message}")
    print(f"SUMMARY PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    target = args.target.resolve()
    config_path = (args.config or target / "peakheadz_quality.json").resolve()
    findings = run_checks(target, args.profile, config_path)
    emit(findings, args.as_json)
    return 1 if any(item.severity == "FAIL" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
