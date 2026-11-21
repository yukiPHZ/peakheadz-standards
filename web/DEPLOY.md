# Web DEPLOY

- Production source、生成手順、provider、branch、出力directoryは製品正本に従う。
- 共通化を理由に既存のdeploy方式、provider設定、secret、domainを変更しない。
- source test、生成、commit、push、providerのdeploy成功、公開URLのread-backを別の証拠として扱う。
- 生成物を持つ場合は、手編集せず製品の既存generatorを使う。
- 変更と関係のないPreview、Production、外部設定確認を毎回の必須gateにしない。
- Production操作は、依頼範囲と製品固有手順に含まれる時だけ行う。
