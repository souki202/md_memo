git checkout master
git pull
cd lambda
call sam build --config-env staging --use-container
call sam deploy --config-env staging
call sam build --config-env staging --use-container -t file_api_template.yaml --config-file file_api_samconfig.toml
call sam deploy --config-env staging -t file_api_template.yaml --config-file file_api_samconfig.toml
cd ..
aws s3 sync web s3://prod-md-memo.tori-blog.net --delete
aws cloudfront create-invalidation --distribution-id E2KO2XM60TVSA0 --paths "/*"