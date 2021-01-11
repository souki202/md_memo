function loadCommonParts(url, insertTarget) {
    if (!insertTarget) return;
    let xhr = new XMLHttpRequest();
    const method = "GET";

    xhr.open(method, url, true);
    xhr.onreadystatechange = function () {
        if(xhr.readyState === 4 && xhr.status === 200) {
            var restxt = xhr.responseText;
            insertTarget.innerHTML = restxt;
        }
    };
    xhr.send();
}

function appendScript(url, isModule = false) {
	var el = document.createElement('script');
    el.src = url;
    el.async = false;
    if (isModule) el.type = 'module';
	document.body.appendChild(el);
}

function appendFontAwsome() {
    var el = document.createElement('script');
    el.src = 'https://kit.fontawesome.com/3c64740337.js';
    el.crossOrigin = 'anonymous'
	document.body.appendChild(el); 
}

function appendCss(url) {
	var el = document.createElement('link');
	el.href = url;
	el.rel = 'stylesheet';
	el.type = 'text/css';
	document.getElementsByTagName('head')[0].appendChild(el);
}

function getIsDevelop() {
    const domain = document.domain
    return domain == 'localhost';
}

window.addEventListener('DOMContentLoaded', (e) => {
    appendCss('/css/bootstrap.min.css');
    appendCss('/css/common.css');
    appendScript('/js/axios.min.js');
    appendScript('/js/js.cookie.min.js', true);
    appendScript('/js/getApiUrl.js', true);
    appendScript('/js/getFileApiUrl.js', true);
    appendScript('/js/getEnv.js', true);
    appendScript('/js/colorTheme.js', true);
    appendScript('/js/urlParameter.js', true);
    if (getIsDevelop()) {
        appendScript('/js/vue.js', true);
    }
    else {
        appendScript('/js/vue.min.js', true);
    }
    appendFontAwsome();

    const header = document.getElementById('header')
    loadCommonParts('/commonParts/header.html', header)
    const footer = document.getElementById('footer')
    loadCommonParts('/commonParts/footer.html', footer)
})