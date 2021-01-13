git checkout staging
git pull
cd lambda
call sam package --template-file template.yaml --output-template-file template-output.yaml --s3-bucket aws-sam-nested-application-packages-md-memo-stg
call sam deploy --template-file template-output.yaml --stack-name md-memo-stg --parameter-overrides Env=dev --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND
cd ..
aws s3 sync web s3://stg-md-memo.tori-blog.net --delete
aws cloudfront create-invalidation --distribution-id EWVQGO1B7LR9X --paths "/*"