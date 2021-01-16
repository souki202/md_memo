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

`aws dynamodb create-table --cli-input-json "file://D:\Projects\md_memo\lambda\task\local\scheme\trash_overviews.json"`

`aws dynamodb create-table --cli-input-json "file://D:\Projects\md_memo\lambda\task\staging\scheme\overviews.json"`

### lambdaのテスト

`sam local invoke "DeleteMemoFunction" -e events/post.json --config-env develop -n env/env.json`

`sam local invoke "GetFileFunction" -e events/post.json --config-env develop -n env/env.json -t file_api_template.yaml --config-file file_api_samconfig.toml -b .aws-sam-file-api/build`

### apiの開始

`sam build --config-env staging`

`sam local start-api -t template.yaml`

## デプロイ

### dev

requiementsの追加があればwslに入って

```shell
cd /mnt/d/Projects/md_memo/lambda/my_layer
pip3 install -r requirements.txt -t ../my_layer_libs/python
```

`sam package --template-file template.yaml --output-template-file template-output.yaml --s3-bucket aws-sam-nested-application-packages-md-memo-dev`

`sam deploy --template-file template-output.yaml --stack-name md-memo-dev --parameter-overrides Env=dev --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND`

### staging

`sam package --template-file template.yaml --output-template-file template-output.yaml --s3-bucket aws-sam-nested-application-packages-md-memo-stg`

`sam deploy --template-file template-output.yaml --stack-name md-memo-stg --parameter-overrides Env=stg --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND`

### production

`sam package --template-file template.yaml --output-template-file template-output.yaml --s3-bucket aws-sam-nested-application-packages-md-memo-prod`

`sam deploy --template-file template-output.yaml --stack-name md-memo-prod --parameter-overrides Env=prod --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND`

#### prodデプロイ時チェック

DynamoDBへの追加

* テーブル追加
* GSI追加, 変更
  * 変更時は, 新しく作成してから消す

## その他

### dynamodb

予約語一覧

<https://docs.aws.amazon.com/ja_jp/amazondynamodb/latest/developerguide/ReservedWords.html>

### axios

各メソッド別の引数

<https://qiita.com/terufumi1122/items/670b1008956428a8cc8c>

### cookie

<https://pizzamanz.net/web/javascript/js-cookie/>

### vue

* vue-multiselect
  * <https://vue-multiselect.js.org>
