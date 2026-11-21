# Web QUALITY

Web製品で機械検査しやすい共通品質を定めます。実際の公開directory、生成元、必須asset、metadata、footerは製品ごとに異なるため、製品の `peakheadz_quality.json` で検査対象を宣言します。

## FAILにできる項目

- 製品が宣言した公開source、必須ファイル、favicon、apple-touch-icon、manifest等がない。
- 製品が検査対象として宣言したHTMLに、title、description、canonical等の必須文字列がない。
- 利用者向け公開物に禁止クレジットがある。
- Production sourceやdeploy出力の明確な設定が、製品正本と一致しない。

## WARNにする項目

- 公開文章に内部用語や強すぎる表現がある可能性がある。
- 文脈判断が必要なfooter表現、導線、表記揺れがある。
- 製品設定がなく、公開文章の確認範囲を特定できない。

## 検査境界

- すべてのWebサイトへ同じframework、directory、icon形式、footer文面を強制しない。
- 生成HTMLを持つ製品では、生成元と生成検査を製品正本に従って扱う。
- source検査、build、Preview、Production deploy、公開URL確認を別の証拠として扱う。
- `WARN` を理由に文章や構造を自動変更しない。
