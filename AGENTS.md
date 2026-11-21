# peakheadz-standards: Codex作業入口

最初に `README.md` と `common/AI_WORKFLOW.md` を読み、変更対象に対応する `common/` またはprofile仕様だけを追加で読みます。

- 共通仕様へ製品固有ルールを混ぜません。
- 共通仕様や `tools/` を製品repositoryへコピーする方式へ変えません。
- `AI_CONTEXT.md` の直接編集を認めません。
- checkerの `FAIL` は機械判定できる違反、`WARN` は文脈確認が必要な候補に限定します。
- tool変更後は `python -m unittest discover -s tests -v` を実行します。
- `web/` は実製品で確認した共通事項だけを扱い、将来用途を想像して拡張しません。
