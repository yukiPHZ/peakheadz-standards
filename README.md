# peakheadz-standards

PEAKHEADZ製品で繰り返し使う、開発・品質・文章・ブランドの共通正本です。

## 正本の境界

- このrepositoryは共通仕様と共通ツールだけを所有します。
- 製品固有の目的、必須挙動、現在地は各製品の正本に置きます。
- 共通仕様や `tools/` を製品repositoryへコピーしません。
- `AI_CONTEXT.md` は製品正本から生成する派生物です。直接編集しません。

## 構成

- `common/`: 全製品に共通する作業・文章・ブランド
- `app/`: Windows / デスクトップアプリの共通仕様
- `web/`: 将来のWeb実証用の最小の器。現時点ではWeb品質を確定しません
- `tools/quality_check.py`: 製品をprofile別に検査
- `tools/generate_ai_context.py`: 指定した正本見出しからAI用入口を生成

## 基本コマンド

```powershell
python tools/quality_check.py <product-root> --profile app
python tools/generate_ai_context.py <product-root>
python tools/generate_ai_context.py <product-root> --check
```

各製品は必要に応じて `peakheadz_quality.json` と `AI_CONTEXT_SOURCES.json` を置きます。これらは共通仕様の複製ではなく、製品固有の検査対象と正本見出しを宣言する小さな設定です。

## Version

初版: `1.0.0`
