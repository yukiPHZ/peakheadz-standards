# DEVELOPMENT_ENVIRONMENT

PEAKHEADZにおけるローカル開発環境・リポジトリ配置・外部接続経路の共通正本です。作業者は推測で環境構造や認証方式を変更せず、この基準に従います。

## 開発ディレクトリ配置

### Development Root
- 正式な通常開発ルート: `C:\Users\yukiz\devlop\`
- 新規repositoryは原則として `C:\Users\yukiz\devlop\<repo>\` 直下へcloneまたは作成します。
- 既存monorepo内の新規製品は、そのrepoの定めたディレクトリ配下へ作成します。
- `C:\Users\yukiz\Documents\` は通常の開発ルートとして使用しません。

### 1 repo = 1 folder 原則
- 原則: `1 GitHub repository = 1 local working copy = C:\Users\yukiz\devlop\<repo>\`
- 同一repositoryの重複clone（別名フォルダ、別階層への多重clone）を作成しません。

### Worktree の禁止
- 通常の開発作業においてGit worktreeを使用しません。
- `_worktrees`、`_wt`、`.codex_worktrees` などを新規開発の作業経路として作成しません。
- feature branch作業は同一repositoryフォルダ内で行います（`git checkout -b <branch>`）。
- 過去の残存worktreeは、未コミット変更の安全確認およびリモートマージ状態を確認した上で順次削除・pruneします。

### 一時ファイルとゴミの排除
- 一時生成物は、各repository内の明示された `.gitignore` 対象ディレクトリまたはOSのテンポラリ（`%TEMP%`）を使用します。
- `devlop` 直下へ無秩序な一時フォルダ（`tmp`、`backup`、`copy`、`old`、`new`、`work` など）を作成しません。

### 秘密情報の取り扱い
- APIキー、トークン、リカバリーコード、パスワード等の秘密情報を `C:\Users\yukiz\devlop\` 直下に平文保存しません。
- 秘密情報の値をログ、Markdown、doctor出力、コミット差分に表示・記録しません。

## 外部サービス認証標準経路

### GitHub 標準経路
- 標準接続方式:
  ```text
  git / gh CLI
  ↓
  GitHub CLI 認証 (gh auth)
  ↓
  Windows Credential Manager (manager)
  ↓
  GitHub (HTTPS)
  ```
- 現在の正常アカウント: `yukiPHZ`（HTTPS）
- 環境変数 `GH_TOKEN` / `GITHUB_TOKEN` が設定されている場合は優先されるため、競合に注意します（値は表示しない）。
- 禁止事項:
  - 正常な認証経路が存在する場面で、新トークンを生成したり別トークンを探索したりしない。
  - 勝手にSSHへ切り替えたり、プロトコルを一括変更したりしない。
  - トークン不整合を理由に無秩序にMCPへフォールバックしない。

### Cloudflare 標準経路
- 標準接続方式:
  ```text
  Wrangler CLI
  ↓
  OAuth ログイン (wrangler login)
  ↓
  OS keyring / credential storage
  ↓
  Cloudflare
  ```
- 現在の正常アカウント: `daleyuki@gmail.com`
- 環境変数 `CLOUDFLARE_API_TOKEN`、`CLOUDFLARE_API_KEY` 等が存在する場合、OAuthと競合する可能性があるため存在有無を確認します（値は表示しない）。
- 勝手に新規ログインセッションを開始したり、APIキーをハードコードしたりしない。

### MCP (Model Context Protocol) の境界
- 通常のローカル開発・Git操作・Cloudflare操作の標準経路にMCPを含めません。
- 標準経路は常に `git` / `gh` および `Wrangler` です。
- MCPは、外部連携機能として明確に指定された案件に限り使用します。

## Git 所有者権限（Dubious Ownership）の対処順位

Codex sandbox環境等の別Windowsユーザーが `.git` を生成・変更した場合、Gitのセキュリティ保護（CVE-2022-24765）により `fatal: detected dubious ownership` が発生することがあります。この場合の対処順位は以下の通りです。

1. **Preferred（最優先・恒久対策）**:
   - Windows NTFS所有者 / ACLの正常化。
   - 対象リポジトリの `.git` ディレクトリおよび作業ツリーの所有者を、現在の主ログインユーザー（`yukiz`）へ整流化します。所有者が一致すれば `safe.directory` 設定自体が不要になります。
2. **Fallback（代替案）**:
   - リポジトリ単位の個別登録。
   - `git config --global --add safe.directory <path>` により、必要なリポジトリの絶対パスのみを個別追加します。
3. **Avoid（禁止・非推奨）**:
   - `git config --global --add safe.directory "*"`（ワイルドカード全面許可）。
   - 全リポジトリの安全保護を無効化する重大なセキュリティリスクとなるため、避けます。
