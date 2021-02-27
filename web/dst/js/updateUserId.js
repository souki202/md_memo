/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./web/src/js/getApiUrl.js":
/*!*********************************!*\
  !*** ./web/src/js/getApiUrl.js ***!
  \*********************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* export default binding */ __WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/* harmony default export */ function __WEBPACK_DEFAULT_EXPORT__() {\n  return 'https://' + 'api.' + document.domain;\n}\n\n//# sourceURL=webpack://web/./web/src/js/getApiUrl.js?");

/***/ }),

/***/ "./web/src/js/updateUserId.js":
/*!************************************!*\
  !*** ./web/src/js/updateUserId.js ***!
  \************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _getApiUrl_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./getApiUrl.js */ \"./web/src/js/getApiUrl.js\");\n/* harmony import */ var _urlParameter_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./urlParameter.js */ \"./web/src/js/urlParameter.js\");\n\n\nnew Vue({\n  el: '#app',\n  data: () => {\n    return {\n      errorMessage: ''\n    };\n  },\n\n  mounted() {\n    const token = (0,_urlParameter_js__WEBPACK_IMPORTED_MODULE_1__.default)('token');\n    axios.post((0,_getApiUrl_js__WEBPACK_IMPORTED_MODULE_0__.default)() + '/update_user_id', {\n      params: {\n        token: token\n      }\n    }, {\n      withCredentials: true\n    }).then(res => {\n      console.log(res);\n      location.href = '/user.html';\n    }).catch(err => {\n      console.log(err);\n      this.errorMessage = 'ユーザIDの更新に失敗しました。お手数をおかけしますが、再度お試しください。';\n    }).then(() => {});\n  },\n\n  methods: {}\n});\n\n//# sourceURL=webpack://web/./web/src/js/updateUserId.js?");

/***/ }),

/***/ "./web/src/js/urlParameter.js":
/*!************************************!*\
  !*** ./web/src/js/urlParameter.js ***!
  \************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* export default binding */ __WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/**\r\n * Get the URL parameter value\r\n *\r\n * @param  name {string} パラメータのキー文字列\r\n * @return  url {url} 対象のURL文字列（任意）\r\n */\n/* harmony default export */ function __WEBPACK_DEFAULT_EXPORT__(name, url) {\n  if (!url) url = window.location.href;\n  name = name.replace(/[\\[\\]]/g, \"\\\\$&\");\n  var regex = new RegExp(\"[?&]\" + name + \"(=([^&#]*)|&|#|$)\"),\n      results = regex.exec(url);\n  if (!results) return null;\n  if (!results[2]) return '';\n  return decodeURIComponent(results[2].replace(/\\+/g, \" \"));\n}\n\n//# sourceURL=webpack://web/./web/src/js/urlParameter.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		if(__webpack_module_cache__[moduleId]) {
/******/ 			return __webpack_module_cache__[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = __webpack_require__("./web/src/js/updateUserId.js");
/******/ 	
/******/ })()
;