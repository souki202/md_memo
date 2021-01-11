# 開発周り

## 各種URL

<https://dev-md-memo.tori-blog.net/>

<https://stg-md-memo.tori-blog.net/>

<https://md-memo.tori-blog.net/>

## ローカル環境

### ドメイン

`dev-md-memo.tori-blog.net`

`C:\Windows\System32\drivers\etc\hosts`に`127.0.0.1 dev-md-memo.tori-blog.net`を追加

### dynamodb

テーブル作成

`aws dynamodb create-table --cli-input-json "file://D:\Projects\md_memo\lambda\task\staging\scheme\table.json"`

### lambdaのテスト

`sam local invoke "DeleteMemoFunction" -e events/post.json --config-env develop -n env/env.json`

`sam local invoke "GetFileFunction" -e events/post.json --config-env develop -n env/env.json -t file_api_template.yaml --config-file file_api_samconfig.toml`

### apiの開始

`sam build --config-env staging`

`sam local start-api -t template.yaml`

## デプロイ

### dev

`sam build --config-env develop --use-container -t file_api_template.yaml --config-file file_api_samconfig.toml`

`sam deploy --config-env develop -t file_api_template.yaml --config-file file_api_samconfig.toml`

### staging

`sam build --config-env staging --use-container`

`sam deploy --config-env staging`

### production

`sam build --config-env production --use-container`

`sam deploy --config-env production`

## その他

### dynamodb

予約語一覧

<https://docs.aws.amazon.com/ja_jp/amazondynamodb/latest/developerguide/ReservedWords.html>

### axios

各メソッド別の引数

<https://qiita.com/terufumi1122/items/670b1008956428a8cc8c>

### cookie

<https://pizzamanz.net/web/javascript/js-cookie/>