export default function () {
    const domain = document.domain
    console.log(domain)

    switch (domain) {
        case 'localhost':
        case '127.0.0.1':
        case 'dev-md-memo.tori-blog.net':
            // return'http://127.0.0.1:3000';
            return'https://fileapi.dev-md-memo.tori-blog.net';
        break;
        default:
            return 'https://' + 'fileapi.' + domain;
        break;
    }
}