/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./web/src/js/loadCommonParts.js":
/*!***************************************!*\
  !*** ./web/src/js/loadCommonParts.js ***!
  \***************************************/
/***/ (() => {

eval("function loadCommonParts(url, insertTarget) {\n  if (!insertTarget) return;\n  let xhr = new XMLHttpRequest();\n  xhr.open(\"GET\", url, true);\n\n  xhr.onreadystatechange = function () {\n    if (xhr.readyState === 4 && xhr.status === 200) {\n      var restxt = xhr.responseText;\n      insertTarget.innerHTML = restxt;\n    }\n  };\n\n  xhr.send();\n}\n\nfunction addBeforeParts(url, className, idName, insertTarget) {\n  if (!insertTarget) return;\n  let xhr = new XMLHttpRequest();\n  xhr.open(\"GET\", url, true);\n\n  xhr.onreadystatechange = function () {\n    if (xhr.readyState === 4 && xhr.status === 200) {\n      const restxt = xhr.responseText;\n      let newElement = document.createElement('div');\n      newElement.classList.add(className);\n\n      if (idName) {\n        newElement.id = idName;\n      }\n\n      newElement.innerHTML = restxt;\n      insertTarget.before(newElement);\n    }\n  };\n\n  xhr.send();\n}\n\nfunction loadCommonDOM() {\n  const header = document.getElementById('header');\n  loadCommonParts('/commonParts/header.html', header);\n  const footer = document.getElementById('footer');\n  loadCommonParts('/commonParts/footer.html', footer); // headerの手前にsidebarを入れる\n\n  addBeforeParts('/commonParts/sidebar.html', 'sidebar-container', null, header);\n}\n\nfunction appendScript(url, isModule = false) {\n  var el = document.createElement('script');\n  el.src = url;\n  el.async = false;\n  if (isModule) el.type = 'module';\n  document.body.appendChild(el);\n}\n\nfunction apeendScriptForHead(url, isModule = false) {\n  var el = document.createElement('script');\n  el.src = url; // el.async = false;\n\n  if (isModule) el.type = 'module';\n  document.head.appendChild(el);\n}\n\nfunction appendFontAwsome() {\n  var el = document.createElement('script');\n  el.src = 'https://kit.fontawesome.com/3c64740337.js';\n  el.crossOrigin = 'anonymous';\n  document.head.appendChild(el);\n}\n\nfunction appendCss(url) {\n  var el = document.createElement('link');\n  el.href = url;\n  el.rel = 'stylesheet';\n  el.type = 'text/css';\n  document.head.appendChild(el);\n}\n\nfunction getIsDevelop() {\n  const domain = document.domain;\n  return domain == 'localhost';\n}\n\nfunction getCookieArray() {\n  var arr = new Array();\n\n  if (document.cookie != '') {\n    var tmp = document.cookie.split('; ');\n\n    for (var i = 0; i < tmp.length; i++) {\n      var data = tmp[i].split('=');\n      arr[data[0]] = decodeURIComponent(data[1]);\n    }\n  }\n\n  return arr;\n}\n\nfunction applyTheme(theme) {\n  var el = document.createElement('link');\n  el.href = '/css/theme/' + theme + '.css';\n  el.rel = 'stylesheet';\n  el.type = 'text/css';\n  document.getElementsByTagName('head')[0].appendChild(el);\n}\n\n(() => {\n  apeendScriptForHead('/js/colorTheme.js', true); // 明転防止のため, ここでテーマを読み込む\n\n  const cookieArray = getCookieArray();\n\n  if (cookieArray['theme'] == 'dark') {\n    applyTheme('dark');\n  } else {\n    applyTheme('light');\n  }\n})();\n\nwindow.appendCss = appendCss;\nwindow.appendScript = appendScript;\nwindow.addEventListener('DOMContentLoaded', e => {\n  appendCss('/css/bootstrap.min.css');\n  appendCss('/css/simplebar.css');\n  appendCss('/css/common.css');\n  appendScript('/js/axios.min.js');\n  appendScript('/js/js.cookie.min.js', true);\n  appendScript('/js/simplebar.min.js'); // appendScript('/js/getApiUrl.js', true);\n  // appendScript('/js/getFileApiUrl.js', true);\n  // appendScript('/js/getEnv.js', true);\n  // appendScript('/js/urlParameter.js', true);\n\n  if (getIsDevelop()) {\n    appendScript('/js/vue.js', true);\n  } else {\n    appendScript('/js/vue.min.js', true);\n  }\n\n  appendFontAwsome();\n  loadCommonDOM();\n});\n\n//# sourceURL=webpack://web/./web/src/js/loadCommonParts.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./web/src/js/loadCommonParts.js"]();
/******/ 	
/******/ })()
;