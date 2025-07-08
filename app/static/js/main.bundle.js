/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ 182:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(590);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(521);
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }



var Login = function Login() {
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(''),
    _useState2 = _slicedToArray(_useState, 2),
    username = _useState2[0],
    setUsername = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(''),
    _useState4 = _slicedToArray(_useState3, 2),
    password = _useState4[0],
    setPassword = _useState4[1];
  var _useState5 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState6 = _slicedToArray(_useState5, 2),
    remember = _useState6[0],
    setRemember = _useState6[1];
  var _useState7 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState8 = _slicedToArray(_useState7, 2),
    show_password = _useState8[0],
    setShowPassword = _useState8[1];
  var _useState9 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState0 = _slicedToArray(_useState9, 2),
    loading = _useState0[0],
    setLoading = _useState0[1];
  var _useState1 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState10 = _slicedToArray(_useState1, 2),
    error = _useState10[0],
    setError = _useState10[1];
  var _useState11 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState12 = _slicedToArray(_useState11, 2),
    site_config = _useState12[0],
    setSiteConfig = _useState12[1];
  var _useState13 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true),
    _useState14 = _slicedToArray(_useState13, 2),
    config_loading = _useState14[0],
    setConfigLoading = _useState14[1];
  var _useAuth = (0,_contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__.useAuth)(),
    login = _useAuth.login;
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    // CLEAR ALL AUTH DATA when login page loads
    localStorage.removeItem('api_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_info');
    sessionStorage.clear();

    // Clear cookies by making a logout request to the server
    // This ensures server-side session is destroyed
    var clearServerSession = /*#__PURE__*/function () {
      var _ref = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
        var _document$querySelect, _t;
        return _regenerator().w(function (_context) {
          while (1) switch (_context.n) {
            case 0:
              _context.p = 0;
              _context.n = 1;
              return _config__WEBPACK_IMPORTED_MODULE_2__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_2__["default"].getUrl(_config__WEBPACK_IMPORTED_MODULE_2__["default"].api.endpoints.auth.logout), {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRF-Token': ((_document$querySelect = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect === void 0 ? void 0 : _document$querySelect.content) || ''
                },
                credentials: 'same-origin'
              });
            case 1:
              _context.n = 3;
              break;
            case 2:
              _context.p = 2;
              _t = _context.v;
            case 3:
              return _context.a(2);
          }
        }, _callee, null, [[0, 2]]);
      }));
      return function clearServerSession() {
        return _ref.apply(this, arguments);
      };
    }();
    clearServerSession().then(function () {
      // Fetch site config for branding AFTER clearing session
      fetch_site_config();
    });

    // Apply theme
    var saved_theme = localStorage.getItem('theme_preference') || 'light';
    document.documentElement.setAttribute('data-theme', saved_theme);
    document.documentElement.setAttribute('data-bs-theme', saved_theme);

    // Check remembered username
    var remembered_username = localStorage.getItem('remembered_username');
    if (remembered_username) {
      setUsername(remembered_username);
      setRemember(true);
    }

    // Check login reason
    var params = new URLSearchParams(window.location.search);
    var reason = params.get('reason');
    if (reason) {
      setError(get_reason_message(reason));
    }
  }, []);

  // In Login.js fetch_site_config function:
  var fetch_site_config = /*#__PURE__*/function () {
    var _ref2 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2() {
      var _document$querySelect2, response, data, _t2;
      return _regenerator().w(function (_context2) {
        while (1) switch (_context2.n) {
          case 0:
            _context2.p = 0;
            console.log('Login page fetching site config from:', _config__WEBPACK_IMPORTED_MODULE_2__["default"].getUrl('/site/config'));
            _context2.n = 1;
            return _config__WEBPACK_IMPORTED_MODULE_2__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_2__["default"].getUrl('/site/config'), {
              method: 'GET',
              headers: {
                'Accept': 'application/json',
                'X-CSRF-Token': ((_document$querySelect2 = document.querySelector('meta[name="csrf-token"]')) === null || _document$querySelect2 === void 0 ? void 0 : _document$querySelect2.content) || ''
              },
              credentials: 'omit'
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
            console.log('Site config response:', data);

            // The site config is nested in data.site
            setSiteConfig(data.site);
          case 3:
            _context2.n = 5;
            break;
          case 4:
            _context2.p = 4;
            _t2 = _context2.v;
            console.error('Failed to fetch site config:', _t2);
          case 5:
            _context2.p = 5;
            setConfigLoading(false);
            return _context2.f(5);
          case 6:
            return _context2.a(2);
        }
      }, _callee2, null, [[0, 4, 5, 6]]);
    }));
    return function fetch_site_config() {
      return _ref2.apply(this, arguments);
    };
  }();
  var get_reason_message = function get_reason_message(reason) {
    var messages = {
      'token_expired': 'Your session has expired. Please log in again.',
      'logout': 'You have been logged out successfully.',
      'unauthorized': 'Please log in to access that page.',
      'csrf_invalid': 'Security token expired. Please log in again.'
    };
    return messages[reason] || 'Please log in to continue.';
  };
  var handle_submit = /*#__PURE__*/function () {
    var _ref3 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee3(e) {
      var result, view;
      return _regenerator().w(function (_context3) {
        while (1) switch (_context3.n) {
          case 0:
            e.preventDefault();
            setError(null);
            if (!(!username.trim() || !password)) {
              _context3.n = 1;
              break;
            }
            setError('Please enter both username and password.');
            return _context3.a(2);
          case 1:
            setLoading(true);
            _context3.n = 2;
            return login(username.trim(), password, remember);
          case 2:
            result = _context3.v;
            if (result.success) {
              // Only use the default_context from login response
              if (result.default_context) {
                sessionStorage.setItem('current_context', result.default_context);
              }

              // If you need to navigate to a specific view based on landing_page:
              // Parse the landing_page URL to extract the view
              if (result.landing_page && result.landing_page !== '/') {
                view = result.landing_page.replace(/^\//, '') || 'home'; // Store it for the app to use after mounting
                sessionStorage.setItem('initial_view', view);
              }

              // Don't set loading to false - let the component unmount naturally
            } else {
              setError(result.message || 'Invalid username or password.');
              setLoading(false);
            }
          case 3:
            return _context3.a(2);
        }
      }, _callee3);
    }));
    return function handle_submit(_x) {
      return _ref3.apply(this, arguments);
    };
  }();
  var toggle_password = function toggle_password() {
    setShowPassword(!show_password);
  };
  var theme = localStorage.getItem('theme_preference') || 'light';
  var logo = theme === 'dark' ? (site_config === null || site_config === void 0 ? void 0 : site_config.logo_desktop_dark) || (site_config === null || site_config === void 0 ? void 0 : site_config.logo_desktop) : site_config === null || site_config === void 0 ? void 0 : site_config.logo_desktop;

  // Debug logging
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    if (site_config) {
      console.log('Site config loaded:', site_config);
      console.log('Logo URL:', logo);
    }
  }, [site_config, logo]);
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "login-container"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("style", {
    dangerouslySetInnerHTML: {
      __html: "\n                .login-container {\n                    min-height: 100vh;\n                    display: flex;\n                    align-items: center;\n                    justify-content: center;\n                    background: var(--theme-background);\n                    padding: 20px;\n                }\n                .login-wrapper {\n                    width: 100%;\n                    max-width: 440px;\n                }\n                .login-wrapper .card {\n                    width: 100%;\n                    border: none;\n                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);\n                    margin-bottom: 1.5rem;\n                }\n                .login-wrapper .card-header {\n                    background: var(--bs-white);\n                    border-bottom: 1px solid var(--bs-gray-200);\n                    padding: 2rem;\n                    text-align: center;\n                }\n                .logo-container {\n                    margin-bottom: 1rem;\n                }\n                .site-logo {\n                    max-height: 60px;\n                    margin-bottom: 1rem;\n                }\n                .logo-container h2 {\n                    font-size: 1.5rem;\n                    margin-bottom: 1rem;\n                    color: var(--bs-gray-800);\n                }\n                .security-badge {\n                    display: inline-flex;\n                    align-items: center;\n                    gap: 0.5rem;\n                    color: var(--bs-success);\n                    font-size: 0.875rem;\n                }\n                .login-wrapper .card-body {\n                    padding: 2rem;\n                    position: relative;\n                }\n                .loading-overlay {\n                    position: absolute;\n                    top: 0;\n                    left: 0;\n                    right: 0;\n                    bottom: 0;\n                    background: rgba(255, 255, 255, 0.9);\n                    display: flex;\n                    align-items: center;\n                    justify-content: center;\n                    z-index: 10;\n                    opacity: 0;\n                    visibility: hidden;\n                    transition: opacity 0.3s, visibility 0.3s;\n                }\n                .loading-overlay.active {\n                    opacity: 1;\n                    visibility: visible;\n                }\n                .form-floating {\n                    margin-bottom: 1rem;\n                }\n                .password-field-wrapper {\n                    position: relative;\n                }\n                .password-toggle {\n                    position: absolute;\n                    right: 12px;\n                    top: 50%;\n                    transform: translateY(-50%);\n                    cursor: pointer;\n                    color: var(--bs-gray-600);\n                    z-index: 5;\n                }\n                .remember-forgot {\n                    display: flex;\n                    justify-content: space-between;\n                    align-items: center;\n                    margin-bottom: 1.5rem;\n                }\n                .btn-login {\n                    width: 100%;\n                    padding: 0.75rem;\n                    font-weight: 600;\n                    position: relative;\n                }\n                .btn-login .spinner-border {\n                    display: none;\n                    margin-right: 0.5rem;\n                }\n                .btn-login.loading .spinner-border {\n                    display: inline-block;\n                }\n                .btn-login.loading .button-text {\n                    opacity: 0.7;\n                }\n                .login-footer {\n                    text-align: center;\n                    color: var(--bs-gray-600);\n                    font-size: 0.875rem;\n                }\n                .login-footer a {\n                    color: var(--bs-gray-600);\n                    margin: 0 0.5rem;\n                }\n                .login-footer a:hover {\n                    color: var(--bs-primary);\n                }\n            "
    }
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "login-wrapper"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "logo-container"
  }, !config_loading && logo && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("img", {
    src: logo,
    alt: "".concat((site_config === null || site_config === void 0 ? void 0 : site_config.name) || 'Site', " logo"),
    className: "site-logo"
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h2", null, (site_config === null || site_config === void 0 ? void 0 : site_config.name) || 'Welcome'), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "security-badge"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-lock"
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", null, "Secure Authentication")))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "loading-overlay ".concat(loading ? 'active' : '')
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "spinner-border text-primary",
    role: "status"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
    className: "visually-hidden"
  }, "Loading..."))), error && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "alert alert-danger alert-dismissible fade show",
    role: "alert"
  }, error, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    type: "button",
    className: "btn-close",
    onClick: function onClick() {
      return setError(null);
    }
  })), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("form", {
    onSubmit: handle_submit,
    noValidate: true
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "form-floating"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("input", {
    type: "text",
    className: "form-control",
    id: "username",
    name: "username",
    placeholder: "Username",
    value: username,
    onChange: function onChange(e) {
      return setUsername(e.target.value);
    },
    autoComplete: "username",
    required: true,
    disabled: loading
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    htmlFor: "username"
  }, "Username")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "form-floating password-field-wrapper"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("input", {
    type: show_password ? 'text' : 'password',
    className: "form-control",
    id: "password",
    name: "password",
    placeholder: "Password",
    value: password,
    onChange: function onChange(e) {
      return setPassword(e.target.value);
    },
    autoComplete: "current-password",
    required: true,
    disabled: loading
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    htmlFor: "password"
  }, "Password"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
    className: "password-toggle",
    onClick: toggle_password
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-eye".concat(show_password ? '-slash' : '')
  }))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "remember-forgot"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "form-check"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("input", {
    className: "form-check-input",
    type: "checkbox",
    id: "remember",
    name: "remember",
    checked: remember,
    onChange: function onChange(e) {
      return setRemember(e.target.checked);
    },
    disabled: loading
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    className: "form-check-label",
    htmlFor: "remember"
  }, "Remember me")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("a", {
    href: "/not_found",
    className: "forgot-link text-decoration-none"
  }, "Forgot password?")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    type: "submit",
    className: "btn btn-primary btn-login ".concat(loading ? 'loading' : ''),
    disabled: loading
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
    className: "spinner-border spinner-border-sm",
    role: "status",
    "aria-hidden": "true"
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
    className: "button-text"
  }, "Sign In"))))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "login-footer"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", null, "\xA9 ", new Date().getFullYear(), " ", (site_config === null || site_config === void 0 ? void 0 : site_config.name) || 'Your Company', ". All rights reserved."), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("a", {
    href: "#",
    className: "text-decoration-none"
  }, "Privacy Policy"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("a", {
    href: "#",
    className: "text-decoration-none"
  }, "Terms of Service"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("a", {
    href: "#",
    className: "text-decoration-none"
  }, "Security")))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (Login);

/***/ }),

/***/ 196:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(590);
/* harmony import */ var _App__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(649);
/* harmony import */ var _layout_NineDotMenu__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(514);
/* harmony import */ var _layout_Breadcrumbs__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(884);
/* harmony import */ var _layout_SidebarMenu__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(397);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(521);
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }







var DefaultLayout = function DefaultLayout(_ref) {
  var children = _ref.children;
  var _useAuth = (0,_contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__.useAuth)(),
    user = _useAuth.user,
    logout = _useAuth.logout;
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(function () {
      return localStorage.getItem('theme_preference') || 'light';
    }),
    _useState2 = _slicedToArray(_useState, 2),
    theme = _useState2[0],
    setTheme = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState4 = _slicedToArray(_useState3, 2),
    sidebar_collapsed = _useState4[0],
    setSidebarCollapsed = _useState4[1];

  // Apply theme
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme_preference', theme);
  }, [theme]);
  var handle_theme_toggle = function handle_theme_toggle() {
    setTheme(function (prev) {
      return prev === 'light' ? 'dark' : 'light';
    });
  };
  var toggle_sidebar = function toggle_sidebar() {
    setSidebarCollapsed(!sidebar_collapsed);
  };

  // Static site info - load once and cache
  var _useState5 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(function () {
      var cached = sessionStorage.getItem('static_site_info');
      return cached ? JSON.parse(cached) : null;
    }),
    _useState6 = _slicedToArray(_useState5, 2),
    static_site_info = _useState6[0],
    setStaticSiteInfo = _useState6[1];

  // Load site info ONCE on mount
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    if (!static_site_info) {
      _config__WEBPACK_IMPORTED_MODULE_6__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_6__["default"].getUrl('/site/config'), {
        method: 'POST',
        headers: _config__WEBPACK_IMPORTED_MODULE_6__["default"].getAuthHeaders(),
        body: JSON.stringify({
          path: '/',
          include_contexts: false
        })
      }).then(function (res) {
        return res.json();
      }).then(function (data) {
        var info = {
          name: data.site.name,
          logo_desktop: data.site.logo_desktop,
          logo_desktop_dark: data.site.logo_desktop_dark,
          footer_text: data.site.footer_text,
          tagline: data.site.tagline,
          maintenance_mode: data.site.maintenance_mode
        };
        setStaticSiteInfo(info);
        sessionStorage.setItem('static_site_info', JSON.stringify(info));
      })["catch"](function (error) {
        console.error('Failed to load site config:', error);
      });
    }
  }, []);
  if (!static_site_info) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "d-flex justify-content-center align-items-center min-vh-100"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "spinner-border",
      role: "status"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
      className: "visually-hidden"
    }, "Loading...")));
  }
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    id: "app-content"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "topbar htmx-indicator"
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("header", {
    className: "header"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "header_brand"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "logo_wrapper"
  }, theme === 'light' ? static_site_info.logo_desktop && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("img", {
    src: static_site_info.logo_desktop,
    alt: "".concat(static_site_info.name || 'Site', " logo"),
    className: "header_logo"
  }) : static_site_info.logo_desktop_dark && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("img", {
    src: static_site_info.logo_desktop_dark,
    alt: "".concat(static_site_info.name || 'Site', " logo"),
    className: "header_logo"
  })), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h1", null, static_site_info.name || 'Dashboard')), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "header_actions"
  }, static_site_info.maintenance_mode && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "maintenance_indicator me-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
    className: "badge bg-warning text-dark"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-tools me-1"
  }), "Maintenance Mode")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_layout_NineDotMenu__WEBPACK_IMPORTED_MODULE_3__["default"], {
    theme: theme,
    user: user,
    onToggleTheme: handle_theme_toggle,
    onLogout: logout
  }))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_layout_Breadcrumbs__WEBPACK_IMPORTED_MODULE_4__["default"], null), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "content_area ".concat(sidebar_collapsed ? 'collapsed' : '')
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_layout_SidebarMenu__WEBPACK_IMPORTED_MODULE_5__["default"], {
    collapsed: sidebar_collapsed,
    onToggleCollapse: toggle_sidebar
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "main_content",
    id: "main-content"
  }, children)), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("footer", {
    className: "footer"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "footer_content"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("p", null, static_site_info.footer_text || "\xA9 ".concat(new Date().getFullYear(), " ").concat(static_site_info.name || 'Your Company', ". All rights reserved.")), static_site_info.tagline && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("p", {
    className: "tagline"
  }, static_site_info.tagline))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.memo(DefaultLayout));

/***/ }),

/***/ 270:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _App__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(649);
/* harmony import */ var _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(721);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(521);
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
var _this = undefined;
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _iterableToArray(r) { if ("undefined" != typeof Symbol && null != r[Symbol.iterator] || null != r["@@iterator"]) return Array.from(r); }
function _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }




var ServerDataTable = function ServerDataTable(_ref) {
  var _table_config$model_n, _table_config$model_n2;
  var report_id = _ref.report_id,
    model_name = _ref.model_name,
    api_url = _ref.api_url,
    _ref$options = _ref.options,
    options = _ref$options === void 0 ? {} : _ref$options,
    _ref$on_config_loaded = _ref.on_config_loaded,
    on_config_loaded = _ref$on_config_loaded === void 0 ? null : _ref$on_config_loaded,
    _ref$overrides = _ref.overrides,
    overrides = _ref$overrides === void 0 ? {} : _ref$overrides;
  // State
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState2 = _slicedToArray(_useState, 2),
    loading = _useState2[0],
    set_loading = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true),
    _useState4 = _slicedToArray(_useState3, 2),
    initial_loading = _useState4[0],
    set_initial_loading = _useState4[1];
  var _useState5 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true),
    _useState6 = _slicedToArray(_useState5, 2),
    config_loading = _useState6[0],
    set_config_loading = _useState6[1];
  var _useState7 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState8 = _slicedToArray(_useState7, 2),
    table_config = _useState8[0],
    set_table_config = _useState8[1];
  var _useState9 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)([]),
    _useState0 = _slicedToArray(_useState9, 2),
    data = _useState0[0],
    set_data = _useState0[1];
  var _useState1 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(0),
    _useState10 = _slicedToArray(_useState1, 2),
    total_records = _useState10[0],
    set_total_records = _useState10[1];
  var _useState11 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(0),
    _useState12 = _slicedToArray(_useState11, 2),
    filtered_records = _useState12[0],
    set_filtered_records = _useState12[1];
  var _useState13 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(1),
    _useState14 = _slicedToArray(_useState13, 2),
    current_page = _useState14[0],
    set_current_page = _useState14[1];
  var _useState15 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(25),
    _useState16 = _slicedToArray(_useState15, 2),
    page_size = _useState16[0],
    set_page_size = _useState16[1];
  var _useState17 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(''),
    _useState18 = _slicedToArray(_useState17, 2),
    search_term = _useState18[0],
    set_search_term = _useState18[1];
  var _useState19 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)({
      column: null,
      direction: null
    }),
    _useState20 = _slicedToArray(_useState19, 2),
    sort_config = _useState20[0],
    set_sort_config = _useState20[1];
  var _useState21 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState22 = _slicedToArray(_useState21, 2),
    error = _useState22[0],
    set_error = _useState22[1];

  // Refs
  var search_input_ref = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);

  // Hooks
  var _useNavigation = (0,_App__WEBPACK_IMPORTED_MODULE_1__.useNavigation)(),
    navigate_to = _useNavigation.navigate_to;
  var _useSite = (0,_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__.useSite)(),
    current_context = _useSite.current_context;

  // Load table configuration from server
  var load_table_config = /*#__PURE__*/function () {
    var _ref2 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
      var response, response_data, config_data, server_config, merged_config, _t;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.n) {
          case 0:
            if (report_id) {
              _context.n = 1;
              break;
            }
            // If no report_id, we're in manual mode
            set_table_config(_objectSpread(_objectSpread({
              model_name: model_name,
              report_name: report_id || (model_name === null || model_name === void 0 ? void 0 : model_name.toLowerCase()),
              api_url: api_url || '/v2/api/data',
              page_length: 25,
              show_search: true,
              show_column_search: false,
              columns: {},
              excluded_columns: ['password_hash', 'created_by', 'updated_by', 'deleted_at'],
              actions: [],
              table_title: null,
              table_description: null,
              report_id: null,
              is_model: true,
              custom_options: {
                cache_enabled: false,
                refresh_interval: 0,
                row_limit: 10000
              }
            }, options), overrides));
            set_config_loading(false);
            return _context.a(2);
          case 1:
            _context.p = 1;
            set_config_loading(true);

            // Fetch report configuration
            _context.n = 2;
            return _config__WEBPACK_IMPORTED_MODULE_3__["default"].apiCall('/v2/api/reports/config', {
              method: 'POST',
              headers: _config__WEBPACK_IMPORTED_MODULE_3__["default"].getAuthHeaders(),
              body: JSON.stringify({
                report_id: report_id,
                context: current_context
              })
            });
          case 2:
            response = _context.v;
            if (response.ok) {
              _context.n = 3;
              break;
            }
            throw new Error('Failed to load report configuration');
          case 3:
            _context.n = 4;
            return response.json();
          case 4:
            response_data = _context.v;
            // Handle nested data structure
            config_data = response_data.data && response_data.data.config ? response_data.data : response_data;
            if (!(config_data.success || response_data.data && response_data.data.success)) {
              _context.n = 5;
              break;
            }
            // Extract config from proper location
            server_config = config_data.config || response_data.data.config; // Merge server config with any overrides
            merged_config = _objectSpread(_objectSpread(_objectSpread({}, server_config), overrides), {}, {
              columns: _objectSpread(_objectSpread({}, server_config.columns), overrides.columns || {}),
              actions: [].concat(_toConsumableArray(server_config.actions || []), _toConsumableArray(overrides.extra_actions || []))
            });
            set_table_config(merged_config);
            set_page_size(merged_config.page_length || 25);

            // Callback if provided
            if (on_config_loaded) {
              on_config_loaded(merged_config);
            }
            _context.n = 6;
            break;
          case 5:
            throw new Error(config_data.error || 'Invalid configuration received');
          case 6:
            _context.n = 8;
            break;
          case 7:
            _context.p = 7;
            _t = _context.v;
            console.error('Failed to load table configuration:', _t);
            set_error("Failed to load table configuration: ".concat(_t.message));
          case 8:
            _context.p = 8;
            set_config_loading(false);
            return _context.f(8);
          case 9:
            return _context.a(2);
        }
      }, _callee, null, [[1, 7, 8, 9]]);
    }));
    return function load_table_config() {
      return _ref2.apply(this, arguments);
    };
  }();

  // Load config on mount or when report_id changes
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    load_table_config();
  }, [report_id, current_context]);

  // API request helper
  var make_api_request = /*#__PURE__*/function () {
    var _ref3 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2(operation) {
      var additional_data,
        model_to_use,
        base_data,
        request_data,
        response,
        _args2 = arguments,
        _t2;
      return _regenerator().w(function (_context2) {
        while (1) switch (_context2.n) {
          case 0:
            additional_data = _args2.length > 1 && _args2[1] !== undefined ? _args2[1] : {};
            if (table_config) {
              _context2.n = 1;
              break;
            }
            return _context2.a(2);
          case 1:
            // When report_id exists, use ReportHandler as the model
            model_to_use = table_config.report_id ? 'ReportHandler' : table_config.model_name;
            base_data = {
              model: model_to_use,
              operation: operation
            };
            if (table_config.report_id !== null) {
              base_data.report_id = table_config.report_id;
            }
            if (table_config.is_model !== null) {
              base_data.is_model = table_config.is_model;
            }
            if (current_context) {
              base_data.context = current_context;
            }
            request_data = _objectSpread(_objectSpread({}, base_data), additional_data);
            _context2.p = 2;
            _context2.n = 3;
            return _config__WEBPACK_IMPORTED_MODULE_3__["default"].apiCall(table_config.api_url || '/api/data', {
              method: 'POST',
              headers: _config__WEBPACK_IMPORTED_MODULE_3__["default"].getAuthHeaders(),
              body: JSON.stringify(request_data)
            });
          case 3:
            response = _context2.v;
            if (response.ok) {
              _context2.n = 4;
              break;
            }
            throw new Error("API request failed: ".concat(response.statusText));
          case 4:
            _context2.n = 5;
            return response.json();
          case 5:
            return _context2.a(2, _context2.v);
          case 6:
            _context2.p = 6;
            _t2 = _context2.v;
            console.error("API request failed for operation '".concat(operation, "':"), _t2);
            throw _t2;
          case 7:
            return _context2.a(2);
        }
      }, _callee2, null, [[2, 6]]);
    }));
    return function make_api_request(_x) {
      return _ref3.apply(this, arguments);
    };
  }();

  // Get ordered columns
  var get_ordered_columns = function get_ordered_columns() {
    if (!(table_config !== null && table_config !== void 0 && table_config.columns)) return [];
    return Object.entries(table_config.columns).sort(function (_ref4, _ref5) {
      var _ref6 = _slicedToArray(_ref4, 2),
        a = _ref6[0],
        conf_a = _ref6[1];
      var _ref7 = _slicedToArray(_ref5, 2),
        b = _ref7[0],
        conf_b = _ref7[1];
      return (conf_a.order_index || 999) - (conf_b.order_index || 999);
    }).map(function (_ref8) {
      var _ref9 = _slicedToArray(_ref8, 2),
        name = _ref9[0],
        config = _ref9[1];
      return _objectSpread({
        name: name
      }, config);
    });
  };

  // Get searchable columns
  var get_searchable_columns = function get_searchable_columns() {
    if (!(table_config !== null && table_config !== void 0 && table_config.columns)) return [];
    return Object.entries(table_config.columns).filter(function (_ref0) {
      var _ref1 = _slicedToArray(_ref0, 2),
        name = _ref1[0],
        config = _ref1[1];
      return config.searchable === true;
    }).map(function (_ref10) {
      var _ref11 = _slicedToArray(_ref10, 1),
        name = _ref11[0];
      return name;
    });
  };

  // Get actions by type
  var get_page_actions = function get_page_actions() {
    if (!(table_config !== null && table_config !== void 0 && table_config.actions)) return [];
    return table_config.actions.filter(function (action) {
      return action.mode === 'page';
    });
  };
  var get_row_actions = function get_row_actions() {
    if (!(table_config !== null && table_config !== void 0 && table_config.actions)) return [];
    return table_config.actions.filter(function (action) {
      return !action.mode || action.mode === 'row';
    });
  };

  // Load data
  var load_data = (0,react__WEBPACK_IMPORTED_MODULE_0__.useCallback)(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee3() {
    var _table_config$custom_, _ordered_columns, searchable_columns, _row_actions, all_columns, order, row_limit, effective_page_size, response, _t3;
    return _regenerator().w(function (_context3) {
      while (1) switch (_context3.n) {
        case 0:
          if (table_config) {
            _context3.n = 1;
            break;
          }
          return _context3.a(2);
        case 1:
          set_loading(true);
          set_error(null);
          _context3.p = 2;
          _ordered_columns = get_ordered_columns();
          searchable_columns = get_searchable_columns();
          _row_actions = get_row_actions(); // Build columns for API (matching DataTables format)
          all_columns = _ordered_columns.map(function (col, index) {
            return {
              data: col.name,
              name: col.name,
              searchable: col.searchable || false,
              orderable: col.orderable !== false,
              search: {
                value: '',
                regex: false
              }
            };
          }); // Add actions column if needed
          if (_row_actions.length > 0) {
            all_columns.push({
              data: null,
              name: 'actions',
              searchable: false,
              orderable: false,
              search: {
                value: '',
                regex: false
              }
            });
          }

          // DataTables-style order array
          order = sort_config.column ? [{
            column: _ordered_columns.findIndex(function (col) {
              return col.name === sort_config.column;
            }),
            dir: sort_config.direction || 'asc'
          }] : []; // Apply row limit from custom_options if present
          row_limit = ((_table_config$custom_ = table_config.custom_options) === null || _table_config$custom_ === void 0 ? void 0 : _table_config$custom_.row_limit) || 10000;
          effective_page_size = Math.min(page_size, row_limit);
          _context3.n = 3;
          return make_api_request('list', {
            draw: 1,
            start: (current_page - 1) * effective_page_size,
            length: effective_page_size,
            search: search_term,
            order: order,
            columns: all_columns,
            return_columns: _ordered_columns.map(function (col) {
              return col.name;
            }),
            searchable_columns: searchable_columns
          });
        case 3:
          response = _context3.v;
          if (!response.success) {
            _context3.n = 4;
            break;
          }
          set_data(response.data || []);
          set_total_records(response.recordsTotal || 0);
          set_filtered_records(response.recordsFiltered || response.recordsTotal || 0);
          set_initial_loading(false);
          _context3.n = 5;
          break;
        case 4:
          throw new Error(response.error || 'Failed to load data');
        case 5:
          _context3.n = 7;
          break;
        case 6:
          _context3.p = 6;
          _t3 = _context3.v;
          console.error('Failed to load table data:', _t3);
          set_error(_t3.message);
          set_data([]);
        case 7:
          _context3.p = 7;
          set_loading(false);
          return _context3.f(7);
        case 8:
          return _context3.a(2);
      }
    }, _callee3, null, [[2, 6, 7, 8]]);
  })), [current_page, page_size, search_term, sort_config, table_config]);

  // Load data when config is ready and dependencies change
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    if (table_config && !config_loading) {
      load_data();
    }
  }, [load_data, table_config, config_loading]);

  // Handle sorting
  var handle_sort = function handle_sort(column_name) {
    set_sort_config(function (prev) {
      if (prev.column === column_name) {
        return {
          column: column_name,
          direction: prev.direction === 'asc' ? 'desc' : 'asc'
        };
      } else {
        return {
          column: column_name,
          direction: 'asc'
        };
      }
    });
    set_current_page(1);
  };

  // Handle search
  var handle_search = function handle_search(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      set_search_term(e.target.value);
      set_current_page(1);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      e.target.value = '';
      set_search_term('');
      set_current_page(1);
    }
  };

  // Handle pagination
  var total_pages = Math.ceil(filtered_records / page_size) || 1;
  var go_to_page = function go_to_page(page) {
    if (page >= 1 && page <= total_pages) {
      set_current_page(page);
    }
  };

  // Handle actions
  var handle_action = /*#__PURE__*/function () {
    var _ref13 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee4(action) {
      var row_id,
        action_type,
        _args4 = arguments,
        _t4;
      return _regenerator().w(function (_context4) {
        while (1) switch (_context4.n) {
          case 0:
            row_id = _args4.length > 1 && _args4[1] !== undefined ? _args4[1] : null;
            console.log('handle_action called:', {
              action: action,
              row_id: row_id,
              action_type: action.action_type
            });
            if (!(action.confirm && !window.confirm(action.confirm_message || action.confirm))) {
              _context4.n = 1;
              break;
            }
            return _context4.a(2);
          case 1:
            action_type = action.action_type || 'api';
            _t4 = action_type;
            _context4.n = _t4 === 'javascript' ? 2 : _t4 === 'navigate' ? 3 : _t4 === 'htmx' ? 4 : _t4 === 'api' ? 5 : 5;
            break;
          case 2:
            handle_javascript_action(action, row_id);
            return _context4.a(3, 7);
          case 3:
            handle_navigate_action(action, row_id);
            return _context4.a(3, 7);
          case 4:
            handle_htmx_action(action, row_id);
            return _context4.a(3, 7);
          case 5:
            _context4.n = 6;
            return handle_api_action(action, row_id);
          case 6:
            return _context4.a(3, 7);
          case 7:
            return _context4.a(2);
        }
      }, _callee4);
    }));
    return function handle_action(_x2) {
      return _ref13.apply(this, arguments);
    };
  }();
  var handle_javascript_action = function handle_javascript_action(action, row_id) {
    if (action.javascript) {
      try {
        var func = new Function('id', 'row_data', 'table', 'action', action.javascript);
        var row_data = row_id ? data.find(function (row) {
          return row.id === row_id;
        }) : null;
        func.call(_this, row_id, row_data, {
          reload: load_data
        }, action);
      } catch (error) {
        var _window$showToast, _window;
        console.error('Error executing JavaScript action:', error);
        (_window$showToast = (_window = window).showToast) === null || _window$showToast === void 0 || _window$showToast.call(_window, 'Error executing action', 'error');
      }
    }
  };
  var handle_navigate_action = function handle_navigate_action(action, row_id) {
    var _action$url;
    console.log('handle_navigate_action called:', {
      action: action,
      row_id: row_id
    });
    var view = action.view || ((_action$url = action.url) === null || _action$url === void 0 ? void 0 : _action$url.replace(/^\//, '')) || 'home';
    var params = _objectSpread({}, action.params);
    if (row_id) {
      params.id = row_id;
    }
    console.log('Navigating to:', {
      view: view,
      params: params
    });
    navigate_to(view, params);
  };
  var handle_htmx_action = function handle_htmx_action(action, row_id) {
    // Create a form and submit it for HTMX-style navigation
    var form = document.createElement('form');
    form.method = action.method || 'POST';
    form.action = action.url;

    // Add row_id if present
    if (row_id) {
      var id_input = document.createElement('input');
      id_input.type = 'hidden';
      id_input.name = 'id';
      id_input.value = row_id;
      form.appendChild(id_input);
    }

    // Add any payload data
    if (action.payload) {
      Object.entries(action.payload).forEach(function (_ref14) {
        var _ref15 = _slicedToArray(_ref14, 2),
          key = _ref15[0],
          value = _ref15[1];
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
      });
    }

    // Add custom headers as hidden fields if needed
    if (action.headers) {
      Object.entries(action.headers).forEach(function (_ref16) {
        var _ref17 = _slicedToArray(_ref16, 2),
          key = _ref17[0],
          value = _ref17[1];
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = "_header_".concat(key);
        input.value = value;
        form.appendChild(input);
      });
    }
    document.body.appendChild(form);
    form.submit();
  };
  var handle_api_action = /*#__PURE__*/function () {
    var _ref18 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee5(action, row_id) {
      var model_to_use, request_data, method, response, result, _window$showToast2, _window2, _window$showToast3, _window3, _window$showToast4, _window4, _t5;
      return _regenerator().w(function (_context5) {
        while (1) switch (_context5.n) {
          case 0:
            _context5.p = 0;
            // When report_id exists, use ReportHandler as the model
            model_to_use = table_config.report_id ? 'ReportHandler' : table_config.model_name;
            request_data = _objectSpread({
              id: row_id,
              model: model_to_use
            }, action.payload || {});
            if (table_config.report_id !== null) {
              request_data.report_id = table_config.report_id;
            }
            method = (action.method || 'POST').toLowerCase();
            _context5.n = 1;
            return _config__WEBPACK_IMPORTED_MODULE_3__["default"].apiCall(action.url || table_config.api_url, {
              method: method.toUpperCase(),
              headers: _objectSpread(_objectSpread({}, _config__WEBPACK_IMPORTED_MODULE_3__["default"].getAuthHeaders()), action.headers || {}),
              body: JSON.stringify(request_data)
            });
          case 1:
            response = _context5.v;
            _context5.n = 2;
            return response.json();
          case 2:
            result = _context5.v;
            if (result.success) {
              (_window$showToast2 = (_window2 = window).showToast) === null || _window$showToast2 === void 0 || _window$showToast2.call(_window2, result.message || "".concat(action.title || action.name, " completed"), 'success');
              if (result.reload_table !== false) {
                load_data();
              }
            } else {
              (_window$showToast3 = (_window3 = window).showToast) === null || _window$showToast3 === void 0 || _window$showToast3.call(_window3, result.error || "".concat(action.title || action.name, " failed"), 'error');
            }
            _context5.n = 4;
            break;
          case 3:
            _context5.p = 3;
            _t5 = _context5.v;
            console.error('API action failed:', _t5);
            (_window$showToast4 = (_window4 = window).showToast) === null || _window$showToast4 === void 0 || _window$showToast4.call(_window4, "Failed to execute ".concat(action.title || action.name), 'error');
          case 4:
            return _context5.a(2);
        }
      }, _callee5, null, [[0, 3]]);
    }));
    return function handle_api_action(_x3, _x4) {
      return _ref18.apply(this, arguments);
    };
  }();

  // Format date based on format string
  var format_date = function format_date(value, format_string) {
    if (!value) return '';
    var date = new Date(value);

    // Handle common date format patterns
    if (format_string) {
      // Simple replacement for common patterns
      var formatted = format_string;

      // Year
      formatted = formatted.replace('%Y', date.getFullYear());
      formatted = formatted.replace('%y', String(date.getFullYear()).slice(-2));

      // Month
      formatted = formatted.replace('%m', String(date.getMonth() + 1).padStart(2, '0'));
      formatted = formatted.replace('%B', date.toLocaleDateString('en-US', {
        month: 'long'
      }));
      formatted = formatted.replace('%b', date.toLocaleDateString('en-US', {
        month: 'short'
      }));

      // Day
      formatted = formatted.replace('%d', String(date.getDate()).padStart(2, '0'));

      // Hour
      formatted = formatted.replace('%H', String(date.getHours()).padStart(2, '0'));
      formatted = formatted.replace('%I', String(date.getHours() % 12 || 12).padStart(2, '0'));

      // Minute
      formatted = formatted.replace('%M', String(date.getMinutes()).padStart(2, '0'));

      // Second
      formatted = formatted.replace('%S', String(date.getSeconds()).padStart(2, '0'));

      // AM/PM
      formatted = formatted.replace('%p', date.getHours() >= 12 ? 'PM' : 'AM');
      return formatted;
    }

    // Default formatting
    return date.toLocaleDateString();
  };

  // Render column value
  var render_column_value = function render_column_value(column, value, row) {
    // Custom renderer
    if (column.render) {
      // If render is a string, it might be a function name or template
      if (typeof column.render === 'string') {
        // Handle template syntax like "{{value}}" or function references
        return value || '';
      }
      return column.render(value, row);
    }

    // Handle date formatting with format string
    if (column.type === 'datetime' || column.format && column.format.includes('%')) {
      return format_date(value, column.format);
    }

    // Type-based rendering
    if (column.format === 'boolean' || column.type === 'boolean') {
      return value ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
        className: "badge bg-success"
      }, "Yes") : /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
        className: "badge bg-secondary"
      }, "No");
    }
    if (column.format === 'currency') {
      return "$".concat(new Intl.NumberFormat().format(value || 0));
    }
    if (column.format === 'number') {
      return new Intl.NumberFormat().format(value || 0);
    }
    if (column.format === 'percent') {
      return "".concat((value * 100).toFixed(1), "%");
    }

    // Default
    return value || '';
  };

  // Get alignment class
  var get_alignment_class = function get_alignment_class(alignment) {
    switch (alignment) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-end';
      case 'left':
      default:
        return 'text-start';
    }
  };

  // Loading state
  if (config_loading) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "d-flex justify-content-center align-items-center",
      style: {
        minHeight: '400px'
      }
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "text-center"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "spinner-border text-primary mb-3",
      role: "status"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
      className: "visually-hidden"
    }, "Loading...")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("p", null, "Loading table configuration...")));
  }

  // Error state
  if (!table_config && !config_loading) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "alert alert-danger"
    }, "Failed to load table configuration");
  }

  // Calculate pagination range
  var get_pagination_range = function get_pagination_range() {
    var delta = 2;
    var range = [];
    var range_with_dots = [];
    var l;
    for (var i = 1; i <= total_pages; i++) {
      if (i === 1 || i === total_pages || i >= current_page - delta && i <= current_page + delta) {
        range.push(i);
      }
    }
    range.forEach(function (i) {
      if (l) {
        if (i - l === 2) {
          range_with_dots.push(l + 1);
        } else if (i - l !== 1) {
          range_with_dots.push('...');
        }
      }
      range_with_dots.push(i);
      l = i;
    });
    return range_with_dots;
  };

  // Main render
  var ordered_columns = get_ordered_columns();
  var page_actions = get_page_actions();
  var row_actions = get_row_actions();
  var title = table_config.table_title || "".concat(table_config.model_name, " Management");
  var description = table_config.table_description || "Manage ".concat((_table_config$model_n = table_config.model_name) === null || _table_config$model_n === void 0 ? void 0 : _table_config$model_n.toLowerCase(), " records");
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    id: table_config.container_id || "".concat(table_config.report_name, "_table"),
    className: table_config.is_wide ? 'container-fluid' : ''
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("style", null, "\n                .table-wrapper {\n                    position: relative;\n                }\n\n                .table-loading th .fas.fa-sort-up,\n                .table-loading th .fas.fa-sort-down {\n                    animation: pulse 1s infinite;\n                }\n\n                @keyframes pulse {\n                    0% { opacity: 1; }\n                    50% { opacity: 0.5; }\n                    100% { opacity: 1; }\n                }\n            "), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "row mb-4"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "col"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h4", {
    className: "mb-0 fw-bold"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-table me-2"
  }), title), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("small", {
    className: "text-body-secondary"
  }, description)), page_actions.length > 0 && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "btn-group"
  }, page_actions.map(function (action) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
      key: action.name,
      className: "btn btn-".concat(action.color || 'secondary'),
      onClick: function onClick() {
        return handle_action(action);
      }
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
      className: "".concat(action.icon, " me-2")
    }), action.title || action.name);
  }))))), table_config.show_search && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "row mb-4"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("input", {
    ref: search_input_ref,
    type: "text",
    className: "form-control",
    placeholder: "Search ".concat((_table_config$model_n2 = table_config.model_name) === null || _table_config$model_n2 === void 0 ? void 0 : _table_config$model_n2.toLowerCase(), "s..."),
    onKeyDown: handle_search
  }))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "row"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "col"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-body"
  }, error && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "alert alert-danger"
  }, error), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "table-responsive table-wrapper"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("table", {
    className: "table table-hover ".concat(loading && !initial_loading ? 'table-loading' : '')
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("thead", null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("tr", null, ordered_columns.map(function (column) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("th", {
      key: column.name,
      className: get_alignment_class(column.alignment),
      style: {
        cursor: column.orderable !== false ? 'pointer' : 'default',
        width: column.width || 'auto'
      },
      onClick: function onClick() {
        return column.orderable !== false && handle_sort(column.name);
      }
    }, column.label || column.name, column.orderable !== false && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
      className: "ms-1"
    }, sort_config.column === column.name ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
      className: "fas fa-sort-".concat(sort_config.direction === 'asc' ? 'up' : 'down')
    }) : /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
      className: "fas fa-sort text-muted"
    })));
  }), row_actions.length > 0 && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("th", {
    className: "text-center"
  }, "Actions"))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("tbody", null, initial_loading ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("tr", null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("td", {
    colSpan: ordered_columns.length + (row_actions.length > 0 ? 1 : 0),
    className: "text-center py-4"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "spinner-border spinner-border-sm me-2",
    role: "status"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
    className: "visually-hidden"
  }, "Loading...")), "Loading data...")) : data.length === 0 ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("tr", null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("td", {
    colSpan: ordered_columns.length + (row_actions.length > 0 ? 1 : 0),
    className: "text-center py-4"
  }, "No records found")) : data.map(function (row, row_index) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("tr", {
      key: row.id || row_index
    }, ordered_columns.map(function (column) {
      return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("td", {
        key: column.name,
        className: get_alignment_class(column.alignment)
      }, render_column_value(column, row[column.name], row));
    }), row_actions.length > 0 && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("td", {
      className: "text-center"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "btn-group btn-group-sm"
    }, row_actions.map(function (action) {
      return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
        key: action.name,
        className: "btn btn-".concat(action.color || 'secondary'),
        onClick: function onClick() {
          return handle_action(action, row.id);
        },
        title: action.title || action.name
      }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
        className: action.icon
      }));
    }))));
  })))), table_config.show_pagination !== false && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "d-flex justify-content-between align-items-center mt-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "text-muted"
  }, "Showing ", (current_page - 1) * page_size + 1, " to", ' ', Math.min(current_page * page_size, filtered_records), " of", ' ', filtered_records, " entries", filtered_records !== total_records && " (filtered from ".concat(total_records, " total entries)")), total_pages > 1 && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("nav", null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("ul", {
    className: "pagination mb-0"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("li", {
    className: "page-item ".concat(current_page === 1 ? 'disabled' : '')
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    className: "page-link",
    onClick: function onClick() {
      return go_to_page(current_page - 1);
    },
    disabled: current_page === 1
  }, "Previous")), get_pagination_range().map(function (page, index) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("li", {
      key: index,
      className: "page-item ".concat(page === current_page ? 'active' : '', " ").concat(page === '...' ? 'disabled' : '')
    }, page === '...' ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
      className: "page-link"
    }, "...") : /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
      className: "page-link",
      onClick: function onClick() {
        return go_to_page(page);
      }
    }, page));
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("li", {
    className: "page-item ".concat(current_page === total_pages ? 'disabled' : '')
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    className: "page-link",
    onClick: function onClick() {
      return go_to_page(current_page + 1);
    },
    disabled: current_page === total_pages
  }, "Next"))))))))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (ServerDataTable);

/***/ }),

/***/ 345:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(521);
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _construct(t, e, r) { if (_isNativeReflectConstruct()) return Reflect.construct.apply(null, arguments); var o = [null]; o.push.apply(o, e); var p = new (t.bind.apply(t, o))(); return r && _setPrototypeOf(p, r.prototype), p; }
function _setPrototypeOf(t, e) { return _setPrototypeOf = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function (t, e) { return t.__proto__ = e, t; }, _setPrototypeOf(t, e); }
function _isNativeReflectConstruct() { try { var t = !Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); } catch (t) {} return (_isNativeReflectConstruct = function _isNativeReflectConstruct() { return !!t; })(); }
function _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _iterableToArray(r) { if ("undefined" != typeof Symbol && null != r[Symbol.iterator] || null != r["@@iterator"]) return Array.from(r); }
function _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }


var ComponentBuilder = function ComponentBuilder() {
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(''),
    _useState2 = _slicedToArray(_useState, 2),
    component_name = _useState2[0],
    setComponentName = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(''),
    _useState4 = _slicedToArray(_useState3, 2),
    component_code = _useState4[0],
    setComponentCode = _useState4[1];
  var _useState5 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(''),
    _useState6 = _slicedToArray(_useState5, 2),
    style_code = _useState6[0],
    setStyleCode = _useState6[1];
  var _useState7 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(''),
    _useState8 = _slicedToArray(_useState7, 2),
    description = _useState8[0],
    setDescription = _useState8[1];
  var _useState9 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState0 = _slicedToArray(_useState9, 2),
    preview_mode = _useState0[0],
    setPreviewMode = _useState0[1];
  var _useState1 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState10 = _slicedToArray(_useState1, 2),
    error = _useState10[0],
    setError = _useState10[1];
  var _useState11 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState12 = _slicedToArray(_useState11, 2),
    success = _useState12[0],
    setSuccess = _useState12[1];
  var preview_ref = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);
  var default_template = "// Define your component\nconst Component = () => {\n    const [count, setCount] = useState(0);\n\n    return (\n        <div className=\"custom-component\">\n            <h2>My Custom Component</h2>\n            <p>Count: {count}</p>\n            <button\n                onClick={() => setCount(count + 1)}\n                className=\"btn btn-primary\"\n            >\n                Increment\n            </button>\n        </div>\n    );\n};\n\n// Component must be the last expression";
  var handlePreview = function handlePreview() {
    setError(null);
    try {
      // Create sandbox globals
      var sandbox_globals = {
        React: react__WEBPACK_IMPORTED_MODULE_0__,
        useState: react__WEBPACK_IMPORTED_MODULE_0__.useState,
        useEffect: react__WEBPACK_IMPORTED_MODULE_0__.useEffect,
        useCallback: react__WEBPACK_IMPORTED_MODULE_0__.useCallback,
        useMemo: react__WEBPACK_IMPORTED_MODULE_0__.useMemo,
        useRef: react__WEBPACK_IMPORTED_MODULE_0__.useRef
      };

      // Test compile the component
      var component_function = _construct(Function, _toConsumableArray(Object.keys(sandbox_globals)).concat(["\n                ".concat(component_code || default_template, "\n                return Component;\n                ")]));
      var TestComponent = component_function.apply(void 0, _toConsumableArray(Object.values(sandbox_globals)));

      // Render preview
      setPreviewMode(true);

      // Clear previous preview
      if (preview_ref.current) {
        var root = ReactDOM.createRoot(preview_ref.current);
        root.render(/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(TestComponent, null));
      }
    } catch (err) {
      setError("Preview error: ".concat(err.message));
      setPreviewMode(false);
    }
  };
  var handleSave = /*#__PURE__*/function () {
    var _ref = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
      var response, data, _t;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.n) {
          case 0:
            setError(null);
            setSuccess(null);
            if (!(!component_name || !component_code)) {
              _context.n = 1;
              break;
            }
            setError('Component name and code are required');
            return _context.a(2);
          case 1:
            _context.p = 1;
            _context.n = 2;
            return _config__WEBPACK_IMPORTED_MODULE_1__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_1__["default"].getUrl('/components'), {
              method: 'POST',
              headers: _config__WEBPACK_IMPORTED_MODULE_1__["default"].getAuthHeaders(),
              body: JSON.stringify({
                name: component_name,
                component_code: component_code,
                style_code: style_code,
                description: description,
                default_props: {}
              })
            });
          case 2:
            response = _context.v;
            _context.n = 3;
            return response.json();
          case 3:
            data = _context.v;
            if (response.ok) {
              _context.n = 4;
              break;
            }
            throw new Error(data.error || 'Failed to save component');
          case 4:
            setSuccess("Component \"".concat(data.name, "\" created successfully!"));

            // Reset form
            setComponentName('');
            setComponentCode('');
            setStyleCode('');
            setDescription('');
            setPreviewMode(false);
            _context.n = 6;
            break;
          case 5:
            _context.p = 5;
            _t = _context.v;
            setError(_t.message);
          case 6:
            return _context.a(2);
        }
      }, _callee, null, [[1, 5]]);
    }));
    return function handleSave() {
      return _ref.apply(this, arguments);
    };
  }();
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "container-fluid mt-4"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "row"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "col-lg-6"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h4", null, "Component Builder")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-body"
  }, error && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "alert alert-danger"
  }, error), success && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "alert alert-success"
  }, success), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "mb-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    className: "form-label"
  }, "Component Name (PascalCase)"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("input", {
    type: "text",
    className: "form-control",
    value: component_name,
    onChange: function onChange(e) {
      return setComponentName(e.target.value);
    },
    placeholder: "MyCustomComponent"
  })), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "mb-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    className: "form-label"
  }, "Description"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("textarea", {
    className: "form-control",
    rows: "2",
    value: description,
    onChange: function onChange(e) {
      return setDescription(e.target.value);
    },
    placeholder: "Describe what this component does..."
  })), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "mb-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    className: "form-label"
  }, "Component Code (React/JSX)"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("textarea", {
    className: "form-control font-monospace",
    rows: "15",
    value: component_code,
    onChange: function onChange(e) {
      return setComponentCode(e.target.value);
    },
    placeholder: default_template
  })), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "mb-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    className: "form-label"
  }, "CSS Styles (Optional)"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("textarea", {
    className: "form-control font-monospace",
    rows: "5",
    value: style_code,
    onChange: function onChange(e) {
      return setStyleCode(e.target.value);
    },
    placeholder: ".custom-component { padding: 20px; }"
  })), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "d-flex gap-2"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    className: "btn btn-secondary",
    onClick: handlePreview
  }, "Preview"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    className: "btn btn-primary",
    onClick: handleSave,
    disabled: !component_name || !component_code
  }, "Save Component"))))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "col-lg-6"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h4", null, "Preview")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-body"
  }, preview_mode ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(react__WEBPACK_IMPORTED_MODULE_0__.Fragment, null, style_code && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("style", {
    dangerouslySetInnerHTML: {
      __html: style_code
    }
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    ref: preview_ref
  })) : /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "text-muted text-center p-5"
  }, "Click \"Preview\" to see your component"))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card mt-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h5", null, "Available APIs")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("pre", {
    className: "bg-light p-3 rounded"
  }, "// React Hooks\nconst [state, setState] = useState(initialValue);\nuseEffect(() => { ... }, [dependencies]);\nconst memoized = useMemo(() => computeValue, [deps]);\nconst callback = useCallback(() => { ... }, [deps]);\nconst ref = useRef(initialValue);\n\n// API Calls\napi.get('/endpoint') // GET request\napi.post('/endpoint', { data }) // POST request\n\n// Component must return JSX\nreturn <div>Your content</div>;\n\n// Access component props\nconst Component = ({ config }) => {\n    // Use config passed from route\n};"))))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (ComponentBuilder);

/***/ }),

/***/ 397:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _App__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(649);
/* harmony import */ var _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(721);
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function _createForOfIteratorHelper(r, e) { var t = "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (!t) { if (Array.isArray(r) || (t = _unsupportedIterableToArray(r)) || e && r && "number" == typeof r.length) { t && (r = t); var _n = 0, F = function F() {}; return { s: F, n: function n() { return _n >= r.length ? { done: !0 } : { done: !1, value: r[_n++] }; }, e: function e(r) { throw r; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var o, a = !0, u = !1; return { s: function s() { t = t.call(r); }, n: function n() { var r = t.next(); return a = r.done, r; }, e: function e(r) { u = !0, o = r; }, f: function f() { try { a || null == t["return"] || t["return"](); } finally { if (u) throw o; } } }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }



var SidebarMenu = function SidebarMenu(_ref) {
  var collapsed = _ref.collapsed,
    onToggleCollapse = _ref.onToggleCollapse;
  var _useNavigation = (0,_App__WEBPACK_IMPORTED_MODULE_1__.useNavigation)(),
    current_view = _useNavigation.current_view,
    navigate_to = _useNavigation.navigate_to;
  var _useSite = (0,_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__.useSite)(),
    _useSite$menu_items = _useSite.menu_items,
    menu_items = _useSite$menu_items === void 0 ? [] : _useSite$menu_items,
    current_context = _useSite.current_context;

  // Debug logging
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    console.log('SidebarMenu: Current context:', current_context);
    console.log('SidebarMenu: Menu items:', menu_items);
  }, [current_context, menu_items]);

  // Initialize expanded menus from localStorage
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(function () {
      var saved = localStorage.getItem('expanded_menus');
      return saved ? JSON.parse(saved) : {};
    }),
    _useState2 = _slicedToArray(_useState, 2),
    expanded_menus = _useState2[0],
    setExpandedMenus = _useState2[1];

  // Save expanded menus state to localStorage whenever it changes
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    localStorage.setItem('expanded_menus', JSON.stringify(expanded_menus));
  }, [expanded_menus]);

  // Auto-expand active menu sections when view changes
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    if (menu_items.length > 0) {
      auto_expand_active_menus(menu_items);
    }
  }, [current_view, menu_items]);

  // Convert URL to view name (remove leading slash and handle nested paths)
  var url_to_view = function url_to_view(url) {
    if (!url) return 'home';
    return url.replace(/^\//, '') || 'home';
  };

  // Check if a menu item is active
  var is_item_active = function is_item_active(item) {
    var item_view = url_to_view(item.url);
    return current_view === item_view;
  };

  // Auto-expand menu sections that contain the current active view
  var auto_expand_active_menus = function auto_expand_active_menus(items) {
    var _find_and_expand_active = function find_and_expand_active(items) {
      var parent_id = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
      var _iterator = _createForOfIteratorHelper(items),
        _step;
      try {
        var _loop = function _loop() {
            var item = _step.value;
            if (is_item_active(item)) {
              // Found active item, expand its parent
              if (parent_id && !expanded_menus[parent_id]) {
                setExpandedMenus(function (prev) {
                  return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, parent_id, true));
                });
              }
              return {
                v: true
              };
            }
            if (item.items && item.items.length > 0) {
              var found = _find_and_expand_active(item.items, item.id);
              if (found && !expanded_menus[item.id]) {
                setExpandedMenus(function (prev) {
                  return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, item.id, true));
                });
              }
            }
          },
          _ret;
        for (_iterator.s(); !(_step = _iterator.n()).done;) {
          _ret = _loop();
          if (_ret) return _ret.v;
        }
      } catch (err) {
        _iterator.e(err);
      } finally {
        _iterator.f();
      }
      return false;
    };
    _find_and_expand_active(items);
  };
  var toggle_menu_expansion = function toggle_menu_expansion(menu_id) {
    setExpandedMenus(function (prev) {
      return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, menu_id, !prev[menu_id]));
    });
  };
  var handle_navigation = function handle_navigation(url) {
    var view = url_to_view(url);
    navigate_to(view);
  };
  var _render_menu_item = function render_menu_item(item) {
    var depth = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;
    var has_children = item.items && item.items.length > 0;
    var is_expanded = expanded_menus[item.id];
    var is_active = is_item_active(item);

    // Check if any child is active
    var _has_active_child = function has_active_child(items) {
      return items === null || items === void 0 ? void 0 : items.some(function (child) {
        return is_item_active(child) || child.items && _has_active_child(child.items);
      });
    };
    var is_parent_of_active = has_children && _has_active_child(item.items);
    // Handle tier type items (parent categories)
    if (item.type === 'tier') {
      return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
        key: item.id,
        className: "sidebar_section"
      }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
        className: "sidebar_section_header ".concat(is_parent_of_active ? 'has-active-child' : ''),
        onClick: function onClick() {
          return toggle_menu_expansion(item.id);
        },
        style: {
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }
      }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h5", {
        style: {
          margin: 0,
          display: 'flex',
          alignItems: 'center'
        }
      }, item.icon && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
        className: "fas ".concat(item.icon, " me-2")
      }), item.display), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
        className: "fas fa-chevron-".concat(is_expanded ? 'down' : 'right')
      })), is_expanded && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("ul", {
        className: "nav flex-column"
      }, item.items.map(function (child) {
        return _render_menu_item(child, depth + 1);
      })));
    }

    // Handle link type items
    if (item.type === 'link') {
      var _item$url, _item$url2;
      var is_external = ((_item$url = item.url) === null || _item$url === void 0 ? void 0 : _item$url.startsWith('http://')) || ((_item$url2 = item.url) === null || _item$url2 === void 0 ? void 0 : _item$url2.startsWith('https://'));
      return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("li", {
        key: item.id,
        className: "nav-item"
      }, has_children ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(react__WEBPACK_IMPORTED_MODULE_0__.Fragment, null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
        type: "button",
        className: "nav-link d-flex justify-content-between align-items-center ".concat(is_active ? 'active' : '', " ").concat(is_parent_of_active ? 'has-active-child' : ''),
        onClick: function onClick(e) {
          e.preventDefault();
          toggle_menu_expansion(item.id);
        },
        style: {
          width: '100%',
          border: 'none',
          background: 'transparent',
          textAlign: 'left',
          padding: 'var(--bs-nav-link-padding-y) var(--bs-nav-link-padding-x)'
        }
      }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", null, item.icon && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
        className: "fas ".concat(item.icon, " me-2")
      }), item.display), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
        className: "fas fa-chevron-".concat(is_expanded ? 'down' : 'right')
      })), is_expanded && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("ul", {
        className: "nav flex-column ms-3"
      }, item.items.map(function (child) {
        return _render_menu_item(child, depth + 1);
      }))) : is_external ? /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("a", {
        href: item.url,
        className: "nav-link ".concat(is_active ? 'active' : ''),
        target: item.new_tab ? '_blank' : undefined,
        rel: item.new_tab ? 'noopener noreferrer' : undefined
      }, item.icon && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
        className: "fas ".concat(item.icon, " me-2")
      }), item.display) : /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
        type: "button",
        className: "nav-link ".concat(is_active ? 'active' : ''),
        onClick: function onClick() {
          return handle_navigation(item.url);
        },
        style: {
          width: '100%',
          border: 'none',
          background: 'transparent',
          textAlign: 'left',
          cursor: 'pointer'
        }
      }, item.icon && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
        className: "fas ".concat(item.icon, " me-2")
      }), item.display));
    }
    return null;
  };
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "sidebar_container"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("aside", {
    className: "sidebar"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "sidebar_toggle",
    onClick: onToggleCollapse
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-chevron-left"
  })), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("nav", {
    className: "sidebar_nav"
  }, menu_items && menu_items.length > 0 ? menu_items.map(function (item) {
    return _render_menu_item(item);
  }) : /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "sidebar_section"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h5", null, "Navigation"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("ul", {
    className: "nav flex-column"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("li", {
    className: "nav-item"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    type: "button",
    className: "nav-link",
    onClick: function onClick() {
      return navigate_to('home');
    },
    style: {
      width: '100%',
      border: 'none',
      background: 'transparent',
      textAlign: 'left',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-home me-2"
  }), "Dashboard")))))));
};

// Memoize but include menu_items in dependency check
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.memo(SidebarMenu, function (prevProps, nextProps) {
  // Re-render if collapsed state changes
  return prevProps.collapsed === nextProps.collapsed;
}));

/***/ }),

/***/ 514:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(721);
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }


var NineDotMenu = function NineDotMenu(_ref) {
  var theme = _ref.theme,
    user = _ref.user,
    onToggleTheme = _ref.onToggleTheme,
    onLogout = _ref.onLogout;
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState2 = _slicedToArray(_useState, 2),
    is_open = _useState2[0],
    setIsOpen = _useState2[1];
  var menu_ref = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);

  // Get context data directly
  var _useSite = (0,_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_1__.useSite)(),
    current_context = _useSite.current_context,
    available_contexts = _useSite.available_contexts,
    switch_context = _useSite.switch_context;

  // Handle outside clicks
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    if (!is_open) return;
    var handle_outside_click = function handle_outside_click(e) {
      if (menu_ref.current && !menu_ref.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    // Add delay to prevent immediate trigger
    var timer = setTimeout(function () {
      document.addEventListener('click', handle_outside_click);
    }, 100);
    return function () {
      clearTimeout(timer);
      document.removeEventListener('click', handle_outside_click);
    };
  }, [is_open]);
  var handle_context_switch = function handle_context_switch(context_name) {
    switch_context(context_name);
    setIsOpen(false);
  };
  var handle_theme_toggle = function handle_theme_toggle() {
    onToggleTheme();
  };
  var handle_logout = function handle_logout(e) {
    e.preventDefault();
    onLogout();
    setIsOpen(false);
  };

  // Debug current state
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    console.log('NineDotMenu state:', {
      current_context: current_context,
      available_contexts: available_contexts,
      user: user,
      contexts_type: Array.isArray(available_contexts) ? 'array' : _typeof(available_contexts),
      contexts_content: available_contexts
    });
  }, [current_context, available_contexts, user]);
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "nine_dot_menu",
    ref: menu_ref,
    style: {
      position: 'relative'
    }
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    className: "nine_dot_btn",
    onClick: function onClick(e) {
      e.preventDefault();
      e.stopPropagation();
      setIsOpen(function (prev) {
        return !prev;
      });
    },
    type: "button",
    style: {
      background: 'none',
      border: 'none',
      padding: '8px',
      cursor: 'pointer',
      fontSize: '20px',
      color: 'inherit'
    },
    "aria-label": "Settings menu",
    "aria-expanded": is_open
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-th"
  })), is_open && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "nine_dot_dropdown",
    style: {
      position: 'absolute',
      right: 0,
      top: '100%',
      marginTop: '8px',
      minWidth: '250px',
      backgroundColor: theme === 'dark' ? 'var(--theme-surface-dark)' : 'var(--theme-surface)',
      border: "1px solid ".concat(theme === 'dark' ? 'var(--theme-border-color-dark)' : 'var(--theme-border-color)'),
      borderRadius: 'var(--theme-card-border-radius)',
      boxShadow: 'var(--theme-shadow-lg)',
      zIndex: 1000,
      padding: '16px',
      color: theme === 'dark' ? 'var(--theme-text-dark)' : 'var(--theme-text)'
    }
  }, console.log('Contexts check:', {
    available_contexts: available_contexts,
    length: available_contexts === null || available_contexts === void 0 ? void 0 : available_contexts.length,
    show: available_contexts && available_contexts.length > 1
  }), available_contexts && available_contexts.length > 0 && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(react__WEBPACK_IMPORTED_MODULE_0__.Fragment, null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "dropdown_section mb-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h6", {
    className: "mb-2",
    style: {
      color: theme === 'dark' ? 'var(--theme-text-muted-dark)' : 'var(--theme-text-muted)'
    }
  }, "Application Switcher"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "context_switcher"
  }, available_contexts.map(function (context) {
    // Compare using the ID field since that's what the server expects
    var is_active = current_context === context.name ||
    // Also check if current_context matches the context field
    context.context && current_context === context.context;

    // Debug logging
    console.log('Context comparison:', {
      context: context,
      current_context: current_context,
      is_active: is_active,
      checks: {
        name_match: current_context === context.name,
        context_match: context.context && current_context === context.context
      }
    });
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
      key: context.name,
      type: "button",
      className: "btn btn-sm w-100 mb-2 ".concat(is_active ? 'btn-primary' : 'btn-outline-secondary'),
      onClick: function onClick() {
        return handle_context_switch(context.name);
      },
      disabled: is_active
    }, context.icon && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
      className: "".concat(context.icon, " me-2")
    }), context.display || context.name);
  })))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "dropdown_section mb-3"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "theme_toggle d-flex align-items-center"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "form-check form-switch"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("input", {
    className: "form-check-input",
    type: "checkbox",
    id: "dark_mode_toggle",
    checked: theme === 'dark',
    onChange: handle_theme_toggle
  }), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("label", {
    className: "form-check-label ms-2",
    htmlFor: "dark_mode_toggle"
  }, "Dark Mode")))), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "dropdown_section"
  }, user && /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "user_info mb-3 p-2 rounded",
    style: {
      backgroundColor: theme === 'dark' ? 'var(--theme-background-dark)' : 'var(--theme-component)',
      border: "1px solid ".concat(theme === 'dark' ? 'var(--theme-border-color-dark)' : 'var(--theme-border-color)')
    }
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("small", {
    className: "d-block",
    style: {
      color: theme === 'dark' ? 'var(--theme-text-muted-dark)' : 'var(--theme-text-muted)'
    }
  }, "Logged in as:"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("strong", null, user.name || user.username || user.email)), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
    type: "button",
    className: "dropdown_link btn btn-sm btn-outline-danger w-100",
    onClick: handle_logout,
    style: {
      borderColor: 'var(--theme-danger)',
      color: 'var(--theme-danger)'
    },
    onMouseEnter: function onMouseEnter(e) {
      e.target.style.backgroundColor = 'var(--theme-danger)';
      e.target.style.color = 'white';
    },
    onMouseLeave: function onMouseLeave(e) {
      e.target.style.backgroundColor = 'transparent';
      e.target.style.color = 'var(--theme-danger)';
    }
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("i", {
    className: "fas fa-sign-out-alt me-2"
  }), "Logout"))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (NineDotMenu);

/***/ }),

/***/ 521:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
// react/src/config/index.js
var config = {
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
    var url = "".concat(config.api.base).concat(endpoint);

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
window.appConfig = config;
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (config);

/***/ }),

/***/ 590:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   AuthProvider: () => (/* binding */ AuthProvider),
/* harmony export */   useAuth: () => (/* binding */ useAuth)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(521);
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }
// react/src/contexts/AuthContext.js


var AuthContext = /*#__PURE__*/(0,react__WEBPACK_IMPORTED_MODULE_0__.createContext)(null);
var useAuth = function useAuth() {
  var context = (0,react__WEBPACK_IMPORTED_MODULE_0__.useContext)(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
var AuthProvider = function AuthProvider(_ref) {
  var children = _ref.children;
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState2 = _slicedToArray(_useState, 2),
    isAuthenticated = _useState2[0],
    setIsAuthenticated = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true),
    _useState4 = _slicedToArray(_useState3, 2),
    loading = _useState4[0],
    setLoading = _useState4[1];
  var _useState5 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState6 = _slicedToArray(_useState5, 2),
    user = _useState6[0],
    setUser = _useState6[1];

  // We'll need to access SiteContext's clear_section
  var _useState7 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState8 = _slicedToArray(_useState7, 2),
    clear_site_callback = _useState8[0],
    setClearSiteCallback = _useState8[1];

  // Refresh handling state
  var refresh_lock = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(false);
  var refresh_promise = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);
  var token_expiry = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);
  var refresh_retry_count = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(0);
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
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    checkAuth();
  }, []);
  var checkAuth = /*#__PURE__*/function () {
    var _ref2 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
      var api_token, refresh_token, expiry, refresh_success, new_api_token, new_expiry, _document$querySelect, current_token, response, data, _t;
      return _regenerator().w(function (_context) {
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
            return _config__WEBPACK_IMPORTED_MODULE_1__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_1__["default"].getUrl(_config__WEBPACK_IMPORTED_MODULE_1__["default"].api.endpoints.auth.validate), {
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
    var _ref3 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2(username, password, remember) {
      var _document$querySelect2, response, data, expiry, error_data, _t2;
      return _regenerator().w(function (_context2) {
        while (1) switch (_context2.n) {
          case 0:
            _context2.p = 0;
            _context2.n = 1;
            return _config__WEBPACK_IMPORTED_MODULE_1__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_1__["default"].getUrl(_config__WEBPACK_IMPORTED_MODULE_1__["default"].api.endpoints.auth.login), {
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
    var _ref4 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee4() {
      return _regenerator().w(function (_context4) {
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
            refresh_promise.current = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee3() {
              var refresh_token, _document$querySelect3, response, data, expiry, _t3;
              return _regenerator().w(function (_context3) {
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
                    return _config__WEBPACK_IMPORTED_MODULE_1__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_1__["default"].getUrl(_config__WEBPACK_IMPORTED_MODULE_1__["default"].api.endpoints.auth.refresh), {
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
    token_check_interval = setInterval(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee5() {
      var api_token, refresh_success, _document$querySelect4, response, _refresh_success, _t4;
      return _regenerator().w(function (_context5) {
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
            return _config__WEBPACK_IMPORTED_MODULE_1__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_1__["default"].getUrl(_config__WEBPACK_IMPORTED_MODULE_1__["default"].api.endpoints.auth.validate), {
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
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    return function () {
      stop_token_check_interval();
    };
  }, []);

  // Set up global auth headers helper - MOVED TO SEPARATE useEffect
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
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
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    // Only set up interceptor after initial auth check is complete
    if (loading) return;
    var original_fetch = window.fetch;
    window.fetch = /*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee6() {
      var _len,
        args,
        _key,
        response,
        url,
        refresh_success,
        new_token,
        _args6 = arguments;
      return _regenerator().w(function (_context6) {
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

  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(AuthContext.Provider, {
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

/***/ }),

/***/ 649:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   NavigationContext: () => (/* binding */ NavigationContext),
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__),
/* harmony export */   useNavigation: () => (/* binding */ useNavigation)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(590);
/* harmony import */ var _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(721);
/* harmony import */ var _components_Login__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(182);
/* harmony import */ var _components_DynamicPage__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(925);
/* harmony import */ var _components_LoadingScreen__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(783);
/* harmony import */ var _components_DefaultLayout__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(196);
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }
// react/src/App.js








// Navigation context for state-based routing
var NavigationContext = /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createContext();
var useNavigation = function useNavigation() {
  var context = react__WEBPACK_IMPORTED_MODULE_0__.useContext(NavigationContext);
  if (!context) throw new Error('useNavigation must be used within NavigationProvider');
  return context;
};

// Protected app wrapper
var ProtectedApp = function ProtectedApp(_ref) {
  var children = _ref.children;
  var _useAuth = (0,_contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__.useAuth)(),
    isAuthenticated = _useAuth.isAuthenticated,
    loading = _useAuth.loading;
  if (loading) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_components_LoadingScreen__WEBPACK_IMPORTED_MODULE_5__["default"], null);
  }
  if (!isAuthenticated) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_components_Login__WEBPACK_IMPORTED_MODULE_3__["default"], null);
  }
  return children;
};

// Wire up the auth and site contexts
var ContextConnector = function ContextConnector(_ref2) {
  var children = _ref2.children;
  var _useAuth2 = (0,_contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__.useAuth)(),
    register_clear_site = _useAuth2.register_clear_site;
  var _useSite = (0,_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__.useSite)(),
    clear_context = _useSite.clear_context;
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    // Register the site clear function with auth context
    register_clear_site(clear_context);
  }, [register_clear_site, clear_context]);
  return children;
};

// Main app content - layout stays stable, only content changes
var AppContent = function AppContent() {
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)('home'),
    _useState2 = _slicedToArray(_useState, 2),
    current_view = _useState2[0],
    setCurrentView = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)({}),
    _useState4 = _slicedToArray(_useState3, 2),
    view_params = _useState4[0],
    setViewParams = _useState4[1];
  var _useSite2 = (0,_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__.useSite)(),
    initialize_context = _useSite2.initialize_context,
    fetch_site_config = _useSite2.fetch_site_config,
    current_context = _useSite2.current_context;
  var _useAuth3 = (0,_contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__.useAuth)(),
    isAuthenticated = _useAuth3.isAuthenticated;

  // Initialize context and fetch site config when authenticated
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    if (!isAuthenticated) {
      return; // Don't fetch if not authenticated
    }
    var init_app = /*#__PURE__*/function () {
      var _ref3 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
        var stored_context, initial_view;
        return _regenerator().w(function (_context) {
          while (1) switch (_context.n) {
            case 0:
              // First check for stored context
              stored_context = sessionStorage.getItem('current_context') || localStorage.getItem('default_context');
              if (stored_context) {
                console.log('Initializing with stored context:', stored_context);
                initialize_context(stored_context);
              }

              // Always fetch site config to get menu items and available contexts
              console.log('Fetching initial site config...');
              _context.n = 1;
              return fetch_site_config('/');
            case 1:
              // Check if we have an initial view from login
              initial_view = sessionStorage.getItem('initial_view');
              if (initial_view) {
                navigate_to(initial_view);
                sessionStorage.removeItem('initial_view');
              }
            case 2:
              return _context.a(2);
          }
        }, _callee);
      }));
      return function init_app() {
        return _ref3.apply(this, arguments);
      };
    }();
    init_app();
  }, [isAuthenticated]); // Re-run when authentication status changes

  // Navigation function
  var navigate_to = function navigate_to(view) {
    var params = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
    console.log('Navigating to:', view, params);
    setCurrentView(view);
    setViewParams(params);
  };

  // Make navigate_to globally available for context switching
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    window.navigate_to = navigate_to;
    return function () {
      delete window.navigate_to;
    };
  }, []);
  var navigation_value = {
    current_view: current_view,
    view_params: view_params,
    navigate_to: navigate_to
  };
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(NavigationContext.Provider, {
    value: navigation_value
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(ProtectedApp, null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_components_DefaultLayout__WEBPACK_IMPORTED_MODULE_6__["default"], null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_components_DynamicPage__WEBPACK_IMPORTED_MODULE_4__["default"], null))));
};
var App = function App() {
  // Don't change the URL - just leave it wherever it was loaded
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_contexts_AuthContext__WEBPACK_IMPORTED_MODULE_1__.AuthProvider, null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__.SiteProvider, null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(ContextConnector, null, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(AppContent, null))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (App);


/***/ }),

/***/ 721:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   SiteProvider: () => (/* binding */ SiteProvider),
/* harmony export */   useSite: () => (/* binding */ useSite)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(521);
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }
// react/src/contexts/SiteContext.js


var SiteContext = /*#__PURE__*/(0,react__WEBPACK_IMPORTED_MODULE_0__.createContext)(null);
var useSite = function useSite() {
  var context = (0,react__WEBPACK_IMPORTED_MODULE_0__.useContext)(SiteContext);
  if (!context) throw new Error('useSite must be used within SiteProvider');
  return context;
};
var SiteProvider = function SiteProvider(_ref) {
  var children = _ref.children;
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(function () {
      // Check session storage for current session's context
      return sessionStorage.getItem('current_context') || null;
    }),
    _useState2 = _slicedToArray(_useState, 2),
    current_context = _useState2[0],
    setCurrentContext = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)([]),
    _useState4 = _slicedToArray(_useState3, 2),
    available_contexts = _useState4[0],
    setAvailableContexts = _useState4[1];
  var _useState5 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState6 = _slicedToArray(_useState5, 2),
    context_loading = _useState6[0],
    setContextLoading = _useState6[1];

  // Separate state for different parts of site config
  var _useState7 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState8 = _slicedToArray(_useState7, 2),
    site_info = _useState8[0],
    setSiteInfo = _useState8[1]; // Name, logo, footer - doesn't change
  var _useState9 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)([]),
    _useState0 = _slicedToArray(_useState9, 2),
    menu_items = _useState0[0],
    setMenuItems = _useState0[1]; // Menu - changes per context

  // Track what we're currently fetching to prevent duplicate requests
  var fetching_context = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);
  var has_initial_fetch = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(false);

  // Initialize default context from login
  var initialize_context = function initialize_context(default_context) {
    console.log('SiteContext: Initializing context:', default_context);
    if (default_context) {
      setCurrentContext(default_context);
      sessionStorage.setItem('current_context', default_context);
    }
  };

  // Get the current context, with fallback to default
  var get_current_context = function get_current_context() {
    var context = current_context || sessionStorage.getItem('current_context') || localStorage.getItem('default_context') || 'default';
    console.log('SiteContext: Getting current context:', context);
    return context;
  };
  var fetch_site_config = (0,react__WEBPACK_IMPORTED_MODULE_0__.useCallback)(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
    var path,
      context,
      request_body,
      response,
      _data$menu,
      _data$menu2,
      data,
      _args = arguments,
      _t;
    return _regenerator().w(function (_context) {
      while (1) switch (_context.n) {
        case 0:
          path = _args.length > 0 && _args[0] !== undefined ? _args[0] : '/';
          context = get_current_context();
          console.log('SiteContext: Fetching config for context:', context, 'path:', path);

          // Don't fetch if we're already fetching the same context
          if (!(fetching_context.current === context && has_initial_fetch.current)) {
            _context.n = 1;
            break;
          }
          console.log('SiteContext: Already fetching this context, skipping');
          return _context.a(2);
        case 1:
          fetching_context.current = context;
          setContextLoading(true);
          _context.p = 2;
          request_body = {
            path: path,
            context: context,
            include_contexts: true
          };
          console.log('SiteContext: Making API call with body:', request_body);
          _context.n = 3;
          return _config__WEBPACK_IMPORTED_MODULE_1__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_1__["default"].getUrl('/site/config'), {
            method: 'POST',
            headers: _config__WEBPACK_IMPORTED_MODULE_1__["default"].getAuthHeaders(),
            body: JSON.stringify(request_body)
          });
        case 3:
          response = _context.v;
          if (!response.ok) {
            _context.n = 5;
            break;
          }
          _context.n = 4;
          return response.json();
        case 4:
          data = _context.v;
          console.log('SiteContext: Received site config:', data);

          // Always set site info
          setSiteInfo({
            name: data.site.name,
            logo_desktop: data.site.logo_desktop,
            logo_desktop_dark: data.site.logo_desktop_dark,
            footer_text: data.site.footer_text,
            tagline: data.site.tagline,
            maintenance_mode: data.site.maintenance_mode
          });

          // Always update menu items (they change per context)
          console.log('SiteContext: Setting menu items:', (_data$menu = data.menu) === null || _data$menu === void 0 ? void 0 : _data$menu.items);
          setMenuItems(((_data$menu2 = data.menu) === null || _data$menu2 === void 0 ? void 0 : _data$menu2.items) || []);
          if (data.contexts) {
            console.log('SiteContext: Setting available contexts:', data.contexts);
            setAvailableContexts(data.contexts);
          }

          // Update current context if server says it's different
          if (data.current_context && data.current_context !== context) {
            console.log('SiteContext: Server returned different context:', data.current_context);
            setCurrentContext(data.current_context);
            sessionStorage.setItem('current_context', data.current_context);
          }
          has_initial_fetch.current = true;
          _context.n = 6;
          break;
        case 5:
          console.error('SiteContext: Failed to fetch site config:', response.status);
        case 6:
          _context.n = 8;
          break;
        case 7:
          _context.p = 7;
          _t = _context.v;
          console.error('SiteContext: Site config fetch error:', _t);
        case 8:
          _context.p = 8;
          setContextLoading(false);
          fetching_context.current = null;
          return _context.f(8);
        case 9:
          return _context.a(2);
      }
    }, _callee, null, [[2, 7, 8, 9]]);
  })), [current_context]);

  // Context switch - fetch new menu items
  var switch_context = /*#__PURE__*/function () {
    var _ref3 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2(context_name) {
      var request_body, response, _data$menu3, _data$menu4, data, _t2;
      return _regenerator().w(function (_context2) {
        while (1) switch (_context2.n) {
          case 0:
            console.log('SiteContext: Switching context from', current_context, 'to', context_name);

            // Don't switch if it's the same context
            if (!(context_name === current_context)) {
              _context2.n = 1;
              break;
            }
            console.log('SiteContext: Same context, not switching');
            return _context2.a(2);
          case 1:
            // Update the context immediately
            setCurrentContext(context_name);
            sessionStorage.setItem('current_context', context_name);

            // Clear main content by navigating to home
            if (window.navigate_to) {
              window.navigate_to('home');
            }

            // Fetch new menu items for this context
            setContextLoading(true);
            _context2.p = 2;
            request_body = {
              path: '/',
              context: context_name,
              include_contexts: false // Don't need contexts again
            };
            console.log('SiteContext: Fetching menu for new context:', request_body);
            _context2.n = 3;
            return _config__WEBPACK_IMPORTED_MODULE_1__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_1__["default"].getUrl('/site/config'), {
              method: 'POST',
              headers: _config__WEBPACK_IMPORTED_MODULE_1__["default"].getAuthHeaders(),
              body: JSON.stringify(request_body)
            });
          case 3:
            response = _context2.v;
            if (!response.ok) {
              _context2.n = 5;
              break;
            }
            _context2.n = 4;
            return response.json();
          case 4:
            data = _context2.v;
            console.log('SiteContext: Received menu items for new context:', (_data$menu3 = data.menu) === null || _data$menu3 === void 0 ? void 0 : _data$menu3.items);

            // Update menu items
            setMenuItems(((_data$menu4 = data.menu) === null || _data$menu4 === void 0 ? void 0 : _data$menu4.items) || []);

            // If server returned different context, update it
            if (data.current_context && data.current_context !== context_name) {
              console.log('SiteContext: Server corrected context to:', data.current_context);
              setCurrentContext(data.current_context);
              sessionStorage.setItem('current_context', data.current_context);
            }
          case 5:
            _context2.n = 7;
            break;
          case 6:
            _context2.p = 6;
            _t2 = _context2.v;
            console.error('SiteContext: Context switch error:', _t2);
          case 7:
            _context2.p = 7;
            setContextLoading(false);
            return _context2.f(7);
          case 8:
            return _context2.a(2);
        }
      }, _callee2, null, [[2, 6, 7, 8]]);
    }));
    return function switch_context(_x) {
      return _ref3.apply(this, arguments);
    };
  }();

  // Clear context data on logout
  var clear_context = function clear_context() {
    console.log('SiteContext: Clearing all context data');
    setCurrentContext(null);
    setAvailableContexts([]);
    setSiteInfo(null);
    setMenuItems([]);
    sessionStorage.removeItem('current_context');
    has_initial_fetch.current = false;
  };

  // Debug log state changes
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    console.log('SiteContext state updated:', {
      current_context: current_context,
      available_contexts: available_contexts.length,
      menu_items: menu_items.length,
      site_info: !!site_info
    });
  }, [current_context, available_contexts, menu_items, site_info]);

  // Provide combined site_config for backward compatibility
  var site_config = site_info ? _objectSpread(_objectSpread({}, site_info), {}, {
    menu_items: menu_items,
    contexts: available_contexts,
    current_context: current_context
  }) : null;
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(SiteContext.Provider, {
    value: {
      current_context: current_context,
      available_contexts: available_contexts,
      context_loading: context_loading,
      site_config: site_config,
      site_info: site_info,
      menu_items: menu_items,
      setAvailableContexts: setAvailableContexts,
      setContextLoading: setContextLoading,
      initialize_context: initialize_context,
      switch_context: switch_context,
      clear_context: clear_context,
      get_current_context: get_current_context,
      fetch_site_config: fetch_site_config
    }
  }, children);
};

/***/ }),

/***/ 783:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);

var LoadingScreen = function LoadingScreen() {
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "d-flex justify-content-center align-items-center",
    style: {
      height: '100vh'
    }
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "text-center"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "spinner-border text-primary mb-3",
    role: "status"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
    className: "visually-hidden"
  }, "Loading...")), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", null, "Loading...")));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (LoadingScreen);

/***/ }),

/***/ 793:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);

var HtmlRenderer = function HtmlRenderer(_ref) {
  var html = _ref.html,
    config = _ref.config;
  var container_ref = (0,react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    if (!html || !container_ref.current) return;

    // Inject the HTML
    container_ref.current.innerHTML = html;

    // If there are any scripts in the HTML, we need to recreate them
    var scripts = container_ref.current.querySelectorAll('script');
    scripts.forEach(function (old_script) {
      var new_script = document.createElement('script');

      // Copy attributes
      Array.from(old_script.attributes).forEach(function (attr) {
        new_script.setAttribute(attr.name, attr.value);
      });

      // Copy content
      new_script.textContent = old_script.textContent;

      // Replace old script with new one
      old_script.parentNode.replaceChild(new_script, old_script);
    });

    // Apply any config-based initialization
    if (config && window.initializePage) {
      window.initializePage(config);
    }
  }, [html, config]);
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    ref: container_ref,
    className: "html-renderer"
  });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (HtmlRenderer);

/***/ }),

/***/ 884:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _App__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(649);
/* harmony import */ var _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(721);



var Breadcrumbs = function Breadcrumbs() {
  var _useNavigation = (0,_App__WEBPACK_IMPORTED_MODULE_1__.useNavigation)(),
    current_view = _useNavigation.current_view,
    navigate_to = _useNavigation.navigate_to;
  var _useSite = (0,_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_2__.useSite)(),
    site_info = _useSite.site_info,
    current_context = _useSite.current_context,
    available_contexts = _useSite.available_contexts;

  // Get current context display name
  var get_context_display_name = function get_context_display_name() {
    if (!current_context || !available_contexts || available_contexts.length === 0) {
      return 'Home';
    }
    var context = available_contexts.find(function (c) {
      return c.name === current_context;
    });
    return context ? context.display : current_context;
  };

  // Parse the current view into breadcrumb items
  var get_breadcrumb_items = function get_breadcrumb_items() {
    var items = [];

    // Always start with the context name
    items.push({
      label: get_context_display_name(),
      view: 'home',
      is_last: current_view === 'home'
    });

    // Add view segments if not on home
    if (current_view !== 'home') {
      // Convert view name to readable format (snake_case to Title Case)
      var label = current_view.split('_').map(function (word) {
        return word.charAt(0).toUpperCase() + word.slice(1);
      }).join(' ');
      items.push({
        label: label,
        view: current_view,
        is_last: true
      });
    }
    return items;
  };
  var breadcrumb_items = get_breadcrumb_items();
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "breadcrumbs"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("nav", {
    "aria-label": "breadcrumb"
  }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("ol", {
    className: "breadcrumb"
  }, breadcrumb_items.map(function (item, index) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("li", {
      key: index,
      className: "breadcrumb-item ".concat(item.is_last ? 'active' : ''),
      "aria-current": item.is_last ? 'page' : undefined
    }, item.is_last ? item.label : /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("button", {
      onClick: function onClick() {
        return navigate_to(item.view);
      },
      style: {
        background: 'none',
        border: 'none',
        color: 'var(--bs-link-color)',
        cursor: 'pointer',
        padding: 0,
        textDecoration: 'underline'
      }
    }, item.label));
  }))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (Breadcrumbs);

/***/ }),

/***/ 891:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _components_DynamicPage__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(925);
/* harmony import */ var _components_LoadingScreen__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(783);
/* harmony import */ var _components_Login__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(182);
/* harmony import */ var _components_HtmlRenderer__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(793);
/* harmony import */ var _components_ComponentBuilder__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(345);
/* harmony import */ var _components_DefaultLayout__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(196);
/* harmony import */ var _components_ServerDataTable__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(270);
// react/src/component_registry.js


// Import all default components that should be part of the main bundle
// These are the core components from your webpack ignore list








// Import any other default components you have
// Add more imports here as needed

// Initialize Components namespace
window.Components = window.Components || {};

// Register all default components
var register_default_components = function register_default_components() {
  // Register core system components
  window.Components.DynamicPage = _components_DynamicPage__WEBPACK_IMPORTED_MODULE_1__["default"];
  window.Components.LoadingScreen = _components_LoadingScreen__WEBPACK_IMPORTED_MODULE_2__["default"];
  window.Components.Login = _components_Login__WEBPACK_IMPORTED_MODULE_3__["default"];
  window.Components.HtmlRenderer = _components_HtmlRenderer__WEBPACK_IMPORTED_MODULE_4__["default"];
  window.Components.ComponentBuilder = _components_ComponentBuilder__WEBPACK_IMPORTED_MODULE_5__["default"];
  window.Components.DefaultLayout = _components_DefaultLayout__WEBPACK_IMPORTED_MODULE_6__["default"];
  window.Components.ServerDataTable = _components_ServerDataTable__WEBPACK_IMPORTED_MODULE_7__["default"];

  // Register any other default components here

  console.log('Default components registered:', Object.keys(window.Components));
};

// Export for use in index.js
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (register_default_components);

/***/ }),

/***/ 925:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(721);
/* harmony import */ var _App__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(649);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(521);
/* harmony import */ var _LoadingScreen__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(783);
/* harmony import */ var _HtmlRenderer__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(793);
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { if (r) i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n;else { var o = function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); }; o("next", 0), o("throw", 1), o("return", 2); } }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }
// react/src/components/DynamicPage.js







// Cache for loaded components
var component_cache = {};

// Ensure Components namespace exists
window.Components = window.Components || {};
var DynamicPage = function DynamicPage() {
  var _useNavigation = (0,_App__WEBPACK_IMPORTED_MODULE_2__.useNavigation)(),
    current_view = _useNavigation.current_view,
    view_params = _useNavigation.view_params;
  var _useSite = (0,_contexts_SiteContext__WEBPACK_IMPORTED_MODULE_1__.useSite)(),
    get_current_context = _useSite.get_current_context,
    current_context = _useSite.current_context;
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState2 = _slicedToArray(_useState, 2),
    page_data = _useState2[0],
    set_page_data = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true),
    _useState4 = _slicedToArray(_useState3, 2),
    loading = _useState4[0],
    set_loading = _useState4[1];
  var _useState5 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState6 = _slicedToArray(_useState5, 2),
    error = _useState6[0],
    set_error = _useState6[1];
  var _useState7 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null),
    _useState8 = _slicedToArray(_useState7, 2),
    dynamic_component = _useState8[0],
    set_dynamic_component = _useState8[1];
  (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(function () {
    load_page();
  }, [current_view, current_context]);
  var load_page = /*#__PURE__*/function () {
    var _ref = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
      var response, data, _t;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.n) {
          case 0:
            set_loading(true);
            set_error(null);
            set_dynamic_component(null);
            _context.p = 1;
            _context.n = 2;
            return _config__WEBPACK_IMPORTED_MODULE_3__["default"].apiCall(_config__WEBPACK_IMPORTED_MODULE_3__["default"].getUrl(_config__WEBPACK_IMPORTED_MODULE_3__["default"].api.endpoints.routes.resolve), {
              method: 'POST',
              headers: _config__WEBPACK_IMPORTED_MODULE_3__["default"].getAuthHeaders(),
              body: JSON.stringify({
                path: "/".concat(current_view),
                params: view_params,
                context: get_current_context()
              })
            });
          case 2:
            response = _context.v;
            if (response.ok) {
              _context.n = 4;
              break;
            }
            if (!(response.status === 404)) {
              _context.n = 3;
              break;
            }
            console.log('View not found:', current_view);
            set_error('Page not found');
            set_loading(false);
            return _context.a(2);
          case 3:
            throw new Error('Failed to load page');
          case 4:
            _context.n = 5;
            return response.json();
          case 5:
            data = _context.v;
            set_page_data(data);

            // If it's a component route, load the component bundle
            if (!(data.component_name && data.bundle_url)) {
              _context.n = 6;
              break;
            }
            _context.n = 6;
            return load_component_bundle(data.component_name, data.bundle_url, data.component_version);
          case 6:
            _context.n = 8;
            break;
          case 7:
            _context.p = 7;
            _t = _context.v;
            set_error(_t.message || 'Failed to load page');
          case 8:
            _context.p = 8;
            set_loading(false);
            return _context.f(8);
          case 9:
            return _context.a(2);
        }
      }, _callee, null, [[1, 7, 8, 9]]);
    }));
    return function load_page() {
      return _ref.apply(this, arguments);
    };
  }();
  var wait_for_component = function wait_for_component(component_name) {
    var timeout = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 5000;
    return new Promise(function (resolve, reject) {
      var start_time = Date.now();

      // Check if component is already available
      if (window.Components[component_name]) {
        resolve(window.Components[component_name]);
        return;
      }

      // Listen for component registration event
      var _handle_registration = function handle_registration(event) {
        if (event.detail.name === component_name) {
          window.removeEventListener('component_registered', _handle_registration);
          resolve(event.detail.component);
        }
      };
      window.addEventListener('component_registered', _handle_registration);

      // Also poll for component availability
      var check_interval = setInterval(function () {
        // Check multiple possible locations
        var component = window.Components[component_name] || window[component_name] || window.Components["components/".concat(component_name)];
        if (component) {
          clearInterval(check_interval);
          window.removeEventListener('component_registered', _handle_registration);

          // Ensure it's registered in the standard location
          if (!window.Components[component_name]) {
            window.Components[component_name] = component;
          }
          resolve(component);
        } else if (Date.now() - start_time > timeout) {
          clearInterval(check_interval);
          window.removeEventListener('component_registered', _handle_registration);
          reject(new Error("Component ".concat(component_name, " not found after ").concat(timeout, "ms")));
        }
      }, 50);
    });
  };
  var load_component_bundle = /*#__PURE__*/function () {
    var _ref2 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2(component_name, bundle_url, version) {
      var cache_key, loaded_component, _t2;
      return _regenerator().w(function (_context2) {
        while (1) switch (_context2.n) {
          case 0:
            cache_key = "".concat(component_name, "_").concat(version || 'latest'); // Check cache first
            if (!component_cache[cache_key]) {
              _context2.n = 1;
              break;
            }
            set_dynamic_component(function () {
              return component_cache[cache_key];
            });
            return _context2.a(2);
          case 1:
            _context2.p = 1;
            // Ensure React is available globally
            if (!window.React) {
              window.React = react__WEBPACK_IMPORTED_MODULE_0__;
              console.warn('React was not available globally, setting it now');
            }
            console.log("Loading component bundle: ".concat(component_name, " from ").concat(bundle_url));

            // Load the script
            _context2.n = 2;
            return new Promise(function (resolve, reject) {
              var script = document.createElement('script');
              script.src = bundle_url;
              script.async = true;
              script.onload = function () {
                console.log("Script loaded for ".concat(component_name));
                resolve();
              };
              script.onerror = function (e) {
                console.error("Failed to load script: ".concat(bundle_url), e);
                reject(new Error("Failed to load script: ".concat(bundle_url)));
              };
              document.head.appendChild(script);
            });
          case 2:
            // Wait for component to be registered
            console.log("Waiting for component ".concat(component_name, " to be registered..."));
            _context2.n = 3;
            return wait_for_component(component_name);
          case 3:
            loaded_component = _context2.v;
            console.log("Component ".concat(component_name, " loaded successfully"));

            // Cache it
            component_cache[cache_key] = loaded_component;
            set_dynamic_component(function () {
              return loaded_component;
            });
            _context2.n = 5;
            break;
          case 4:
            _context2.p = 4;
            _t2 = _context2.v;
            console.error("Failed to load component ".concat(component_name, ":"), _t2);
            set_error("Failed to load component: ".concat(component_name, " - ").concat(_t2.message));
          case 5:
            return _context2.a(2);
        }
      }, _callee2, null, [[1, 4]]);
    }));
    return function load_component_bundle(_x, _x2, _x3) {
      return _ref2.apply(this, arguments);
    };
  }();

  // Show loading inside the layout
  if (loading) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "d-flex justify-content-center align-items-center",
      style: {
        minHeight: '400px'
      }
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "spinner-border text-primary",
      role: "status"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
      className: "visually-hidden"
    }, "Loading...")));
  }

  // Show error
  if (error) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "container mt-4"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
      className: "alert alert-danger"
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("h4", {
      className: "alert-heading"
    }, "Error"), /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("p", null, error)));
  }

  // Render dynamic component
  if (dynamic_component && page_data) {
    // Create component element with proper casing
    var DynamicComponentElement = dynamic_component;

    // Merge route params with configured props
    var component_props = _objectSpread(_objectSpread({}, page_data.props), {}, {
      route_params: view_params,
      route_config: page_data.config || {},
      meta: {
        title: page_data.title,
        description: page_data.description
      }
    });
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(react__WEBPACK_IMPORTED_MODULE_0__.Suspense, {
      fallback: /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
        className: "d-flex justify-content-center align-items-center",
        style: {
          minHeight: '400px'
        }
      }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
        className: "spinner-border text-primary",
        role: "status"
      }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("span", {
        className: "visually-hidden"
      }, "Loading...")))
    }, /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(DynamicComponentElement, component_props));
  }

  // Render HTML template
  if (page_data !== null && page_data !== void 0 && page_data.html) {
    return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_HtmlRenderer__WEBPACK_IMPORTED_MODULE_5__["default"], {
      html: page_data.html,
      config: page_data.config
    });
  }

  // Default: show warning
  return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement("div", {
    className: "alert alert-warning m-3"
  }, "Unknown page type");
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (DynamicPage);

/***/ }),

/***/ 954:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(540);
/* harmony import */ var react_dom_client__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(338);
/* harmony import */ var _App__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(649);
/* harmony import */ var _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(721);
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(521);
/* harmony import */ var _component_registry__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(891);






window.React = react__WEBPACK_IMPORTED_MODULE_0__;
window.ReactDOM = react_dom_client__WEBPACK_IMPORTED_MODULE_1__;

// Make contexts and hooks available for dynamic components
window.NavigationContext = _App__WEBPACK_IMPORTED_MODULE_2__.NavigationContext;
window.useNavigation = _App__WEBPACK_IMPORTED_MODULE_2__.useNavigation;
window.SiteContext = _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_3__.SiteContext;
window.useSite = _contexts_SiteContext__WEBPACK_IMPORTED_MODULE_3__.useSite;
window.config = _config__WEBPACK_IMPORTED_MODULE_4__["default"];

// Ensure they're available on the global object too
if (typeof __webpack_require__.g !== 'undefined') {
  __webpack_require__.g.React = react__WEBPACK_IMPORTED_MODULE_0__;
  __webpack_require__.g.ReactDOM = react_dom_client__WEBPACK_IMPORTED_MODULE_1__;
}

// Initialize Components namespace
window.Components = window.Components || {};

// Register all default components
(0,_component_registry__WEBPACK_IMPORTED_MODULE_5__["default"])();

// Debug helper
window.list_components = function () {
  console.log('Available components:', Object.keys(window.Components));
  return window.Components;
};

// Wait for any existing app initialization if needed
var init_react = function init_react() {
  var root = react_dom_client__WEBPACK_IMPORTED_MODULE_1__.createRoot(document.getElementById('root'));
  root.render(/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0__.createElement(_App__WEBPACK_IMPORTED_MODULE_2__["default"], null));
};
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init_react);
} else {
  init_react();
}

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
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
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = __webpack_modules__;
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/chunk loaded */
/******/ 	(() => {
/******/ 		var deferred = [];
/******/ 		__webpack_require__.O = (result, chunkIds, fn, priority) => {
/******/ 			if(chunkIds) {
/******/ 				priority = priority || 0;
/******/ 				for(var i = deferred.length; i > 0 && deferred[i - 1][2] > priority; i--) deferred[i] = deferred[i - 1];
/******/ 				deferred[i] = [chunkIds, fn, priority];
/******/ 				return;
/******/ 			}
/******/ 			var notFulfilled = Infinity;
/******/ 			for (var i = 0; i < deferred.length; i++) {
/******/ 				var [chunkIds, fn, priority] = deferred[i];
/******/ 				var fulfilled = true;
/******/ 				for (var j = 0; j < chunkIds.length; j++) {
/******/ 					if ((priority & 1 === 0 || notFulfilled >= priority) && Object.keys(__webpack_require__.O).every((key) => (__webpack_require__.O[key](chunkIds[j])))) {
/******/ 						chunkIds.splice(j--, 1);
/******/ 					} else {
/******/ 						fulfilled = false;
/******/ 						if(priority < notFulfilled) notFulfilled = priority;
/******/ 					}
/******/ 				}
/******/ 				if(fulfilled) {
/******/ 					deferred.splice(i--, 1)
/******/ 					var r = fn();
/******/ 					if (r !== undefined) result = r;
/******/ 				}
/******/ 			}
/******/ 			return result;
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
/******/ 	/* webpack/runtime/global */
/******/ 	(() => {
/******/ 		__webpack_require__.g = (function() {
/******/ 			if (typeof globalThis === 'object') return globalThis;
/******/ 			try {
/******/ 				return this || new Function('return this')();
/******/ 			} catch (e) {
/******/ 				if (typeof window === 'object') return window;
/******/ 			}
/******/ 		})();
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
/******/ 	/* webpack/runtime/jsonp chunk loading */
/******/ 	(() => {
/******/ 		// no baseURI
/******/ 		
/******/ 		// object to store loaded and loading chunks
/******/ 		// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 		// [resolve, reject, Promise] = chunk loading, 0 = chunk loaded
/******/ 		var installedChunks = {
/******/ 			792: 0
/******/ 		};
/******/ 		
/******/ 		// no chunk on demand loading
/******/ 		
/******/ 		// no prefetching
/******/ 		
/******/ 		// no preloaded
/******/ 		
/******/ 		// no HMR
/******/ 		
/******/ 		// no HMR manifest
/******/ 		
/******/ 		__webpack_require__.O.j = (chunkId) => (installedChunks[chunkId] === 0);
/******/ 		
/******/ 		// install a JSONP callback for chunk loading
/******/ 		var webpackJsonpCallback = (parentChunkLoadingFunction, data) => {
/******/ 			var [chunkIds, moreModules, runtime] = data;
/******/ 			// add "moreModules" to the modules object,
/******/ 			// then flag all "chunkIds" as loaded and fire callback
/******/ 			var moduleId, chunkId, i = 0;
/******/ 			if(chunkIds.some((id) => (installedChunks[id] !== 0))) {
/******/ 				for(moduleId in moreModules) {
/******/ 					if(__webpack_require__.o(moreModules, moduleId)) {
/******/ 						__webpack_require__.m[moduleId] = moreModules[moduleId];
/******/ 					}
/******/ 				}
/******/ 				if(runtime) var result = runtime(__webpack_require__);
/******/ 			}
/******/ 			if(parentChunkLoadingFunction) parentChunkLoadingFunction(data);
/******/ 			for(;i < chunkIds.length; i++) {
/******/ 				chunkId = chunkIds[i];
/******/ 				if(__webpack_require__.o(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 					installedChunks[chunkId][0]();
/******/ 				}
/******/ 				installedChunks[chunkId] = 0;
/******/ 			}
/******/ 			return __webpack_require__.O(result);
/******/ 		}
/******/ 		
/******/ 		var chunkLoadingGlobal = self["webpackChunkreact_app"] = self["webpackChunkreact_app"] || [];
/******/ 		chunkLoadingGlobal.forEach(webpackJsonpCallback.bind(null, 0));
/******/ 		chunkLoadingGlobal.push = webpackJsonpCallback.bind(null, chunkLoadingGlobal.push.bind(chunkLoadingGlobal));
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module depends on other loaded chunks and execution need to be delayed
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, [121], () => (__webpack_require__(954)))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;
//# sourceMappingURL=main.bundle.js.map