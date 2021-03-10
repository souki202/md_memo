import Cookies from './js.cookie.min';

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