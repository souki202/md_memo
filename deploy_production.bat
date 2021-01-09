git checkout master
git pull
cd lambda
call sam build --config-env staging
call sam deploy --config-env staging
cd ..
aws s3 sync web s3://prod-md-memo.tori-blog.net --delete
aws cloudfront create-invalidation --distribution-id E2KO2XM60TVSA0 --paths "/*"