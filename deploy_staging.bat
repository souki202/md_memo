git checkout staging
cd lambda
sam build --config-env staging
sam deploy --config-env staging
cd ..
aws s3 sync web s3://stg-md-memo.tori-blog.net --delete