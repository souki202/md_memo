import '/js/js.cookie.min.js';

function getTheme() {
    const theme = Cookies.get('theme');
    if (!theme || theme == 'light') {
        return 'light';
    }
    else {
        return 'dark'
    }
}

export default getTheme