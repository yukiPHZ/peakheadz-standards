# Pilot: dakeapp

## 対象

- Product: dakeapp
- Profile: `common + web + 製品固有`
- Public source: `public/`
- Deploy: 既存の静的Cloudflare Pages方式を維持

## 検査結果

- Web quality check: `PASS 26 / WARN 0 / FAIL 0`
- 既存Node test: `26 PASS`
- DAKE Network check: `11 items`
- AI_CONTEXT: 生成、決定論的再生成、stale checkを確認

## 実変更

- 既存の `ORIGINAL.md` を製品正本として、`AGENTS.md`、`STATE.md`、生成設定、品質設定を接続した。
- Windows checkoutのCRLFを内容差として扱っていたDAKE Network stale checkを、改行コードだけ正規化して比較するよう修正した。
- 公開UI、販売、決済、deploy方式、外部設定は変更していない。

## 発見と境界

- footerはDAKE Network正本から生成され、しまりす不動産の製品固有footerとは異なる。共通文言へ統一しない。
- `public/go/kaitori/` は恒久リダイレクトかつ `noindex` のため、通常コンテンツと同じfooter・descriptionを強制しない。
- 静的PagesとPages Functionsの差は製品固有であり、共通DEPLOYはsource・build・push・deploy・readbackを区別する原則だけを所有する。

## standardsへ戻したもの

- Web検査対象は製品設定で宣言し、構成差や意図された例外を共通FAILにしない方針を2サイトで確認した。
- footer、deploy provider、生成器の具体実装は製品固有として残した。
