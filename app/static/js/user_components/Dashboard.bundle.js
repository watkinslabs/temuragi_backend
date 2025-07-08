// Ensure window.Components exists
window.Components = window.Components || {};
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	// The require scope
/******/ 	var __webpack_require__ = {};
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
/************************************************************************/
var __webpack_exports__ = {};

// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  "default": () => (/* binding */ user_components_Dashboard)
});

;// external "React"
const external_React_namespaceObject = window["React"];
var external_React_default = /*#__PURE__*/__webpack_require__.n(external_React_namespaceObject);
;// ./src/config/index.js
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
// react/src/config/index.js
var config_config = {
  api: {
    base: '/v2/api',
    endpoints: {
      // Auth endpoints
      auth: {
        login: '/auth/login',
        logout: '/auth/logout',
        validate: '/auth/validate',
        refresh: '/auth/refresh',
        status: '/auth/status'
      },
      // Template endpoints
      templates: {
        get: '/templates/:slug'
      },
      // Route resolution
      routes: {
        resolve: '/routes/resolve',
        list: '/routes'
      },
      // Data endpoint
      data: '/data'
    }
  },
  // Build full URL from endpoint
  getUrl: function getUrl(endpoint) {
    var params = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
    var url = "".concat(config_config.api.base).concat(endpoint);

    // Replace URL parameters like :name
    Object.keys(params).forEach(function (key) {
      url = url.replace(":".concat(key), params[key]);
    });
    return url;
  },
  // Wrap fetch to check for CSRF invalid
  apiCall: function () {
    var _apiCall = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee(url) {
      var options,
        response,
        content_type,
        data,
        _args = arguments;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.n) {
          case 0:
            options = _args.length > 1 && _args[1] !== undefined ? _args[1] : {};
            _context.n = 1;
            return fetch(url, options);
          case 1:
            response = _context.v;
            if (response.ok) {
              _context.n = 4;
              break;
            }
            content_type = response.headers.get('content-type');
            if (!(content_type && content_type.includes('application/json'))) {
              _context.n = 4;
              break;
            }
            _context.n = 2;
            return response.json();
          case 2:
            data = _context.v;
            if (!(data.success === false && data.csrf_invalid === true)) {
              _context.n = 3;
              break;
            }
            console.log('CSRF invalid - clearing auth and reloading');

            // Clear everything
            localStorage.removeItem('api_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_id');
            localStorage.removeItem('user_info');
            localStorage.removeItem('default_context');
            sessionStorage.clear();

            // Just reload the page - the app will show login since auth is cleared
            window.location.reload();

            // Return the response anyway
            return _context.a(2, response);
          case 3:
            return _context.a(2, new Response(JSON.stringify(data), {
              status: response.status,
              statusText: response.statusText,
              headers: response.headers
            }));
          case 4:
            return _context.a(2, response);
        }
      }, _callee);
    }));
    function apiCall(_x) {
      return _apiCall.apply(this, arguments);
    }
    return apiCall;
  }(),
  // Get auth headers
  getAuthHeaders: function getAuthHeaders() {
    var _document$querySelect;
    return {
      'Authorization': "Bearer ".concat(localStorage.getItem('api_token') || ''),
      'X-CSRF-Token': ((_document$querySelect = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect === void 0 ? void 0 : _document$querySelect.content) || '',
      'Content-Type': 'application/json'
    };
  }
};

// Make it available globally if needed
window.appConfig = config_config;
/* harmony default export */ const src_config = (config_config);
;// ./src/contexts/AuthContext.js
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function AuthContext_regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return AuthContext_regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (AuthContext_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, AuthContext_regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, AuthContext_regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), AuthContext_regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", AuthContext_regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), AuthContext_regeneratorDefine2(u), AuthContext_regeneratorDefine2(u, o, "Generator"), AuthContext_regeneratorDefine2(u, n, function () { return this; }), AuthContext_regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (AuthContext_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function AuthContext_regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } AuthContext_regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { AuthContext_regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, AuthContext_regeneratorDefine2(e, r, n, t); }
function AuthContext_asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function AuthContext_asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { AuthContext_asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { AuthContext_asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }
// react/src/contexts/AuthContext.js


var AuthContext = /*#__PURE__*/(0,external_React_namespaceObject.createContext)(null);
var useAuth = function useAuth() {
  var context = (0,external_React_namespaceObject.useContext)(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
var AuthProvider = function AuthProvider(_ref) {
  var children = _ref.children;
  var _useState = useState(false),
    _useState2 = _slicedToArray(_useState, 2),
    isAuthenticated = _useState2[0],
    setIsAuthenticated = _useState2[1];
  var _useState3 = useState(true),
    _useState4 = _slicedToArray(_useState3, 2),
    loading = _useState4[0],
    setLoading = _useState4[1];
  var _useState5 = useState(null),
    _useState6 = _slicedToArray(_useState5, 2),
    user = _useState6[0],
    setUser = _useState6[1];

  // We'll need to access SiteContext's clear_section
  var _useState7 = useState(null),
    _useState8 = _slicedToArray(_useState7, 2),
    clear_site_callback = _useState8[0],
    setClearSiteCallback = _useState8[1];

  // Refresh handling state
  var refresh_lock = useRef(false);
  var refresh_promise = useRef(null);
  var token_expiry = useRef(null);
  var refresh_retry_count = useRef(0);
  var max_refresh_retries = 3;

  // Add helper functions for cookie management at the top of AuthProvider
  var set_cookie = function set_cookie(name, value) {
    var days = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 365 * 10;
    var expires = new Date();
    expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = "".concat(name, "=").concat(value, ";expires=").concat(expires.toUTCString(), ";path=/;SameSite=Lax");
  };
  var delete_cookie = function delete_cookie(name) {
    document.cookie = "".concat(name, "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;SameSite=Lax");
  };

  // Allow SiteProvider to register its clear function
  var register_clear_site = function register_clear_site(callback) {
    setClearSiteCallback(function () {
      return callback;
    });
  };

  // Parse JWT to get expiry time
  var get_token_expiry = function get_token_expiry(token) {
    if (!token) return null;
    try {
      var parts = token.split('.');
      if (parts.length !== 3) return null;
      var payload = JSON.parse(atob(parts[1]));
      // JWT exp is in seconds, convert to milliseconds
      return payload.exp ? payload.exp * 1000 : null;
    } catch (error) {
      console.error('Failed to parse token:', error);
      return null;
    }
  };

  // Check if token is expired or about to expire
  var is_token_expired = function is_token_expired(expiry_time) {
    var buffer_minutes = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 2;
    if (!expiry_time) return true;

    // Add buffer to refresh before actual expiry
    var buffer_ms = buffer_minutes * 60 * 1000;
    return Date.now() >= expiry_time - buffer_ms;
  };

  // Check if we have valid tokens on mount
  useEffect(function () {
    checkAuth();
  }, []);
  var checkAuth = /*#__PURE__*/function () {
    var _ref2 = AuthContext_asyncToGenerator(/*#__PURE__*/AuthContext_regenerator().m(function _callee() {
      var api_token, refresh_token, expiry, refresh_success, new_api_token, new_expiry, _document$querySelect, current_token, response, data, _t;
      return AuthContext_regenerator().w(function (_context) {
        while (1) switch (_context.n) {
          case 0:
            api_token = localStorage.getItem('api_token');
            refresh_token = localStorage.getItem('refresh_token');
            if (!(!api_token || !refresh_token)) {
              _context.n = 1;
              break;
            }
            setLoading(false);
            return _context.a(2);
          case 1:
            // Set token expiry
            expiry = get_token_expiry(api_token);
            token_expiry.current = expiry;

            // Check if token is already expired BEFORE making any API calls
            if (!is_token_expired(expiry)) {
              _context.n = 4;
              break;
            }
            console.log('Token expired on mount, refreshing...');
            _context.n = 2;
            return _refreshToken();
          case 2:
            refresh_success = _context.v;
            if (refresh_success) {
              _context.n = 3;
              break;
            }
            clearAuth();
            setLoading(false);
            return _context.a(2);
          case 3:
            // Get the new token after refresh
            new_api_token = localStorage.getItem('api_token');
            new_expiry = get_token_expiry(new_api_token);
            token_expiry.current = new_expiry;
          case 4:
            _context.p = 4;
            // NOW validate the current token (which should be fresh if it was expired)
            current_token = localStorage.getItem('api_token');
            _context.n = 5;
            return config.apiCall(config.getUrl(config.api.endpoints.auth.validate), {
              method: 'POST',
              headers: {
                'Authorization': "Bearer ".concat(current_token),
                'Content-Type': 'application/json',
                'X-CSRF-Token': ((_document$querySelect = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect === void 0 ? void 0 : _document$querySelect.content) || ''
              }
            });
          case 5:
            response = _context.v;
            if (!response.ok) {
              _context.n = 7;
              break;
            }
            _context.n = 6;
            return response.json();
          case 6:
            data = _context.v;
            setIsAuthenticated(true);
            setUser(data.user_info);

            // Set up periodic token validation
            start_token_check_interval();
            _context.n = 8;
            break;
          case 7:
            // Validation failed - clear auth
            clearAuth();
          case 8:
            _context.n = 10;
            break;
          case 9:
            _context.p = 9;
            _t = _context.v;
            console.error('Auth check failed:', _t);
            clearAuth();
          case 10:
            _context.p = 10;
            setLoading(false);
            return _context.f(10);
          case 11:
            return _context.a(2);
        }
      }, _callee, null, [[4, 9, 10, 11]]);
    }));
    return function checkAuth() {
      return _ref2.apply(this, arguments);
    };
  }();
  var login = /*#__PURE__*/function () {
    var _ref3 = AuthContext_asyncToGenerator(/*#__PURE__*/AuthContext_regenerator().m(function _callee2(username, password, remember) {
      var _document$querySelect2, response, data, expiry, error_data, _t2;
      return AuthContext_regenerator().w(function (_context2) {
        while (1) switch (_context2.n) {
          case 0:
            _context2.p = 0;
            _context2.n = 1;
            return config.apiCall(config.getUrl(config.api.endpoints.auth.login), {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': ((_document$querySelect2 = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect2 === void 0 ? void 0 : _document$querySelect2.content) || ''
              },
              body: JSON.stringify({
                username: username,
                password: password,
                remember: remember
              })
            });
          case 1:
            response = _context2.v;
            if (!response.ok) {
              _context2.n = 3;
              break;
            }
            _context2.n = 2;
            return response.json();
          case 2:
            data = _context2.v;
            // Store tokens
            localStorage.setItem('api_token', data.api_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_info', JSON.stringify(data.user_info));
            set_cookie('user_id', data.user_id);
            if (data.user_info && data.user_info.email) {
              set_cookie('email', data.user_info.email);
            }

            // Store token expiry
            expiry = get_token_expiry(data.api_token);
            token_expiry.current = expiry;

            // Store the ACTUAL default context from login
            if (data.default_context) {
              localStorage.setItem('default_context', data.default_context);
              sessionStorage.setItem('current_context', data.default_context);
              sessionStorage.setItem('current_section', data.default_context); // Also store as section for compatibility
            }

            // Handle remember me
            if (remember) {
              localStorage.setItem('remembered_username', username);
            } else {
              localStorage.removeItem('remembered_username');
            }
            setIsAuthenticated(true);
            setUser(data.user_info);

            // Reset refresh retry count on successful login
            refresh_retry_count.current = 0;

            // Start token check interval after successful login
            start_token_check_interval();
            return _context2.a(2, {
              success: true,
              landing_page: data.landing_page || '/',
              default_context: data.default_context
            });
          case 3:
            _context2.n = 4;
            return response.json();
          case 4:
            error_data = _context2.v;
            return _context2.a(2, {
              success: false,
              message: error_data.message || 'Login failed'
            });
          case 5:
            _context2.n = 7;
            break;
          case 6:
            _context2.p = 6;
            _t2 = _context2.v;
            console.error('Login error:', _t2);
            return _context2.a(2, {
              success: false,
              message: 'Login failed'
            });
          case 7:
            return _context2.a(2);
        }
      }, _callee2, null, [[0, 6]]);
    }));
    return function login(_x, _x2, _x3) {
      return _ref3.apply(this, arguments);
    };
  }();
  var _refreshToken = /*#__PURE__*/function () {
    var _ref4 = AuthContext_asyncToGenerator(/*#__PURE__*/AuthContext_regenerator().m(function _callee4() {
      return AuthContext_regenerator().w(function (_context4) {
        while (1) switch (_context4.n) {
          case 0:
            if (!(refresh_lock.current && refresh_promise.current)) {
              _context4.n = 1;
              break;
            }
            console.log('Refresh already in progress, waiting...');
            return _context4.a(2, refresh_promise.current);
          case 1:
            // Set the lock
            refresh_lock.current = true;

            // Create the refresh promise
            refresh_promise.current = AuthContext_asyncToGenerator(/*#__PURE__*/AuthContext_regenerator().m(function _callee3() {
              var refresh_token, _document$querySelect3, response, data, expiry, _t3;
              return AuthContext_regenerator().w(function (_context3) {
                while (1) switch (_context3.n) {
                  case 0:
                    refresh_token = localStorage.getItem('refresh_token');
                    if (refresh_token) {
                      _context3.n = 1;
                      break;
                    }
                    refresh_lock.current = false;
                    refresh_promise.current = null;
                    return _context3.a(2, false);
                  case 1:
                    _context3.p = 1;
                    console.log('Attempting token refresh...');
                    _context3.n = 2;
                    return config.apiCall(config.getUrl(config.api.endpoints.auth.refresh), {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': ((_document$querySelect3 = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect3 === void 0 ? void 0 : _document$querySelect3.content) || ''
                      },
                      body: JSON.stringify({
                        refresh_token: refresh_token
                      })
                    });
                  case 2:
                    response = _context3.v;
                    if (!response.ok) {
                      _context3.n = 4;
                      break;
                    }
                    _context3.n = 3;
                    return response.json();
                  case 3:
                    data = _context3.v;
                    localStorage.setItem('api_token', data.api_token);

                    // Update token expiry
                    expiry = get_token_expiry(data.api_token);
                    token_expiry.current = expiry;

                    // Update user info if provided
                    if (data.user_info) {
                      localStorage.setItem('user_info', JSON.stringify(data.user_info));
                      setUser(data.user_info);
                    }
                    setIsAuthenticated(true);

                    // Reset retry count on successful refresh
                    refresh_retry_count.current = 0;
                    console.log('Token refresh successful');
                    return _context3.a(2, true);
                  case 4:
                    if (!(response.status === 401 || response.status === 403)) {
                      _context3.n = 5;
                      break;
                    }
                    // Refresh token is invalid, this is permanent
                    console.log('Refresh token is invalid');
                    refresh_retry_count.current = max_refresh_retries; // Don't retry
                    return _context3.a(2, false);
                  case 5:
                    if (!(response.status >= 500)) {
                      _context3.n = 7;
                      break;
                    }
                    // Server error, might be temporary
                    refresh_retry_count.current++;
                    console.log("Refresh failed with server error, retry count: ".concat(refresh_retry_count.current));
                    if (!(refresh_retry_count.current < max_refresh_retries)) {
                      _context3.n = 7;
                      break;
                    }
                    _context3.n = 6;
                    return new Promise(function (resolve) {
                      return setTimeout(resolve, 1000 * refresh_retry_count.current);
                    });
                  case 6:
                    refresh_lock.current = false;
                    refresh_promise.current = null;
                    return _context3.a(2, _refreshToken());
                  case 7:
                    return _context3.a(2, false);
                  case 8:
                    _context3.n = 12;
                    break;
                  case 9:
                    _context3.p = 9;
                    _t3 = _context3.v;
                    console.error('Token refresh failed:', _t3);
                    refresh_retry_count.current++;
                    if (!(refresh_retry_count.current < max_refresh_retries)) {
                      _context3.n = 11;
                      break;
                    }
                    _context3.n = 10;
                    return new Promise(function (resolve) {
                      return setTimeout(resolve, 1000 * refresh_retry_count.current);
                    });
                  case 10:
                    refresh_lock.current = false;
                    refresh_promise.current = null;
                    return _context3.a(2, _refreshToken());
                  case 11:
                    return _context3.a(2, false);
                  case 12:
                    _context3.p = 12;
                    refresh_lock.current = false;
                    refresh_promise.current = null;
                    return _context3.f(12);
                  case 13:
                    return _context3.a(2);
                }
              }, _callee3, null, [[1, 9, 12, 13]]);
            }))();
            return _context4.a(2, refresh_promise.current);
        }
      }, _callee4);
    }));
    return function refreshToken() {
      return _ref4.apply(this, arguments);
    };
  }();
  var logout = function logout() {
    clearAuth();
    // Clear site context if callback is registered
    if (clear_site_callback) {
      clear_site_callback();
    }
  };
  var clearAuth = function clearAuth() {
    // Clear all auth data
    localStorage.removeItem('api_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_info');
    localStorage.removeItem('default_context'); // Changed from default_section

    // Clear cookies
    delete_cookie('user_id');
    delete_cookie('email');

    // Clear state
    setIsAuthenticated(false);
    setUser(null);

    // Reset refresh state
    refresh_lock.current = false;
    refresh_promise.current = null;
    token_expiry.current = null;
    refresh_retry_count.current = 0;

    // Stop token check interval
    stop_token_check_interval();
  };

  // Periodic token validation
  var token_check_interval = null;
  var start_token_check_interval = function start_token_check_interval() {
    // Clear any existing interval
    stop_token_check_interval();

    // Check token every minute (more frequently to catch expiry)
    token_check_interval = setInterval(/*#__PURE__*/AuthContext_asyncToGenerator(/*#__PURE__*/AuthContext_regenerator().m(function _callee5() {
      var api_token, refresh_success, _document$querySelect4, response, _refresh_success, _t4;
      return AuthContext_regenerator().w(function (_context5) {
        while (1) switch (_context5.n) {
          case 0:
            api_token = localStorage.getItem('api_token');
            if (api_token) {
              _context5.n = 1;
              break;
            }
            clearAuth();
            return _context5.a(2);
          case 1:
            if (!is_token_expired(token_expiry.current, 5)) {
              _context5.n = 3;
              break;
            }
            // 5 minute buffer
            console.log('Token about to expire, refreshing proactively...');
            _context5.n = 2;
            return _refreshToken();
          case 2:
            refresh_success = _context5.v;
            if (!refresh_success) {
              // Only clear auth if we've exhausted retries
              if (refresh_retry_count.current >= max_refresh_retries) {
                clearAuth();
              }
            }
            return _context5.a(2);
          case 3:
            _context5.p = 3;
            _context5.n = 4;
            return config.apiCall(config.getUrl(config.api.endpoints.auth.validate), {
              method: 'POST',
              headers: {
                'Authorization': "Bearer ".concat(api_token),
                'Content-Type': 'application/json',
                'X-CSRF-Token': ((_document$querySelect4 = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect4 === void 0 ? void 0 : _document$querySelect4.content) || ''
              }
            });
          case 4:
            response = _context5.v;
            if (!(!response.ok && response.status === 401)) {
              _context5.n = 6;
              break;
            }
            _context5.n = 5;
            return _refreshToken();
          case 5:
            _refresh_success = _context5.v;
            if (!_refresh_success && refresh_retry_count.current >= max_refresh_retries) {
              clearAuth();
            }
          case 6:
            _context5.n = 8;
            break;
          case 7:
            _context5.p = 7;
            _t4 = _context5.v;
            console.error('Token validation error:', _t4);
            // Don't clear auth on network errors
          case 8:
            return _context5.a(2);
        }
      }, _callee5, null, [[3, 7]]);
    })), 60 * 1000); // Check every minute
  };
  var stop_token_check_interval = function stop_token_check_interval() {
    if (token_check_interval) {
      clearInterval(token_check_interval);
      token_check_interval = null;
    }
  };

  // Clean up interval on unmount
  useEffect(function () {
    return function () {
      stop_token_check_interval();
    };
  }, []);

  // Set up global auth headers helper - MOVED TO SEPARATE useEffect
  useEffect(function () {
    if (!window.app) window.app = {};
    window.app.getAuthHeaders = function () {
      var _document$querySelect5;
      var token = localStorage.getItem('api_token');
      return {
        'Authorization': token ? "Bearer ".concat(token) : '',
        'X-CSRF-Token': ((_document$querySelect5 = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect5 === void 0 ? void 0 : _document$querySelect5.content) || ''
      };
    };
  }, []);

  // Global fetch interceptor in separate useEffect with proper dependencies
  useEffect(function () {
    // Only set up interceptor after initial auth check is complete
    if (loading) return;
    var original_fetch = window.fetch;
    window.fetch = /*#__PURE__*/AuthContext_asyncToGenerator(/*#__PURE__*/AuthContext_regenerator().m(function _callee6() {
      var _len,
        args,
        _key,
        response,
        url,
        refresh_success,
        new_token,
        _args6 = arguments;
      return AuthContext_regenerator().w(function (_context6) {
        while (1) switch (_context6.n) {
          case 0:
            for (_len = _args6.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
              args[_key] = _args6[_key];
            }
            _context6.n = 1;
            return original_fetch.apply(void 0, args);
          case 1:
            response = _context6.v;
            if (!(response.status === 401 && !window.location.pathname.includes('/login'))) {
              _context6.n = 5;
              break;
            }
            url = typeof args[0] === 'string' ? args[0] : args[0].url; // Don't intercept auth endpoints
            if (url.includes('/auth/')) {
              _context6.n = 5;
              break;
            }
            _context6.n = 2;
            return _refreshToken();
          case 2:
            refresh_success = _context6.v;
            if (!refresh_success) {
              _context6.n = 4;
              break;
            }
            // Retry the original request with new token
            new_token = localStorage.getItem('api_token');
            if (args[1] && args[1].headers) {
              args[1].headers['Authorization'] = "Bearer ".concat(new_token);
            } else if (args[1]) {
              args[1].headers = _objectSpread(_objectSpread({}, args[1].headers), {}, {
                'Authorization': "Bearer ".concat(new_token)
              });
            } else {
              args[1] = {
                headers: {
                  'Authorization': "Bearer ".concat(new_token)
                }
              };
            }
            _context6.n = 3;
            return original_fetch.apply(void 0, args);
          case 3:
            response = _context6.v;
            _context6.n = 5;
            break;
          case 4:
            if (refresh_retry_count.current >= max_refresh_retries) {
              // Only clear auth if we've exhausted retries
              clearAuth();
            }
          case 5:
            return _context6.a(2, response);
        }
      }, _callee6);
    }));

    // Restore original fetch on cleanup
    return function () {
      window.fetch = original_fetch;
    };
  }, [loading]); // Only run after loading is complete

  return /*#__PURE__*/React.createElement(AuthContext.Provider, {
    value: {
      isAuthenticated: isAuthenticated,
      loading: loading,
      user: user,
      login: login,
      logout: logout,
      refreshToken: _refreshToken,
      checkAuth: checkAuth,
      register_clear_site: register_clear_site
    }
  }, children);
};
;// ./src/user_components/Dashboard.js
function Dashboard_regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return Dashboard_regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (Dashboard_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, Dashboard_regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, Dashboard_regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), Dashboard_regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", Dashboard_regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), Dashboard_regeneratorDefine2(u), Dashboard_regeneratorDefine2(u, o, "Generator"), Dashboard_regeneratorDefine2(u, n, function () { return this; }), Dashboard_regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (Dashboard_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function Dashboard_regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } Dashboard_regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { Dashboard_regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, Dashboard_regeneratorDefine2(e, r, n, t); }
function Dashboard_asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function Dashboard_asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { Dashboard_asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { Dashboard_asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function Dashboard_slicedToArray(r, e) { return Dashboard_arrayWithHoles(r) || Dashboard_iterableToArrayLimit(r, e) || Dashboard_unsupportedIterableToArray(r, e) || Dashboard_nonIterableRest(); }
function Dashboard_nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function Dashboard_unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return Dashboard_arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? Dashboard_arrayLikeToArray(r, a) : void 0; } }
function Dashboard_arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function Dashboard_iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function Dashboard_arrayWithHoles(r) { if (Array.isArray(r)) return r; }



var Dashboard = function Dashboard() {
  var _useAuth = useAuth(),
    user = _useAuth.user;
  var _useState = (0,external_React_namespaceObject.useState)(null),
    _useState2 = Dashboard_slicedToArray(_useState, 2),
    stats = _useState2[0],
    setStats = _useState2[1];
  var _useState3 = (0,external_React_namespaceObject.useState)(true),
    _useState4 = Dashboard_slicedToArray(_useState3, 2),
    loading = _useState4[0],
    setLoading = _useState4[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    fetch_dashboard_data();
  }, []);
  var fetch_dashboard_data = /*#__PURE__*/function () {
    var _ref = Dashboard_asyncToGenerator(/*#__PURE__*/Dashboard_regenerator().m(function _callee() {
      var response, data, _t;
      return Dashboard_regenerator().w(function (_context) {
        while (1) switch (_context.n) {
          case 0:
            _context.p = 0;
            _context.n = 1;
            return fetch(src_config.getUrl('/dashboard/stats'), {
              headers: src_config.getAuthHeaders()
            });
          case 1:
            response = _context.v;
            if (!response.ok) {
              _context.n = 3;
              break;
            }
            _context.n = 2;
            return response.json();
          case 2:
            data = _context.v;
            setStats(data);
          case 3:
            _context.n = 5;
            break;
          case 4:
            _context.p = 4;
            _t = _context.v;
            console.error('Failed to fetch dashboard data:', _t);
          case 5:
            _context.p = 5;
            setLoading(false);
            return _context.f(5);
          case 6:
            return _context.a(2);
        }
      }, _callee, null, [[0, 4, 5, 6]]);
    }));
    return function fetch_dashboard_data() {
      return _ref.apply(this, arguments);
    };
  }();
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "dashboard"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "container-fluid"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row mb-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col"
  }, /*#__PURE__*/external_React_default().createElement("h2", null, "Welcome back", user !== null && user !== void 0 && user.name ? ", ".concat(user.name) : '', "!"), /*#__PURE__*/external_React_default().createElement("p", {
    className: "text-muted"
  }, "Here's what's happening with your account today."))), loading ? /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-center p-5"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "spinner-border text-primary",
    role: "status"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "visually-hidden"
  }, "Loading..."))) : /*#__PURE__*/external_React_default().createElement("div", {
    className: "row"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-3 col-md-6 mb-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card border-0 shadow-sm"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "text-muted mb-2"
  }, "Total Items"), /*#__PURE__*/external_React_default().createElement("h3", {
    className: "mb-0"
  }, (stats === null || stats === void 0 ? void 0 : stats.total_items) || 0)), /*#__PURE__*/external_React_default().createElement("div", {
    className: "text-primary"
  }, /*#__PURE__*/external_React_default().createElement("i", {
    className: "fas fa-box fa-2x opacity-50"
  })))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-3 col-md-6 mb-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card border-0 shadow-sm"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "text-muted mb-2"
  }, "Active Tasks"), /*#__PURE__*/external_React_default().createElement("h3", {
    className: "mb-0"
  }, (stats === null || stats === void 0 ? void 0 : stats.active_tasks) || 0)), /*#__PURE__*/external_React_default().createElement("div", {
    className: "text-success"
  }, /*#__PURE__*/external_React_default().createElement("i", {
    className: "fas fa-tasks fa-2x opacity-50"
  })))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-3 col-md-6 mb-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card border-0 shadow-sm"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "text-muted mb-2"
  }, "Messages"), /*#__PURE__*/external_React_default().createElement("h3", {
    className: "mb-0"
  }, (stats === null || stats === void 0 ? void 0 : stats.messages) || 0)), /*#__PURE__*/external_React_default().createElement("div", {
    className: "text-info"
  }, /*#__PURE__*/external_React_default().createElement("i", {
    className: "fas fa-envelope fa-2x opacity-50"
  })))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-3 col-md-6 mb-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card border-0 shadow-sm"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "text-muted mb-2"
  }, "Notifications"), /*#__PURE__*/external_React_default().createElement("h3", {
    className: "mb-0"
  }, (stats === null || stats === void 0 ? void 0 : stats.notifications) || 0)), /*#__PURE__*/external_React_default().createElement("div", {
    className: "text-warning"
  }, /*#__PURE__*/external_React_default().createElement("i", {
    className: "fas fa-bell fa-2x opacity-50"
  }))))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row mt-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card border-0 shadow-sm"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header bg-transparent"
  }, /*#__PURE__*/external_React_default().createElement("h5", {
    className: "mb-0"
  }, "Quick Actions")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex flex-wrap gap-2"
  }, /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-primary"
  }, /*#__PURE__*/external_React_default().createElement("i", {
    className: "fas fa-plus me-2"
  }), "Create New"), /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-outline-secondary"
  }, /*#__PURE__*/external_React_default().createElement("i", {
    className: "fas fa-file-export me-2"
  }), "Export Data"), /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-outline-secondary"
  }, /*#__PURE__*/external_React_default().createElement("i", {
    className: "fas fa-cog me-2"
  }), "Settings")))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row mt-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card border-0 shadow-sm"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header bg-transparent"
  }, /*#__PURE__*/external_React_default().createElement("h5", {
    className: "mb-0"
  }, "Recent Activity")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("p", {
    className: "text-muted"
  }, "No recent activity to display.")))))));
};

// Make sure window.Components exists
if (!window.Components) {
  window.Components = {};
}

// Register the component
window.Components.Dashboard = Dashboard;

// Also export normally
/* harmony default export */ const user_components_Dashboard = (Dashboard);
window["components/Dashboard"] = __webpack_exports__["default"];
/******/ })()
;
//# sourceMappingURL=Dashboard.bundle.js.map