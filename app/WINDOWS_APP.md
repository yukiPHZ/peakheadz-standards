# WINDOWS_APP

Windowsアプリへ共通化できる範囲だけを定めます。

## 配布と表示

- 製品正本が指定するアイコンをsourceとbuildで一貫して使う。
- sourceまたはbuild設定上のアイコン指定だけで、生成exeへの反映完了を保証しない。
- アイコンの生成・埋め込み方式を変更した時、または正式配布の確認が必要な時は、生成されたexeそのものでも意図したアイコンを確認する。
- アイコンのsource、build設定、生成exeは別の証拠として扱う。
- source quality checkのPASSで、生成exeのアイコン、実機GUI、署名、外部配布の確認を代替しない。
- 利用者へ開発用Pythonや手動の依存配置を要求しない配布を基本とする。
- Windows固有設定は既存の正常なbuild方式を尊重し、目的なく変更しない。

## exe metadata

既存製品の確定値を優先し、未確定の場合は次を基本形とします。

- CompanyName: `PEAKHEADZ`
- Author: `Yukihiko Kikuta`
- Copyright: `© Yukihiko Kikuta / PEAKHEADZ`
- FileVersion / ProductVersion: 製品正本のversion
- ProductName / FileDescription / OriginalFilename: 製品正本の値

metadataの生成方式を変えた時は実exeで確認します。source上の設定確認だけで配布exeへの反映を保証しません。
