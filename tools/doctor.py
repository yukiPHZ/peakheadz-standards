#!/usr/bin/env python3
"""PEAKHEADZ Development Environment Doctor.

Read-only diagnostics for local workspace, Git configuration, and external services.
Does not perform login, logout, token generation, credential changes, or file mutations.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

SEVERITY_ORDER = {"FAIL": 0, "WARN": 1, "PASS": 2}
CANONICAL_DEV_ROOT = Path("C:/Users/yukiz/devlop")


@dataclass(frozen=True)
class DoctorItem:
    severity: str  # PASS, WARN, FAIL
    category: str  # local, github, cloudflare, web
    name: str
    message: str
    remediation: str = ""


CommandRunner = Callable[[Sequence[str], Path | None], tuple[int, str, str]]


def default_command_runner(cmd: Sequence[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        resolved_cmd = list(cmd)
        if platform.system() == "Windows":
            target_bin = shutil.which(resolved_cmd[0]) or resolved_cmd[0]
            if str(target_bin).lower().endswith((".cmd", ".bat")):
                resolved_cmd = ["cmd.exe", "/c", target_bin, *resolved_cmd[1:]]
        proc = subprocess.run(
            resolved_cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            shell=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, "", str(exc)


def check_local(
    target: Path,
    runner: CommandRunner = default_command_runner,
    dev_root: Path = CANONICAL_DEV_ROOT,
) -> list[DoctorItem]:
    items: list[DoctorItem] = []

    # 1. Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        items.append(DoctorItem("PASS", "local", "Python runtime", f"Python {py_ver} ({platform.system()})"))
    else:
        items.append(
            DoctorItem(
                "FAIL",
                "local",
                "Python runtime",
                f"Python {py_ver} は非推奨です（3.10以上が必要）",
                "Python 3.10以降をインストールしてください",
            )
        )

    # 2. Development root check
    target_resolved = target.resolve()
    try:
        dev_root_resolved = dev_root.resolve()
        is_under_dev = target_resolved == dev_root_resolved or dev_root_resolved in target_resolved.parents
    except OSError:
        is_under_dev = False

    if is_under_dev:
        items.append(DoctorItem("PASS", "local", "Development root", f"正規開発ルート配下: {target_resolved}"))
    else:
        items.append(
            DoctorItem(
                "WARN",
                "local",
                "Development root",
                f"標準外のパスです: {target_resolved}",
                f"標準の開発ルートは {dev_root} 配下です",
            )
        )

    # 3. Workspace structure (normal clone vs worktree)
    git_entry = target / ".git"
    if not git_entry.exists():
        items.append(
            DoctorItem(
                "WARN",
                "local",
                "Workspace type",
                "Git管理下ではありません（.git が存在しません）",
                "Git repository内で実行するか、git init / clone を確認してください",
            )
        )
    elif git_entry.is_dir():
        items.append(DoctorItem("PASS", "local", "Workspace type", "通常のGit working copy (.git ディレクトリ)"))
    else:
        # .git is a file, indicating a git worktree or submodule
        try:
            content = git_entry.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            content = ""
        items.append(
            DoctorItem(
                "WARN",
                "local",
                "Workspace type",
                f"Git worktree が検出されました ({content})",
                "PEAKHEADZ標準では通常開発でworktreeを使用せず、同一フォルダ内ブランチ作業を推奨します",
            )
        )

    # 4. Git availability & dubious ownership check
    git_bin = shutil.which("git")
    if not git_bin:
        items.append(
            DoctorItem(
                "FAIL",
                "local",
                "Git availability",
                "git コマンドが見つかりません",
                "Gitをインストールし、PATHを通してください",
            )
        )
        return items

    code, out, _ = runner(["git", "--version"], target)
    if code == 0:
        items.append(DoctorItem("PASS", "local", "Git availability", out))
    else:
        items.append(DoctorItem("FAIL", "local", "Git availability", "git --version の実行に失敗しました"))

    # Check git status for dubious ownership
    if git_entry.exists():
        code, out, err = runner(["git", "status", "--porcelain"], target)
        combined = f"{out}\n{err}"
        if "dubious ownership" in combined.lower():
            items.append(
                DoctorItem(
                    "FAIL",
                    "local",
                    "Git ownership",
                    "Git所有者権限の不一致（dubious ownership）が検出されました",
                    "Preferred: Windows NTFS所有者を正規ユーザーへ正常化 / Fallback: safe.directory個別登録 / Avoid: safe.directory=*",
                )
            )
        elif code == 0:
            items.append(DoctorItem("PASS", "local", "Git ownership", "リポジトリ所有者・安全設定は正常です"))
        else:
            items.append(DoctorItem("WARN", "local", "Git ownership", f"git status 実行時にエラーが発生しました: {err}"))

    return items


def check_github(
    target: Path,
    runner: CommandRunner = default_command_runner,
    env: dict[str, str] | None = None,
) -> list[DoctorItem]:
    items: list[DoctorItem] = []
    environ = env if env is not None else os.environ

    # 1. gh CLI availability
    gh_bin = shutil.which("gh")
    if not gh_bin:
        items.append(
            DoctorItem(
                "FAIL",
                "github",
                "GitHub CLI",
                "gh CLI がインストールされていないか、PATHに存在しません",
                "GitHub CLI (gh) をインストールしてください",
            )
        )
        return items

    code, out, _ = runner(["gh", "--version"], target)
    gh_version = out.splitlines()[0] if out else "installed"
    items.append(DoctorItem("PASS", "github", "GitHub CLI", gh_version))

    # 2. gh auth status (read-only)
    code, out, err = runner(["gh", "auth", "status"], target)
    combined = f"{out}\n{err}"
    if code == 0 and "Logged in to github.com" in combined:
        # Extract account info safely without secrets
        account_line = "Logged in to github.com"
        for line in combined.splitlines():
            if "Logged in to github.com account" in line:
                account_line = line.strip()
                break
        items.append(DoctorItem("PASS", "github", "GitHub auth", account_line))
    else:
        items.append(
            DoctorItem(
                "FAIL",
                "github",
                "GitHub auth",
                "gh auth status でログイン状態が確認できませんでした",
                "gh auth login でHTTPS/Credential Managerによる標準認証を確認してください",
            )
        )

    # 3. Git remote protocol
    code, out, _ = runner(["git", "config", "--get", "remote.origin.url"], target)
    if code == 0 and out:
        remote_url = out.strip()
        if remote_url.startswith("https://"):
            items.append(DoctorItem("PASS", "github", "Git remote", f"標準HTTPSプロトコル: {remote_url}"))
        elif remote_url.startswith("git@") or remote_url.startswith("ssh://"):
            items.append(
                DoctorItem(
                    "WARN",
                    "github",
                    "Git remote",
                    f"SSHプロトコルが設定されています: {remote_url}",
                    "PEAKHEADZの標準経路はHTTPSです。明示設定がない場合はHTTPSを推奨します",
                )
            )
        else:
            items.append(DoctorItem("WARN", "github", "Git remote", f"非標準リモート: {remote_url}"))
    else:
        items.append(DoctorItem("WARN", "github", "Git remote", "remote.origin.url が設定されていません"))

    # 4. Environment variable conflict check (NEVER print values)
    gh_token_set = bool(environ.get("GH_TOKEN"))
    github_token_set = bool(environ.get("GITHUB_TOKEN"))
    if gh_token_set or github_token_set:
        items.append(
            DoctorItem(
                "WARN",
                "github",
                "Auth conflict",
                "GH_TOKEN または GITHUB_TOKEN 環境変数が設定されています（値は非表示）。保存済みOAuth認証より優先される可能性があります",
                "不要なトークン競合を防ぐため、標準認証（keyring/GCM）を使用する場合は環境変数の整理を検討してください",
            )
        )
    else:
        items.append(DoctorItem("PASS", "github", "Auth conflict", "環境変数トークンによる認証競合はありません"))

    return items


def check_cloudflare(
    target: Path,
    runner: CommandRunner = default_command_runner,
    env: dict[str, str] | None = None,
) -> list[DoctorItem]:
    items: list[DoctorItem] = []
    environ = env if env is not None else os.environ

    # 1. Wrangler availability
    wrangler_bin = shutil.which("wrangler")
    wrangler_cmd = ["wrangler"]
    if not wrangler_bin:
        # Check if npx is available
        if shutil.which("npx"):
            wrangler_cmd = ["npx", "--no-install", "wrangler"]
        else:
            items.append(
                DoctorItem(
                    "FAIL",
                    "cloudflare",
                    "Wrangler CLI",
                    "wrangler または npx が見つかりません",
                    "npm i -g wrangler 等で Wrangler CLI を利用可能にしてください",
                )
            )
            return items

    code, out, _ = runner([*wrangler_cmd, "--version"], target)
    if code == 0 and out:
        wrangler_ver = out.splitlines()[0]
        items.append(DoctorItem("PASS", "cloudflare", "Wrangler CLI", f"Wrangler {wrangler_ver}"))
    else:
        items.append(DoctorItem("FAIL", "cloudflare", "Wrangler CLI", "wrangler --version に失敗しました"))
        return items

    # 2. Wrangler whoami (read-only auth check)
    code, out, err = runner([*wrangler_cmd, "whoami"], target)
    combined = f"{out}\n{err}"
    if code == 0 and ("logged in" in combined.lower() or "account name" in combined.lower()):
        # Extract safe account description
        account_info = "Logged in via OAuth"
        for line in combined.splitlines():
            if "associated with the email" in line:
                account_info = line.strip()
                break
            elif "Account Name" in line or "Account ID" in line:
                account_info = "OAuth token active"
        items.append(DoctorItem("PASS", "cloudflare", "Cloudflare auth", account_info))
    else:
        items.append(
            DoctorItem(
                "FAIL",
                "cloudflare",
                "Cloudflare auth",
                "wrangler whoami で認証状態が確認できませんでした",
                "wrangler login を実行してOAuth認証を完了してください",
            )
        )

    # 3. Environment variables conflict check (NEVER print values)
    api_token_set = bool(environ.get("CLOUDFLARE_API_TOKEN"))
    api_key_set = bool(environ.get("CLOUDFLARE_API_KEY"))
    if api_token_set or api_key_set:
        items.append(
            DoctorItem(
                "WARN",
                "cloudflare",
                "Auth conflict",
                "CLOUDFLARE_API_TOKEN または CLOUDFLARE_API_KEY 環境変数が設定されています（値は非表示）。OAuth認証と競合する可能性があります",
                "OAuthによる標準認証を主とする場合、環境変数の優先順位に注意してください",
            )
        )
    else:
        items.append(DoctorItem("PASS", "cloudflare", "Auth conflict", "環境変数によるCloudflare認証競合はありません"))

    return items


def check_web(
    target: Path,
    runner: CommandRunner = default_command_runner,
    env: dict[str, str] | None = None,
) -> list[DoctorItem]:
    items: list[DoctorItem] = []
    items.extend(check_local(target, runner))

    # Inspect target for Wrangler configurations
    wrangler_configs = ["wrangler.json", "wrangler.jsonc", "wrangler.toml"]
    has_cf_config = any((target / cfg).exists() for cfg in wrangler_configs)
    if has_cf_config:
        items.extend(check_cloudflare(target, runner, env))

    # Inspect target for git remote pointing to GitHub
    code, out, _ = runner(["git", "config", "--get", "remote.origin.url"], target)
    if code == 0 and "github.com" in out:
        items.extend(check_github(target, runner, env))

    return items


def run_doctor(
    target: Path,
    profile: str = "local",
    runner: CommandRunner = default_command_runner,
    env: dict[str, str] | None = None,
) -> list[DoctorItem]:
    target = target.resolve()
    if profile == "local":
        return check_local(target, runner)
    elif profile == "github":
        return check_github(target, runner, env)
    elif profile == "cloudflare":
        return check_cloudflare(target, runner, env)
    elif profile == "web":
        return check_web(target, runner, env)
    elif profile == "all":
        items = []
        items.extend(check_local(target, runner))
        items.extend(check_github(target, runner, env))
        items.extend(check_cloudflare(target, runner, env))
        return items
    else:
        raise ValueError(f"未知のprofileです: {profile}")


def render_report(items: Sequence[DoctorItem], profile: str) -> str:
    lines = [f"PEAKHEADZ Development Doctor (profile: {profile})", ""]
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}

    for item in items:
        counts[item.severity] = counts.get(item.severity, 0) + 1
        tag = f"[{item.severity}]"
        lines.append(f"{tag:<8} {item.name:<22} {item.message}")
        if item.remediation and item.severity in {"WARN", "FAIL"}:
            lines.append(f"         対処: {item.remediation}")

    lines.append("")
    summary = f"Doctor summary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL"
    lines.append(summary)
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PEAKHEADZ development environment diagnostics.")
    parser.add_argument("target", nargs="?", default=".", type=Path, help="Target workspace path (default: .)")
    parser.add_argument(
        "--profile",
        choices=("local", "github", "cloudflare", "web", "all"),
        default="local",
        help="Diagnostic profile (default: local)",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.target.resolve()
    try:
        items = run_doctor(target, profile=args.profile)
    except Exception as exc:  # noqa: BLE001
        print(f"doctor 実行中にエラーが発生しました: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        data = {
            "profile": args.profile,
            "target": str(target),
            "findings": [asdict(item) for item in items],
            "passed": all(item.severity != "FAIL" for item in items),
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_report(items, args.profile))

    # Exit code: 1 if any FAIL, 0 otherwise
    return 1 if any(item.severity == "FAIL" for item in items) else 0


if __name__ == "__main__":
    sys.exit(main())
