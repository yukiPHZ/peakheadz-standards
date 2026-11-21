# v1 Validation

`v1.0.0` は永久不変を意味せず、通常利用に入れる初回安定基準点です。

## 実証範囲

- App: Dake確認印 — `common + app + 製品固有`
- Web: しまりす不動産 — `common + web + 製品固有`
- Web: dakeapp — `common + web + 製品固有`

3製品で共通ツールをrepository外から使用し、AI_CONTEXT生成・stale checkとprofile別quality checkを確認しました。

## v1で共通化したもの

- 既存尊重、依頼範囲、正本と派生物、完了条件
- 利用者向け文章と禁止クレジットの共通原則
- 製品設定で宣言した対象をprofile別に検査する仕組み
- 見出しを明示選択する決定論的AI_CONTEXT生成
- Webのsource・生成・push・deploy・公開確認を分ける証拠境界

## 製品固有に残したもの

- favicon、manifest、footerの実ファイル・文言・導線
- provider、Functions、外部設定、生成器の具体手順
- Appのbuild、exe metadata、配布工程の製品値
- 情報サイト、恒久redirect、生成ページ等の意図された例外

Phase 9の既存製品横展開はこの基準点に含みません。
