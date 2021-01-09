git checkout staging
git pull
cd lambda
call sam build --config-env staging --use-container
call sam deploy --config-env staging
cd ..
aws s3 sync web s3://stg-md-memo.tori-blog.net --delete
aws cloudfront create-invalidation --distribution-id EWVQGO1B7LR9X --paths "/*"