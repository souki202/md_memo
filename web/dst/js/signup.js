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

/***/ "./web/src/js/colorTheme.js":
/*!**********************************!*\
  !*** ./web/src/js/colorTheme.js ***!
  \**********************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (__WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/* harmony import */ var _js_cookie_min__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./js.cookie.min */ \"./web/src/js/js.cookie.min.js\");\n/* harmony import */ var _js_cookie_min__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_js_cookie_min__WEBPACK_IMPORTED_MODULE_0__);\n\n\nfunction getTheme() {\n  const theme = _js_cookie_min__WEBPACK_IMPORTED_MODULE_0___default().get('theme');\n\n  if (!theme || theme == 'light') {\n    return 'light';\n  } else {\n    return 'dark';\n  }\n}\n\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (getTheme);\n\n//# sourceURL=webpack://web/./web/src/js/colorTheme.js?");

/***/ }),

/***/ "./web/src/js/getApiUrl.js":
/*!*********************************!*\
  !*** ./web/src/js/getApiUrl.js ***!
  \*********************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* export default binding */ __WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/* harmony default export */ function __WEBPACK_DEFAULT_EXPORT__() {\n  return 'https://' + 'api.' + document.domain;\n}\n\n//# sourceURL=webpack://web/./web/src/js/getApiUrl.js?");

/***/ }),

/***/ "./web/src/js/js.cookie.min.js":
/*!*************************************!*\
  !*** ./web/src/js/js.cookie.min.js ***!
  \*************************************/
/***/ ((module, exports, __webpack_require__) => {

eval("var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_RESULT__;/**\r\n * Minified by jsDelivr using Terser v3.14.1.\r\n * Original file: /npm/js-cookie@2.2.1/src/js.cookie.js\r\n * \r\n * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files\r\n */\n!function (e) {\n  var n;\n\n  if ( true && (!(__WEBPACK_AMD_DEFINE_FACTORY__ = (e),\n\t\t__WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ?\n\t\t(__WEBPACK_AMD_DEFINE_FACTORY__.call(exports, __webpack_require__, exports, module)) :\n\t\t__WEBPACK_AMD_DEFINE_FACTORY__),\n\t\t__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__)), n = !0),  true && (module.exports = e(), n = !0), !n) {\n    var t = window.Cookies,\n        o = window.Cookies = e();\n\n    o.noConflict = function () {\n      return window.Cookies = t, o;\n    };\n  }\n}(function () {\n  function e() {\n    for (var e = 0, n = {}; e < arguments.length; e++) {\n      var t = arguments[e];\n\n      for (var o in t) n[o] = t[o];\n    }\n\n    return n;\n  }\n\n  function n(e) {\n    return e.replace(/(%[0-9A-Z]{2})+/g, decodeURIComponent);\n  }\n\n  return function t(o) {\n    function r() {}\n\n    function i(n, t, i) {\n      if (\"undefined\" != typeof document) {\n        \"number\" == typeof (i = e({\n          path: \"/\"\n        }, r.defaults, i)).expires && (i.expires = new Date(1 * new Date() + 864e5 * i.expires)), i.expires = i.expires ? i.expires.toUTCString() : \"\";\n\n        try {\n          var c = JSON.stringify(t);\n          /^[\\{\\[]/.test(c) && (t = c);\n        } catch (e) {}\n\n        t = o.write ? o.write(t, n) : encodeURIComponent(String(t)).replace(/%(23|24|26|2B|3A|3C|3E|3D|2F|3F|40|5B|5D|5E|60|7B|7D|7C)/g, decodeURIComponent), n = encodeURIComponent(String(n)).replace(/%(23|24|26|2B|5E|60|7C)/g, decodeURIComponent).replace(/[\\(\\)]/g, escape);\n        var f = \"\";\n\n        for (var u in i) i[u] && (f += \"; \" + u, !0 !== i[u] && (f += \"=\" + i[u].split(\";\")[0]));\n\n        return document.cookie = n + \"=\" + t + f;\n      }\n    }\n\n    function c(e, t) {\n      if (\"undefined\" != typeof document) {\n        for (var r = {}, i = document.cookie ? document.cookie.split(\"; \") : [], c = 0; c < i.length; c++) {\n          var f = i[c].split(\"=\"),\n              u = f.slice(1).join(\"=\");\n          t || '\"' !== u.charAt(0) || (u = u.slice(1, -1));\n\n          try {\n            var a = n(f[0]);\n            if (u = (o.read || o)(u, a) || n(u), t) try {\n              u = JSON.parse(u);\n            } catch (e) {}\n            if (r[a] = u, e === a) break;\n          } catch (e) {}\n        }\n\n        return e ? r[e] : r;\n      }\n    }\n\n    return r.set = i, r.get = function (e) {\n      return c(e, !1);\n    }, r.getJSON = function (e) {\n      return c(e, !0);\n    }, r.remove = function (n, t) {\n      i(n, \"\", e(t, {\n        expires: -1\n      }));\n    }, r.defaults = {}, r.withConverter = t, r;\n  }(function () {});\n});\n\n//# sourceURL=webpack://web/./web/src/js/js.cookie.min.js?");

/***/ }),

/***/ "./web/src/js/signup.js":
/*!******************************!*\
  !*** ./web/src/js/signup.js ***!
  \******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _getApiUrl_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./getApiUrl.js */ \"./web/src/js/getApiUrl.js\");\n/* harmony import */ var _js_cookie_min_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./js.cookie.min.js */ \"./web/src/js/js.cookie.min.js\");\n/* harmony import */ var _js_cookie_min_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_js_cookie_min_js__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var _colorTheme_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./colorTheme.js */ \"./web/src/js/colorTheme.js\");\n\n\n // import './axios.min.js';\n\nnew Vue({\n  el: '#signupForm',\n  data: () => {\n    return {\n      errorMessage: '',\n      successMessage: '',\n      form: {\n        email: '',\n        password: '',\n        password2: ''\n      },\n      theme: 'light'\n    };\n  },\n\n  mounted() {\n    this.theme = (0,_colorTheme_js__WEBPACK_IMPORTED_MODULE_2__.default)();\n  },\n\n  methods: {\n    submit() {\n      this.errorMessage = \"\";\n      const email = this.form.email;\n      const password = this.form.password;\n      const password2 = this.form.password2;\n\n      if (!email || !password || !password2) {\n        // this.errorMessage = 'There are not enough input items.'\n        this.errorMessage = '入力が不足しています';\n        return false;\n      }\n\n      if (password.length < 8) {\n        this.errorMessage = 'パスワードは8文字以上入力してください';\n        return false;\n      }\n\n      if (password != password2) {\n        // this.errorMessage = 'Password input does not match.';\n        this.errorMessage = '確認用のパスワードが一致しません';\n        return false;\n      }\n\n      axios.post((0,_getApiUrl_js__WEBPACK_IMPORTED_MODULE_0__.default)() + '/signup', {\n        params: {\n          email: email,\n          password: password\n        }\n      }, {\n        withCredentials: true\n      }).then(res => {\n        this.successMessage = '本登録用のメールを送信しました';\n      }).catch(err => {\n        console.log(err.response.status);\n\n        if (err.response.status == 403) {\n          this.errorMessage = \"そのユーザはすでに登録されているか、退会済みのユーザです。\";\n        } else {\n          this.errorMessage = \"サーバーエラーが発生しました\";\n        }\n      }).then(() => {// always executed\n      });\n      return false;\n    }\n\n  }\n});\n\n//# sourceURL=webpack://web/./web/src/js/signup.js?");

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
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	(() => {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = (module) => {
/******/ 			var getter = module && module.__esModule ?
/******/ 				() => (module['default']) :
/******/ 				() => (module);
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	})();
/******/ 	
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
/******/ 	var __webpack_exports__ = __webpack_require__("./web/src/js/signup.js");
/******/ 	
/******/ })()
;