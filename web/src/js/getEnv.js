export default function () {
    const domain = document.domain
    console.log(domain)

    switch (domain) {
        case 'localhost':
        case '127.0.0.1':
        case 'dev-md-memo.tori-blog.net':
            return'dev';
        break;
        case 'stg-md-memo.tori-blog.net':
            return 'stg'
        case 'memo-ease.com':
            return 'prod';
        default:
            return 'prod';
        break;
    }
}