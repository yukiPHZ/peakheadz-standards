# しまりす不動産 Web Pilot

## 対象

- Repository: `yukiPHZ/shimarisu-site`
- Profile: `common + web + 製品固有`
- Production source: `public/`
- Deploy: Cloudflare Pages + Pages Functions

## 検査結果

- 既存Node検査: 30件PASS
- Web quality check: `PASS 27 / WARN 0 / FAIL 0`
- AI_CONTEXT: 57行。再生成後stale check PASS
- 公開HTML: 39 fileでlang、title、description、canonical、footerを確認

## 実変更

- `ORIGINAL.md`、`AGENTS.md`、`STATE.md`、製品固有checker設定を追加。
- 指定見出しだけから `AI_CONTEXT.md` を生成。
- 公開HTML、UI、deploy構成、Cloudflare設定は変更していない。

## standardsへ戻した変更

- `scan_globs` / `user_text_globs` により、製品が宣言した公開範囲だけを検査できるようにした。
- `required_text_globs` により、宣言したHTML集合の必須文字列を安定して確認できるようにした。
- HTMLのUX候補検査はscript/styleを除いた可視文字列だけを対象にした。
- Web共通仕様は、製品固有構成を設定で宣言し、同じfooterやdirectoryを強制しない形にした。

## 製品固有として残したもの

- しまりす不動産が情報メディアであり宅建業者ではないこと。
- 一般記事と株式会社さくら都市の査定導線の境界。
- `public/`、Pages Functions、Turnstile、Market Observer、実務ノート生成構造。
- footerへ人物名・プロフィール導線を置かない既存policy。

Phase 6時点ではWeb標準を完成扱いにせず、dakeappで再実証する。
