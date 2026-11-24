# peakheadz-standards

PEAKHEADZ製品で繰り返し使う、開発・品質・文章・ブランドの共通正本です。

## 正本の境界

- このrepositoryは共通仕様と共通ツールだけを所有します。
- 製品固有の目的、必須挙動、現在地は各製品の正本に置きます。
- 共通仕様や `tools/` を製品repositoryへコピーしません。
- `AI_CONTEXT.md` は製品正本から生成する派生物です。直接編集しません。

## 構成

- `common/`: 全製品に共通する作業・環境・文章・ブランド
- `app/`: Windows / デスクトップアプリの共通仕様
- `web/`: Web製品の品質、UI、footer、deployに共通する境界
- `tools/doctor.py`: 開発環境・リポジトリ構造・認証経路をprofile別に簡易診断
- `tools/quality_check.py`: 製品をprofile別に検査
- `tools/generate_ai_context.py`: 指定した正本見出しからAI用入口を生成

## 基本コマンド

```powershell
python tools/doctor.py --profile local
python tools/doctor.py --profile github
python tools/doctor.py --profile cloudflare
python tools/doctor.py --profile all
python tools/quality_check.py <product-root> --profile app
python tools/quality_check.py <product-root> --profile web
python tools/generate_ai_context.py <product-root>
python tools/generate_ai_context.py <product-root> --check
```

各製品は必要に応じて `peakheadz_quality.json` と `AI_CONTEXT_SOURCES.json` を置きます。これらは共通仕様の複製ではなく、製品固有の検査対象と正本見出しを宣言する小さな設定です。

## Version

基準点: `v1.0.0`

App 1製品とWeb 2製品で、`common`、profile、製品固有正本、quality check、AI contextの境界を実証した初回安定版です。今後は実運用で必要性が確認できた変更だけを加えます。

実証結果は `PILOT_DAKE_PDF_CHECKSTAMP.md`、`PILOT_SHIMARISU_REAL_ESTATE.md`、`PILOT_DAKEAPP.md` に簡潔に記録しています。
