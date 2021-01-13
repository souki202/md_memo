git checkout master
git pull
cd lambda
call sam package --template-file template.yaml --output-template-file template-output.yaml --s3-bucket aws-sam-nested-application-packages-md-memo-prod
call sam deploy --template-file template-output.yaml --stack-name md-memo-prod --parameter-overrides Env=prod --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND
cd ..
aws s3 sync web s3://prod-md-memo.tori-blog.net --delete
aws cloudfront create-invalidation --distribution-id E2KO2XM60TVSA0 --paths "/*"