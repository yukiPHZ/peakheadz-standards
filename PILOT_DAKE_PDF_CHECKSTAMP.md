# Dake確認印 Pilot

Phase 1〜5の実証記録です。長期仕様は各正本へ置き、この文書には実証で得た判断だけを残します。

## 対象と範囲

- 対象: `dake-series/01_apps/DAKE_PDF_CheckStamp`
- profile: `common + app + 製品固有`
- 小規模変更: 旧作者クレジットを確定表記へ変更し、単独の「エラー」見出しを穏やかな案内へ変更
- 対象外: PDF処理、依存、build方式、exe生成、release、販売、Web

## 実証結果

- 初回quality check: `FAIL 2 / WARN 1`。未確定Copyright、禁止クレジット、単独のエラー表現を検出。
- 修正後quality check: `PASS 18 / WARN 0 / FAIL 0`。共有generatorのCompanyNameとexe Copyrightも確認。
- AI context: 46行。指定した6見出しだけを抽出し、全文連結・生成日時・commit hashを含めていない。
- 共通ツールtest: 3件PASS。
- 製品固有test: 2件PASS。確定UI表記と、合成1-page PDFへの確認印保存・元PDF hash維持を確認。Python構文checkもPASS。
- build済みexeと実機GUIは未確認。source検査のPASSと分離した。

## 基盤へ戻した修正

- monorepo内製品が共有アイコンを参照できるよう、検査対象pathを製品設定で宣言可能にした。
- Pythonの内部構文にある `Exception` をUI文言と誤判定しないよう、UX候補検査は文字列literalへ限定した。
- 製品固有の必須ファイル・build文字列を共通checkerへhard-codeせず、`peakheadz_quality.json` へ分離した。
- AI contextは見出し単位の明示抽出とし、同じ入力から同じcontent hashを生成するようにした。

## 判定

Phase 1〜5のapp実証に必要な基盤は成立した。Web仕様は器だけであり、Phase 6へ自動的には進めない。
