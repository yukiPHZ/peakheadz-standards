# Web ASSETS

favicon、apple-touch-icon、OGP画像など、Web製品で共有するassetの最小要件です。図案、色、素材、ファイル名、配置は製品正本で決めます。

## favicon / app icon

- 16px / 32pxで識別できることを基準にする。
- SVGを優先し、必要なら `favicon.ico` を併置する。
- iOS向けに `apple-touch-icon` を用意する。
- PWA対応製品ではmanifestのicon指定も確認する。
- 文字列を詰め込まず、暗い背景・明るい背景の両方で潰れないことを確認する。
- 配置は製品の公開sourceに従う。共通のdirectory名を強制しない。

```html
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

## OGP / share image

- 基本サイズは `1200x630`。
- `og:image` には公開URLの絶対パスを指定する。
- 画像内の文字は製品名または短い言葉までに抑える。
- 機能説明、料金、CTAを画像へ詰め込まない。
- faviconと空気感を揃え、製品の世界観を優先する。

```html
<meta property="og:image" content="https://example.com/assets/og/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

## 境界

- 図案、色、撮影素材、生成方法、ファイル名、配置は製品正本で決める。
- assetの存在検査は `QUALITY.md` と製品の `peakheadz_quality.json` に従う。
- 共通化を理由に、既存製品のfaviconやOGPを一括で作り直さない。
