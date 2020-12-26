import '/js/js.cookie.min.js';

function applyTheme(theme) {
	var el = document.createElement('link');
	el.href = '/css/theme/' + theme + '.css';
	el.rel = 'stylesheet';
	el.type = 'text/css';
	document.getElementsByTagName('head')[0].appendChild(el);
}

function getTheme() {
    const theme = Cookies.get('theme');
    if (!theme || theme == 'light') {
        return 'light';
    }
    else {
        return 'dark'
    }
}

(() => {
    applyTheme(getTheme());
})();

export default getTheme