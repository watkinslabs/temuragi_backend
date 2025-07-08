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
  "default": () => (/* binding */ user_components_SalesOrderDetail)
});

;// external "React"
const external_React_namespaceObject = window["React"];
var external_React_default = /*#__PURE__*/__webpack_require__.n(external_React_namespaceObject);
;// ./node_modules/lucide-react/dist/esm/shared/src/utils.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */

const toKebabCase = (string) => string.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const toCamelCase = (string) => string.replace(
  /^([A-Z])|[\s-_]+(\w)/g,
  (match, p1, p2) => p2 ? p2.toUpperCase() : p1.toLowerCase()
);
const toPascalCase = (string) => {
  const camelCase = toCamelCase(string);
  return camelCase.charAt(0).toUpperCase() + camelCase.slice(1);
};
const mergeClasses = (...classes) => classes.filter((className, index, array) => {
  return Boolean(className) && className.trim() !== "" && array.indexOf(className) === index;
}).join(" ").trim();
const hasA11yProp = (props) => {
  for (const prop in props) {
    if (prop.startsWith("aria-") || prop === "role" || prop === "title") {
      return true;
    }
  }
};


//# sourceMappingURL=utils.js.map

;// ./node_modules/lucide-react/dist/esm/defaultAttributes.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */

var defaultAttributes = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round"
};


//# sourceMappingURL=defaultAttributes.js.map

;// ./node_modules/lucide-react/dist/esm/Icon.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */





const Icon = (0,external_React_namespaceObject.forwardRef)(
  ({
    color = "currentColor",
    size = 24,
    strokeWidth = 2,
    absoluteStrokeWidth,
    className = "",
    children,
    iconNode,
    ...rest
  }, ref) => (0,external_React_namespaceObject.createElement)(
    "svg",
    {
      ref,
      ...defaultAttributes,
      width: size,
      height: size,
      stroke: color,
      strokeWidth: absoluteStrokeWidth ? Number(strokeWidth) * 24 / Number(size) : strokeWidth,
      className: mergeClasses("lucide", className),
      ...!children && !hasA11yProp(rest) && { "aria-hidden": "true" },
      ...rest
    },
    [
      ...iconNode.map(([tag, attrs]) => (0,external_React_namespaceObject.createElement)(tag, attrs)),
      ...Array.isArray(children) ? children : [children]
    ]
  )
);


//# sourceMappingURL=Icon.js.map

;// ./node_modules/lucide-react/dist/esm/createLucideIcon.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */





const createLucideIcon = (iconName, iconNode) => {
  const Component = (0,external_React_namespaceObject.forwardRef)(
    ({ className, ...props }, ref) => (0,external_React_namespaceObject.createElement)(Icon, {
      ref,
      iconNode,
      className: mergeClasses(
        `lucide-${toKebabCase(toPascalCase(iconName))}`,
        `lucide-${iconName}`,
        className
      ),
      ...props
    })
  );
  Component.displayName = toPascalCase(iconName);
  return Component;
};


//# sourceMappingURL=createLucideIcon.js.map

;// ./node_modules/lucide-react/dist/esm/icons/file-text.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const __iconNode = [
  ["path", { d: "M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z", key: "1rqfz7" }],
  ["path", { d: "M14 2v4a2 2 0 0 0 2 2h4", key: "tnqrlb" }],
  ["path", { d: "M10 9H8", key: "b1mrlr" }],
  ["path", { d: "M16 13H8", key: "t4e002" }],
  ["path", { d: "M16 17H8", key: "z1uh3a" }]
];
const FileText = createLucideIcon("file-text", __iconNode);


//# sourceMappingURL=file-text.js.map

;// ./node_modules/lucide-react/dist/esm/icons/pen.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const pen_iconNode = [
  [
    "path",
    {
      d: "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z",
      key: "1a8usu"
    }
  ]
];
const Pen = createLucideIcon("pen", pen_iconNode);


//# sourceMappingURL=pen.js.map

;// ./node_modules/lucide-react/dist/esm/icons/plus.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const plus_iconNode = [
  ["path", { d: "M5 12h14", key: "1ays0h" }],
  ["path", { d: "M12 5v14", key: "s699le" }]
];
const Plus = createLucideIcon("plus", plus_iconNode);


//# sourceMappingURL=plus.js.map

;// ./node_modules/lucide-react/dist/esm/icons/circle-alert.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const circle_alert_iconNode = [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["line", { x1: "12", x2: "12", y1: "8", y2: "12", key: "1pkeuh" }],
  ["line", { x1: "12", x2: "12.01", y1: "16", y2: "16", key: "4dfq90" }]
];
const CircleAlert = createLucideIcon("circle-alert", circle_alert_iconNode);


//# sourceMappingURL=circle-alert.js.map

;// ./node_modules/lucide-react/dist/esm/icons/check.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const check_iconNode = [["path", { d: "M20 6 9 17l-5-5", key: "1gmf2c" }]];
const Check = createLucideIcon("check", check_iconNode);


//# sourceMappingURL=check.js.map

;// ./node_modules/lucide-react/dist/esm/icons/credit-card.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const credit_card_iconNode = [
  ["rect", { width: "20", height: "14", x: "2", y: "5", rx: "2", key: "ynyp8z" }],
  ["line", { x1: "2", x2: "22", y1: "10", y2: "10", key: "1b3vmo" }]
];
const CreditCard = createLucideIcon("credit-card", credit_card_iconNode);


//# sourceMappingURL=credit-card.js.map

;// ./node_modules/lucide-react/dist/esm/icons/user.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const user_iconNode = [
  ["path", { d: "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2", key: "975kel" }],
  ["circle", { cx: "12", cy: "7", r: "4", key: "17ys0d" }]
];
const User = createLucideIcon("user", user_iconNode);


//# sourceMappingURL=user.js.map

;// ./node_modules/lucide-react/dist/esm/icons/package.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const package_iconNode = [
  [
    "path",
    {
      d: "M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z",
      key: "1a0edw"
    }
  ],
  ["path", { d: "M12 22V12", key: "d0xqtd" }],
  ["polyline", { points: "3.29 7 12 12 20.71 7", key: "ousv84" }],
  ["path", { d: "m7.5 4.27 9 5.15", key: "1c824w" }]
];
const Package = createLucideIcon("package", package_iconNode);


//# sourceMappingURL=package.js.map

;// ./node_modules/lucide-react/dist/esm/icons/truck.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const truck_iconNode = [
  ["path", { d: "M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2", key: "wrbu53" }],
  ["path", { d: "M15 18H9", key: "1lyqi6" }],
  [
    "path",
    {
      d: "M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14",
      key: "lysw3i"
    }
  ],
  ["circle", { cx: "17", cy: "18", r: "2", key: "332jqn" }],
  ["circle", { cx: "7", cy: "18", r: "2", key: "19iecd" }]
];
const Truck = createLucideIcon("truck", truck_iconNode);


//# sourceMappingURL=truck.js.map

;// ./node_modules/lucide-react/dist/esm/icons/message-square.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const message_square_iconNode = [
  ["path", { d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z", key: "1lielz" }]
];
const MessageSquare = createLucideIcon("message-square", message_square_iconNode);


//# sourceMappingURL=message-square.js.map

;// ./node_modules/lucide-react/dist/esm/icons/save.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const save_iconNode = [
  [
    "path",
    {
      d: "M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z",
      key: "1c8476"
    }
  ],
  ["path", { d: "M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7", key: "1ydtos" }],
  ["path", { d: "M7 3v4a1 1 0 0 0 1 1h7", key: "t51u73" }]
];
const Save = createLucideIcon("save", save_iconNode);


//# sourceMappingURL=save.js.map

;// ./node_modules/lucide-react/dist/esm/icons/x.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const x_iconNode = [
  ["path", { d: "M18 6 6 18", key: "1bl5f8" }],
  ["path", { d: "m6 6 12 12", key: "d8bk6v" }]
];
const X = createLucideIcon("x", x_iconNode);


//# sourceMappingURL=x.js.map

;// ./node_modules/lucide-react/dist/esm/icons/arrow-left.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const arrow_left_iconNode = [
  ["path", { d: "m12 19-7-7 7-7", key: "1l729n" }],
  ["path", { d: "M19 12H5", key: "x3x0zl" }]
];
const ArrowLeft = createLucideIcon("arrow-left", arrow_left_iconNode);


//# sourceMappingURL=arrow-left.js.map

;// ./node_modules/lucide-react/dist/esm/icons/copy.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const copy_iconNode = [
  ["rect", { width: "14", height: "14", x: "8", y: "8", rx: "2", ry: "2", key: "17jyea" }],
  ["path", { d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2", key: "zix9uf" }]
];
const Copy = createLucideIcon("copy", copy_iconNode);


//# sourceMappingURL=copy.js.map

;// ./node_modules/lucide-react/dist/esm/icons/trash-2.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const trash_2_iconNode = [
  ["path", { d: "M3 6h18", key: "d0wm0j" }],
  ["path", { d: "M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6", key: "4alrt4" }],
  ["path", { d: "M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2", key: "v07s0e" }],
  ["line", { x1: "10", x2: "10", y1: "11", y2: "17", key: "1uufr5" }],
  ["line", { x1: "14", x2: "14", y1: "11", y2: "17", key: "xtxkd" }]
];
const Trash2 = createLucideIcon("trash-2", trash_2_iconNode);


//# sourceMappingURL=trash-2.js.map

;// ./src/user_components/SalesOrderDetail.js
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _iterableToArray(r) { if ("undefined" != typeof Symbol && null != r[Symbol.iterator] || null != r["@@iterator"]) return Array.from(r); }
function _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }
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
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
/**
 * @routes ["SalesOrderDetail"]
 */




// Main Sales Order Component
var SalesOrderDetail = function SalesOrderDetail() {
  // Get config from props or window
  var config = window.config || {};

  // Get navigation hook at the top level
  var navigation = window.useNavigation ? window.useNavigation() : null;
  var view_params = (navigation === null || navigation === void 0 ? void 0 : navigation.view_params) || {};

  // Merge config with view_params
  var merged_config = _objectSpread(_objectSpread(_objectSpread({}, config), view_params), {}, {
    company: config.company || 'PACIFIC',
    data_api: config.data_api || '/v2/api/data'
  });

  // Determine mode
  var is_view_mode = merged_config.mode === 'view';
  var is_edit_mode = merged_config.mode === 'edit';
  var so_number_param = merged_config.so_number || null;
  var is_new_so = !so_number_param || so_number_param === 'NEW';

  // Core state
  var _useState = (0,external_React_namespaceObject.useState)(false),
    _useState2 = _slicedToArray(_useState, 2),
    loading = _useState2[0],
    setLoading = _useState2[1];
  var _useState3 = (0,external_React_namespaceObject.useState)(''),
    _useState4 = _slicedToArray(_useState3, 2),
    loadingMessage = _useState4[0],
    setLoadingMessage = _useState4[1];
  var _useState5 = (0,external_React_namespaceObject.useState)(is_view_mode ? 'view' : is_edit_mode ? 'edit' : 'create'),
    _useState6 = _slicedToArray(_useState5, 2),
    mode = _useState6[0],
    setMode = _useState6[1];
  var _useState7 = (0,external_React_namespaceObject.useState)(null),
    _useState8 = _slicedToArray(_useState7, 2),
    toast = _useState8[0],
    setToast = _useState8[1];

  // SO Data state
  var _useState9 = (0,external_React_namespaceObject.useState)(is_new_so ? null : so_number_param),
    _useState0 = _slicedToArray(_useState9, 2),
    soNumber = _useState0[0],
    setSoNumber = _useState0[1];
  var _useState1 = (0,external_React_namespaceObject.useState)(null),
    _useState10 = _slicedToArray(_useState1, 2),
    customer = _useState10[0],
    setCustomer = _useState10[1];
  var _useState11 = (0,external_React_namespaceObject.useState)(get_default_header(merged_config)),
    _useState12 = _slicedToArray(_useState11, 2),
    header = _useState12[0],
    setHeader = _useState12[1];
  var _useState13 = (0,external_React_namespaceObject.useState)([]),
    _useState14 = _slicedToArray(_useState13, 2),
    lines = _useState14[0],
    setLines = _useState14[1];
  var _useState15 = (0,external_React_namespaceObject.useState)('PENDING'),
    _useState16 = _slicedToArray(_useState15, 2),
    status = _useState16[0],
    setStatus = _useState16[1];

  // API configuration
  var api_call = /*#__PURE__*/function () {
    var _ref = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee(operation, model) {
      var _window$app;
      var params,
        request_data,
        _config$getAuthHeader,
        response,
        _args = arguments,
        _t;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.n) {
          case 0:
            params = _args.length > 2 && _args[2] !== undefined ? _args[2] : {};
            request_data = _objectSpread({
              operation: operation,
              model: model,
              company: merged_config.company
            }, params);
            if (!((_window$app = window.app) !== null && _window$app !== void 0 && (_window$app = _window$app.api) !== null && _window$app !== void 0 && _window$app.post)) {
              _context.n = 2;
              break;
            }
            _context.n = 1;
            return window.app.api.post(merged_config.data_api, request_data);
          case 1:
            return _context.a(2, _context.v);
          case 2:
            _context.p = 2;
            _context.n = 3;
            return fetch(merged_config.data_api, {
              method: 'POST',
              headers: _objectSpread({
                'Content-Type': 'application/json'
              }, (_config$getAuthHeader = config.getAuthHeaders) === null || _config$getAuthHeader === void 0 ? void 0 : _config$getAuthHeader.call(config)),
              body: JSON.stringify(request_data)
            });
          case 3:
            response = _context.v;
            if (response.ok) {
              _context.n = 4;
              break;
            }
            throw new Error("HTTP error! status: ".concat(response.status));
          case 4:
            _context.n = 5;
            return response.json();
          case 5:
            return _context.a(2, _context.v);
          case 6:
            _context.p = 6;
            _t = _context.v;
            console.error('API call failed:', _t);
            return _context.a(2, {
              success: false,
              error: _t.message
            });
          case 7:
            return _context.a(2);
        }
      }, _callee, null, [[2, 6]]);
    }));
    return function api_call(_x, _x2) {
      return _ref.apply(this, arguments);
    };
  }();

  // Initialize component
  (0,external_React_namespaceObject.useEffect)(function () {
    var init = /*#__PURE__*/function () {
      var _ref2 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2() {
        return _regenerator().w(function (_context2) {
          while (1) switch (_context2.n) {
            case 0:
              if (is_new_so) {
                _context2.n = 1;
                break;
              }
              _context2.n = 1;
              return load_existing_so();
            case 1:
              return _context2.a(2);
          }
        }, _callee2);
      }));
      return function init() {
        return _ref2.apply(this, arguments);
      };
    }();
    init();
  }, []);

  // Load existing SO
  var load_existing_so = /*#__PURE__*/function () {
    var _ref3 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee3() {
      var result, _result$header, _result$header2, _t2;
      return _regenerator().w(function (_context3) {
        while (1) switch (_context3.n) {
          case 0:
            if (soNumber) {
              _context3.n = 1;
              break;
            }
            return _context3.a(2);
          case 1:
            setLoading(true);
            setLoadingMessage('Loading sales order...');
            _context3.p = 2;
            _context3.n = 3;
            return api_call('get', 'SalesOrder', {
              so_number: soNumber,
              company: merged_config.company
            });
          case 3:
            result = _context3.v;
            if (!result.success) {
              _context3.n = 5;
              break;
            }
            // Map the data
            setHeader(map_header_data(result.header || {}));
            setLines(result.lines || []);
            setStatus(((_result$header = result.header) === null || _result$header === void 0 ? void 0 : _result$header.status) || 'PENDING');

            // Load customer info if we have customer code
            if (!((_result$header2 = result.header) !== null && _result$header2 !== void 0 && _result$header2.customer_code)) {
              _context3.n = 4;
              break;
            }
            _context3.n = 4;
            return load_customer_details(result.header.customer_code);
          case 4:
            _context3.n = 6;
            break;
          case 5:
            show_error('Failed to load sales order: ' + (result.error || 'Unknown error'));
          case 6:
            _context3.n = 8;
            break;
          case 7:
            _context3.p = 7;
            _t2 = _context3.v;
            console.error('Error loading SO:', _t2);
            show_error('Failed to load sales order');
          case 8:
            _context3.p = 8;
            setLoading(false);
            return _context3.f(8);
          case 9:
            return _context3.a(2);
        }
      }, _callee3, null, [[2, 7, 8, 9]]);
    }));
    return function load_existing_so() {
      return _ref3.apply(this, arguments);
    };
  }();

  // Customer handling
  var load_customer_details = /*#__PURE__*/function () {
    var _ref4 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee4(customer_code) {
      var model, result, _t3;
      return _regenerator().w(function (_context4) {
        while (1) switch (_context4.n) {
          case 0:
            if (customer_code) {
              _context4.n = 1;
              break;
            }
            return _context4.a(2);
          case 1:
            _context4.p = 1;
            model = customer_code >= 7000000 ? 'GCANADA_dbo_BKARCUST' : 'GPACIFIC_dbo_BKARCUST';
            _context4.n = 2;
            return api_call('list', model, {
              filters: {
                code: {
                  operator: "eq",
                  value: customer_code
                }
              },
              start: 0,
              length: 1
            });
          case 2:
            result = _context4.v;
            if (!(result.success && result.data && result.data.length > 0)) {
              _context4.n = 3;
              break;
            }
            setCustomer(result.data[0]);
            return _context4.a(2, result.data[0]);
          case 3:
            _context4.n = 5;
            break;
          case 4:
            _context4.p = 4;
            _t3 = _context4.v;
            console.error('Error loading customer details:', _t3);
          case 5:
            return _context4.a(2, null);
        }
      }, _callee4, null, [[1, 4]]);
    }));
    return function load_customer_details(_x3) {
      return _ref4.apply(this, arguments);
    };
  }();

  // Save SO
  var save_so = /*#__PURE__*/function () {
    var _ref5 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee5() {
      var save_data, result, _t4;
      return _regenerator().w(function (_context5) {
        while (1) switch (_context5.n) {
          case 0:
            if (validate_so()) {
              _context5.n = 1;
              break;
            }
            return _context5.a(2);
          case 1:
            setLoading(true);
            setLoadingMessage('Saving sales order...');
            _context5.p = 2;
            save_data = {
              customer_id: header.customer_code,
              location: header.location,
              admin_id: header.admin_id || 1,
              // Would need to get actual admin ID
              shipping: {
                address: header.shipping,
                attention: header.shipping.attention,
                via_id: header.ship_via_id || 0
              },
              billing: {
                address: header.billing
              },
              payment: {
                terms: header.terms,
                cod: header.cod || 'N'
              },
              lines: lines.filter(function (line) {
                return line.type !== 'X';
              }).map(function (line) {
                return {
                  part: line.part,
                  quantity: line.quantity,
                  price: line.price,
                  list_price: line.list_price || 0,
                  discount: line.discount || 0,
                  vendor: line.vendor || '',
                  freight: line.freight || 0,
                  taxable: line.taxable ? 'Y' : 'N'
                };
              }),
              notes: lines.filter(function (line) {
                return line.type === 'X';
              }).map(function (line) {
                return line.message;
              }),
              custom_po: header.custom_po || '',
              taxable: header.taxable ? 'Y' : 'N',
              freight: header.freight || 0
            };
            _context5.n = 3;
            return api_call('create', 'SalesOrder', save_data);
          case 3:
            result = _context5.v;
            if (!result.success) {
              _context5.n = 5;
              break;
            }
            show_toast('Sales order saved successfully!', 'success');
            setSoNumber(result.so_number);
            setMode('view');

            // Reload to get the saved data
            _context5.n = 4;
            return load_existing_so();
          case 4:
            _context5.n = 6;
            break;
          case 5:
            show_toast(result.error || 'Failed to save sales order', 'error');
          case 6:
            _context5.n = 8;
            break;
          case 7:
            _context5.p = 7;
            _t4 = _context5.v;
            console.error('Error saving SO:', _t4);
            show_toast('Failed to save sales order', 'error');
          case 8:
            _context5.p = 8;
            setLoading(false);
            return _context5.f(8);
          case 9:
            return _context5.a(2);
        }
      }, _callee5, null, [[2, 7, 8, 9]]);
    }));
    return function save_so() {
      return _ref5.apply(this, arguments);
    };
  }();

  // Validation
  var validate_so = function validate_so() {
    var errors = [];
    if (!header.customer_code) {
      errors.push('Please select a customer');
    }
    if (lines.filter(function (l) {
      return l.type !== 'X';
    }).length === 0) {
      errors.push('At least one line item is required');
    }
    if (errors.length > 0) {
      show_error('Please fix the following errors:\n' + errors.join('\n'));
      return false;
    }
    return true;
  };

  // Utility functions
  var show_error = function show_error(message) {
    show_toast(message, 'error');
  };
  var show_toast = function show_toast(message) {
    var type = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'info';
    setToast({
      message: message,
      type: type
    });
    setTimeout(function () {
      return setToast(null);
    }, 5000);
  };

  // Calculations
  var totals = (0,external_React_namespaceObject.useMemo)(function () {
    var subtotal = 0;
    var total_freight = 0;
    lines.forEach(function (line) {
      if (line.type !== 'X') {
        subtotal += line.extended || 0;
        total_freight += (line.freight || 0) * (line.quantity || 0);
      }
    });
    var order_freight = parseFloat(header.freight || 0);
    var tax_amount = parseFloat(header.tax_amount || 0);
    var total = subtotal + tax_amount + order_freight + total_freight;
    return {
      subtotal: subtotal,
      order_freight: order_freight,
      total_freight: total_freight,
      tax_amount: tax_amount,
      total: total
    };
  }, [lines, header.freight, header.tax_amount]);

  // Mode badge component
  var ModeBadge = function ModeBadge() {
    var badge_config = {
      view: {
        color: 'secondary',
        text: 'VIEW ONLY',
        icon: FileText
      },
      edit: {
        color: 'warning',
        text: 'EDIT MODE',
        icon: Pen
      },
      create: {
        color: 'success',
        text: 'NEW ORDER',
        icon: Plus
      }
    };
    var config = badge_config[mode];
    var Icon = config.icon;
    return /*#__PURE__*/external_React_default().createElement("span", {
      className: "badge bg-".concat(config.color, " d-inline-flex align-items-center")
    }, /*#__PURE__*/external_React_default().createElement(Icon, {
      size: 14,
      className: "me-1"
    }), config.text);
  };

  // Status badge component
  var StatusBadge = function StatusBadge(_ref6) {
    var status = _ref6.status;
    var status_config = {
      PENDING: {
        color: 'warning',
        icon: CircleAlert
      },
      INVOICED: {
        color: 'success',
        icon: Check
      },
      CREDIT: {
        color: 'danger',
        icon: CreditCard
      }
    };
    var config = status_config[status] || {
      color: 'secondary',
      icon: FileText
    };
    var Icon = config.icon;
    return /*#__PURE__*/external_React_default().createElement("span", {
      className: "badge bg-".concat(config.color, " d-inline-flex align-items-center ms-2")
    }, /*#__PURE__*/external_React_default().createElement(Icon, {
      size: 14,
      className: "me-1"
    }), status);
  };
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "container-fluid mt-2"
  }, loading && /*#__PURE__*/external_React_default().createElement("div", {
    className: "position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center",
    style: {
      background: 'rgba(0,0,0,0.5)',
      zIndex: 9999
    }
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "text-center text-white"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "spinner-border text-light mb-2",
    role: "status"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "visually-hidden"
  }, "Loading...")), /*#__PURE__*/external_React_default().createElement("div", null, loadingMessage || 'Loading...'))), toast && /*#__PURE__*/external_React_default().createElement("div", {
    className: "position-fixed top-0 start-50 translate-middle-x mt-3 alert alert-".concat(toast.type === 'error' ? 'danger' : toast.type, " alert-dismissible"),
    style: {
      zIndex: 10000,
      minWidth: '300px'
    }
  }, toast.message, /*#__PURE__*/external_React_default().createElement("button", {
    type: "button",
    className: "btn-close",
    onClick: function onClick() {
      return setToast(null);
    }
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between align-items-center mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("h4", {
    className: "mb-0 me-3"
  }, "Sales Order", soNumber && /*#__PURE__*/external_React_default().createElement("span", {
    className: "ms-2"
  }, "#", soNumber)), /*#__PURE__*/external_React_default().createElement(ModeBadge, null), soNumber && /*#__PURE__*/external_React_default().createElement(StatusBadge, {
    status: status
  })), mode === 'view' && !is_view_mode && /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-primary btn-sm",
    onClick: function onClick() {
      return setMode('edit');
    }
  }, /*#__PURE__*/external_React_default().createElement(Pen, {
    size: 16,
    className: "me-1"
  }), "Edit Order"))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2 mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card h-100"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header py-2"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0 d-flex align-items-center"
  }, /*#__PURE__*/external_React_default().createElement(User, {
    size: 16,
    className: "me-2"
  }), "Customer Information")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body p-2"
  }, /*#__PURE__*/external_React_default().createElement(CustomerSection, {
    customer: customer,
    customer_code: header.customer_code,
    onCustomerChange: function onCustomerChange(cust) {
      setCustomer(cust);
      setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          customer_code: (cust === null || cust === void 0 ? void 0 : cust.code) || '',
          billing: {
            name: (cust === null || cust === void 0 ? void 0 : cust.name) || '',
            address1: (cust === null || cust === void 0 ? void 0 : cust.add1) || '',
            address2: (cust === null || cust === void 0 ? void 0 : cust.add2) || '',
            city: (cust === null || cust === void 0 ? void 0 : cust.city) || '',
            state: (cust === null || cust === void 0 ? void 0 : cust.state) || '',
            zip: (cust === null || cust === void 0 ? void 0 : cust.zip_) || '',
            country: (cust === null || cust === void 0 ? void 0 : cust.country) || 'USA'
          }
        });
      });
    },
    api_call: api_call,
    readonly: mode === 'view'
  }), customer && /*#__PURE__*/external_React_default().createElement("div", {
    className: "mt-2 pt-2 border-top"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2 small"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "text-muted"
  }, "Terms:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "ms-1"
  }, customer.terms_num || 'N/A')), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "text-muted"
  }, "Sales Person:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "ms-1"
  }, customer.slsp_num || 'N/A')), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "text-muted"
  }, "Credit Limit:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "ms-1"
  }, "$", customer.creditlmt || 0)), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "text-muted"
  }, "Available:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "ms-1"
  }, "$", customer.remaincrd || 0))))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card h-100"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header py-2"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0 d-flex align-items-center"
  }, /*#__PURE__*/external_React_default().createElement(Package, {
    size: 16,
    className: "me-2"
  }), "Order Details")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body p-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Order Date"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "date",
    className: "form-control form-control-sm",
    value: header.order_date,
    readOnly: true
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Ship Date"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "date",
    className: "form-control form-control-sm",
    value: header.ship_date || '',
    onChange: function onChange(e) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          ship_date: e.target.value
        });
      });
    },
    readOnly: mode === 'view'
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Location"), /*#__PURE__*/external_React_default().createElement(LocationSelect, {
    value: header.location,
    onChange: function onChange(value) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          location: value
        });
      });
    },
    api_call: api_call,
    company: merged_config.company,
    disabled: mode === 'view',
    size: "sm"
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Customer PO"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: header.custom_po || '',
    onChange: function onChange(e) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          custom_po: e.target.value
        });
      });
    },
    readOnly: mode === 'view',
    placeholder: "Customer PO#"
  })))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-4"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card h-100"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header py-2"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0 d-flex align-items-center"
  }, /*#__PURE__*/external_React_default().createElement(Truck, {
    size: 16,
    className: "me-2"
  }), "Shipping & Payment")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body p-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Ship Via"), /*#__PURE__*/external_React_default().createElement(ShipViaSelect, {
    value: header.ship_via,
    onChange: function onChange(value, id) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          ship_via: value,
          ship_via_id: id
        });
      });
    },
    api_call: api_call,
    disabled: mode === 'view',
    size: "sm"
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Terms"), /*#__PURE__*/external_React_default().createElement(TermsSelect, {
    value: header.terms,
    onChange: function onChange(value) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          terms: value
        });
      });
    },
    api_call: api_call,
    disabled: mode === 'view',
    size: "sm"
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Freight"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: header.freight || 0,
    onChange: function onChange(e) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          freight: parseFloat(e.target.value) || 0
        });
      });
    },
    readOnly: mode === 'view',
    step: "0.01",
    min: "0"
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Taxable"), /*#__PURE__*/external_React_default().createElement("div", {
    className: "form-check form-switch mt-1"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    className: "form-check-input",
    type: "checkbox",
    checked: header.taxable,
    onChange: function onChange(e) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          taxable: e.target.checked
        });
      });
    },
    disabled: mode === 'view'
  }), /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-check-label small"
  }, header.taxable ? 'Yes' : 'No')))))))), /*#__PURE__*/external_React_default().createElement(AddressSection, {
    billing: header.billing,
    shipping: header.shipping,
    onBillingChange: function onBillingChange(billing) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          billing: billing
        });
      });
    },
    onShippingChange: function onShippingChange(shipping) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          shipping: shipping
        });
      });
    },
    readonly: mode === 'view',
    collapsed: mode === 'view'
  }), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header py-2 d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0"
  }, "Line Items"), mode !== 'view' && /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-primary btn-sm me-2",
    onClick: function onClick() {
      return add_line();
    }
  }, /*#__PURE__*/external_React_default().createElement(Plus, {
    size: 16,
    className: "me-1"
  }), "Add Line"), /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-secondary btn-sm",
    onClick: function onClick() {
      return add_note_line();
    }
  }, /*#__PURE__*/external_React_default().createElement(MessageSquare, {
    size: 16,
    className: "me-1"
  }), "Add Note"))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body p-0"
  }, /*#__PURE__*/external_React_default().createElement(LineItemsTable, {
    lines: lines,
    onUpdate: update_line,
    onRemove: remove_line,
    api_call: api_call,
    readonly: mode === 'view'
  }))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-4 offset-md-8"
  }, /*#__PURE__*/external_React_default().createElement(TotalsCard, {
    totals: totals
  }))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "mb-4"
  }, mode === 'create' && /*#__PURE__*/external_React_default().createElement((external_React_default()).Fragment, null, /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-success me-2",
    onClick: save_so,
    disabled: loading
  }, /*#__PURE__*/external_React_default().createElement(Save, {
    size: 16,
    className: "me-1"
  }), "Create Order"), /*#__PURE__*/external_React_default().createElement(CancelButton, {
    navigation: navigation
  })), mode === 'edit' && /*#__PURE__*/external_React_default().createElement((external_React_default()).Fragment, null, /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-success me-2",
    onClick: save_so,
    disabled: loading
  }, /*#__PURE__*/external_React_default().createElement(Save, {
    size: 16,
    className: "me-1"
  }), "Save Changes"), /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-secondary me-2",
    onClick: function onClick() {
      setMode('view');
      load_existing_so(); // Reload to discard changes
    }
  }, /*#__PURE__*/external_React_default().createElement(X, {
    size: 16,
    className: "me-1"
  }), "Cancel")), mode === 'view' && /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-secondary",
    onClick: function onClick() {
      if (navigation) {
        navigation.navigate_to('SalesOrders');
      }
    }
  }, /*#__PURE__*/external_React_default().createElement(ArrowLeft, {
    size: 16,
    className: "me-1"
  }), "Back to Orders")));

  // Component methods
  function add_line() {
    var new_line = {
      type: 'R',
      part: '',
      description: '',
      quantity: 1,
      price: 0,
      list_price: 0,
      discount: 0,
      extended: 0,
      freight: 0,
      taxable: false,
      message: ''
    };
    setLines(function (prev) {
      return [].concat(_toConsumableArray(prev), [new_line]);
    });
  }
  function add_note_line() {
    var new_note = {
      type: 'X',
      message: '',
      part: '',
      description: '',
      quantity: 0,
      price: 0,
      extended: 0
    };
    setLines(function (prev) {
      return [].concat(_toConsumableArray(prev), [new_note]);
    });
  }
  function remove_line(index) {
    if (confirm('Remove this line?')) {
      setLines(function (prev) {
        return prev.filter(function (_, i) {
          return i !== index;
        });
      });
    }
  }
  function update_line(index, field, value) {
    setLines(function (prev) {
      var updated = _toConsumableArray(prev);
      var line = _objectSpread({}, updated[index]);
      line[field] = value;

      // Recalculate extended if needed
      if (line.type !== 'X' && ['quantity', 'price', 'discount'].includes(field)) {
        var qty = parseFloat(line.quantity || 0);
        var price = parseFloat(line.price || 0);
        var discount = parseFloat(line.discount || 0);
        line.extended = qty * (price - discount);
      }
      updated[index] = line;
      return updated;
    });
  }
};

// Sub-components

var CustomerSection = function CustomerSection(_ref7) {
  var customer = _ref7.customer,
    customer_code = _ref7.customer_code,
    onCustomerChange = _ref7.onCustomerChange,
    api_call = _ref7.api_call,
    readonly = _ref7.readonly;
  var _useState17 = (0,external_React_namespaceObject.useState)(''),
    _useState18 = _slicedToArray(_useState17, 2),
    searchTerm = _useState18[0],
    setSearchTerm = _useState18[1];
  var _useState19 = (0,external_React_namespaceObject.useState)([]),
    _useState20 = _slicedToArray(_useState19, 2),
    suggestions = _useState20[0],
    setSuggestions = _useState20[1];
  var _useState21 = (0,external_React_namespaceObject.useState)(false),
    _useState22 = _slicedToArray(_useState21, 2),
    loading = _useState22[0],
    setLoading = _useState22[1];
  var _useState23 = (0,external_React_namespaceObject.useState)(false),
    _useState24 = _slicedToArray(_useState23, 2),
    showDropdown = _useState24[0],
    setShowDropdown = _useState24[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    if (customer) {
      setSearchTerm("".concat(customer.code, " - ").concat(customer.name));
    }
  }, [customer]);
  var search_customers = /*#__PURE__*/function () {
    var _ref8 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee6(term) {
      var model, result, _t5;
      return _regenerator().w(function (_context6) {
        while (1) switch (_context6.n) {
          case 0:
            if (!(term.length < 2)) {
              _context6.n = 1;
              break;
            }
            setSuggestions([]);
            return _context6.a(2);
          case 1:
            setLoading(true);
            _context6.p = 2;
            // Determine which table to search based on term
            model = term >= '7000000' ? 'GCANADA_dbo_BKARCUST' : 'GPACIFIC_dbo_BKARCUST';
            _context6.n = 3;
            return api_call('list', model, {
              filters: {
                name: {
                  operator: "ilike",
                  value: "%".concat(term, "%")
                },
                active: {
                  operator: "eq",
                  value: "Y"
                }
              },
              start: 0,
              length: 10
            });
          case 3:
            result = _context6.v;
            if (result.success && result.data) {
              setSuggestions(result.data);
            }
            _context6.n = 5;
            break;
          case 4:
            _context6.p = 4;
            _t5 = _context6.v;
            console.error('Error searching customers:', _t5);
            setSuggestions([]);
          case 5:
            setLoading(false);
          case 6:
            return _context6.a(2);
        }
      }, _callee6, null, [[2, 4]]);
    }));
    return function search_customers(_x4) {
      return _ref8.apply(this, arguments);
    };
  }();
  (0,external_React_namespaceObject.useEffect)(function () {
    var timer = setTimeout(function () {
      if (searchTerm && !customer) {
        search_customers(searchTerm);
      }
    }, 300);
    return function () {
      return clearTimeout(timer);
    };
  }, [searchTerm, customer]);
  if (readonly && customer) {
    return /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("div", {
      className: "fw-bold"
    }, customer.name), /*#__PURE__*/external_React_default().createElement("div", {
      className: "text-muted small"
    }, "Customer #", customer.code), customer.contact && /*#__PURE__*/external_React_default().createElement("div", {
      className: "text-muted small"
    }, "Contact: ", customer.contact), customer.telephone && /*#__PURE__*/external_React_default().createElement("div", {
      className: "text-muted small"
    }, "Phone: ", customer.telephone));
  }
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "position-relative"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: searchTerm,
    onChange: function onChange(e) {
      setSearchTerm(e.target.value);
      setShowDropdown(true);
      if (!e.target.value) {
        onCustomerChange(null);
      }
    },
    onFocus: function onFocus() {
      return setShowDropdown(true);
    },
    onBlur: function onBlur() {
      return setTimeout(function () {
        return setShowDropdown(false);
      }, 200);
    },
    placeholder: "Search customer by code or name...",
    disabled: readonly
  }), showDropdown && (suggestions.length > 0 || loading) && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-menu d-block position-absolute mt-1 w-100",
    style: {
      maxHeight: '200px',
      overflowY: 'auto',
      zIndex: 1050
    }
  }, loading && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-item-text text-center"
  }, /*#__PURE__*/external_React_default().createElement("small", {
    className: "text-muted"
  }, "Loading...")), !loading && suggestions.map(function (cust) {
    return /*#__PURE__*/external_React_default().createElement("button", {
      key: cust.code,
      className: "dropdown-item text-truncate",
      type: "button",
      onClick: function onClick() {
        onCustomerChange(cust);
        setSearchTerm("".concat(cust.code, " - ").concat(cust.name));
        setShowDropdown(false);
      }
    }, /*#__PURE__*/external_React_default().createElement("strong", null, cust.code), " - ", cust.name, cust.city && /*#__PURE__*/external_React_default().createElement("small", {
      className: "text-muted d-block"
    }, cust.city, ", ", cust.state));
  })));
};
var AddressSection = function AddressSection(_ref9) {
  var billing = _ref9.billing,
    shipping = _ref9.shipping,
    onBillingChange = _ref9.onBillingChange,
    onShippingChange = _ref9.onShippingChange,
    readonly = _ref9.readonly,
    collapsed = _ref9.collapsed;
  var _useState25 = (0,external_React_namespaceObject.useState)(collapsed),
    _useState26 = _slicedToArray(_useState25, 2),
    isCollapsed = _useState26[0],
    setIsCollapsed = _useState26[1];
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "card mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header py-2"
  }, /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-link btn-sm text-decoration-none w-100 text-start p-0",
    onClick: function onClick() {
      return setIsCollapsed(!isCollapsed);
    },
    type: "button"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0"
  }, isCollapsed ? '▶' : '▼', " Billing & Shipping Addresses"))), !isCollapsed && /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-6"
  }, /*#__PURE__*/external_React_default().createElement(AddressCard, {
    title: "Billing Address",
    address: billing,
    onChange: onBillingChange,
    readonly: readonly,
    compact: true
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-6"
  }, /*#__PURE__*/external_React_default().createElement(AddressCard, {
    title: "Shipping Address",
    address: shipping,
    onChange: onShippingChange,
    showCopyButton: true,
    onCopy: function onCopy() {
      return onShippingChange(_objectSpread(_objectSpread({}, billing), {}, {
        attention: shipping.attention
      }));
    },
    readonly: readonly,
    compact: true
  })))));
};
var AddressCard = function AddressCard(_ref0) {
  var title = _ref0.title,
    address = _ref0.address,
    _onChange = _ref0.onChange,
    readonly = _ref0.readonly,
    showCopyButton = _ref0.showCopyButton,
    onCopy = _ref0.onCopy,
    compact = _ref0.compact;
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: compact ? "" : "card h-100"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: compact ? "d-flex justify-content-between align-items-center mb-2" : "card-header py-2 d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0 small"
  }, title), showCopyButton && !readonly && /*#__PURE__*/external_React_default().createElement("button", {
    type: "button",
    className: "btn btn-sm btn-link p-0",
    onClick: onCopy
  }, /*#__PURE__*/external_React_default().createElement(Copy, {
    size: 14
  }))), /*#__PURE__*/external_React_default().createElement("div", {
    className: compact ? "" : "card-body p-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-1"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.name || '',
    onChange: function onChange(e) {
      return _onChange(_objectSpread(_objectSpread({}, address), {}, {
        name: e.target.value
      }));
    },
    placeholder: "Name",
    readOnly: readonly
  })), title === "Shipping Address" && /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.attention || '',
    onChange: function onChange(e) {
      return _onChange(_objectSpread(_objectSpread({}, address), {}, {
        attention: e.target.value
      }));
    },
    placeholder: "Attention",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.address1 || '',
    onChange: function onChange(e) {
      return _onChange(_objectSpread(_objectSpread({}, address), {}, {
        address1: e.target.value
      }));
    },
    placeholder: "Address 1",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.address2 || '',
    onChange: function onChange(e) {
      return _onChange(_objectSpread(_objectSpread({}, address), {}, {
        address2: e.target.value
      }));
    },
    placeholder: "Address 2",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-5"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.city || '',
    onChange: function onChange(e) {
      return _onChange(_objectSpread(_objectSpread({}, address), {}, {
        city: e.target.value
      }));
    },
    placeholder: "City",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-2"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.state || '',
    onChange: function onChange(e) {
      return _onChange(_objectSpread(_objectSpread({}, address), {}, {
        state: e.target.value.toUpperCase()
      }));
    },
    placeholder: "ST",
    maxLength: "2",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-5"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.zip || '',
    onChange: function onChange(e) {
      return _onChange(_objectSpread(_objectSpread({}, address), {}, {
        zip: e.target.value
      }));
    },
    placeholder: "ZIP",
    readOnly: readonly
  })))));
};
var LineItemsTable = function LineItemsTable(_ref1) {
  var lines = _ref1.lines,
    onUpdate = _ref1.onUpdate,
    onRemove = _ref1.onRemove,
    api_call = _ref1.api_call,
    readonly = _ref1.readonly;
  if (lines.length === 0) {
    return /*#__PURE__*/external_React_default().createElement("div", {
      className: "text-center text-muted p-4"
    }, "No line items. Click \"Add Line\" to start.");
  }
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "table-responsive"
  }, /*#__PURE__*/external_React_default().createElement("table", {
    className: "table table-sm table-hover mb-0"
  }, /*#__PURE__*/external_React_default().createElement("thead", {
    className: "table-light"
  }, /*#__PURE__*/external_React_default().createElement("tr", null, /*#__PURE__*/external_React_default().createElement("th", {
    width: "40"
  }, "#"), /*#__PURE__*/external_React_default().createElement("th", {
    width: "120"
  }, "Part"), /*#__PURE__*/external_React_default().createElement("th", null, "Description"), /*#__PURE__*/external_React_default().createElement("th", {
    width: "80"
  }, "Qty"), /*#__PURE__*/external_React_default().createElement("th", {
    width: "100"
  }, "Price"), /*#__PURE__*/external_React_default().createElement("th", {
    width: "100"
  }, "Discount"), /*#__PURE__*/external_React_default().createElement("th", {
    width: "100"
  }, "Extended"), !readonly && /*#__PURE__*/external_React_default().createElement("th", {
    width: "50"
  }))), /*#__PURE__*/external_React_default().createElement("tbody", null, lines.map(function (line, index) {
    return /*#__PURE__*/external_React_default().createElement(LineItemRow, {
      key: index,
      line: line,
      index: index,
      onUpdate: onUpdate,
      onRemove: onRemove,
      api_call: api_call,
      readonly: readonly
    });
  }))));
};
var LineItemRow = function LineItemRow(_ref10) {
  var line = _ref10.line,
    index = _ref10.index,
    onUpdate = _ref10.onUpdate,
    onRemove = _ref10.onRemove,
    api_call = _ref10.api_call,
    readonly = _ref10.readonly;
  var is_note = line.type === 'X';
  if (is_note) {
    return /*#__PURE__*/external_React_default().createElement("tr", null, /*#__PURE__*/external_React_default().createElement("td", null, index + 1), /*#__PURE__*/external_React_default().createElement("td", {
      colSpan: readonly ? 6 : 5
    }, /*#__PURE__*/external_React_default().createElement("div", {
      className: "d-flex align-items-center"
    }, /*#__PURE__*/external_React_default().createElement("span", {
      className: "badge bg-info me-2"
    }, "NOTE"), readonly ? /*#__PURE__*/external_React_default().createElement("span", null, line.message) : /*#__PURE__*/external_React_default().createElement("input", {
      type: "text",
      className: "form-control form-control-sm flex-grow-1",
      value: line.message || '',
      onChange: function onChange(e) {
        return onUpdate(index, 'message', e.target.value);
      },
      placeholder: "Note text...",
      maxLength: "75"
    }))), !readonly && /*#__PURE__*/external_React_default().createElement("td", {
      className: "text-center"
    }, /*#__PURE__*/external_React_default().createElement("button", {
      className: "btn btn-sm btn-link text-danger p-0",
      onClick: function onClick() {
        return onRemove(index);
      }
    }, /*#__PURE__*/external_React_default().createElement(Trash2, {
      size: 16
    }))));
  }
  return /*#__PURE__*/external_React_default().createElement("tr", null, /*#__PURE__*/external_React_default().createElement("td", null, index + 1), /*#__PURE__*/external_React_default().createElement("td", null, readonly ? /*#__PURE__*/external_React_default().createElement("span", null, line.part) : /*#__PURE__*/external_React_default().createElement(PartInput, {
    value: line.part,
    onChange: function onChange(value) {
      return onUpdate(index, 'part', value);
    },
    onPartSelect: (/*#__PURE__*/function () {
      var _ref11 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee7(part) {
        return _regenerator().w(function (_context7) {
          while (1) switch (_context7.n) {
            case 0:
              onUpdate(index, 'part', part.part);
              onUpdate(index, 'description', part.inventory_description);

              // Could fetch pricing here
            case 1:
              return _context7.a(2);
          }
        }, _callee7);
      }));
      return function (_x5) {
        return _ref11.apply(this, arguments);
      };
    }()),
    api_call: api_call
  })), /*#__PURE__*/external_React_default().createElement("td", null, readonly ? /*#__PURE__*/external_React_default().createElement("span", null, line.description) : /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: line.description || '',
    onChange: function onChange(e) {
      return onUpdate(index, 'description', e.target.value);
    },
    placeholder: "Description"
  })), /*#__PURE__*/external_React_default().createElement("td", null, readonly ? /*#__PURE__*/external_React_default().createElement("span", null, line.quantity) : /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: line.quantity,
    onChange: function onChange(e) {
      return onUpdate(index, 'quantity', parseFloat(e.target.value) || 0);
    },
    min: "0",
    step: "1"
  })), /*#__PURE__*/external_React_default().createElement("td", null, readonly ? /*#__PURE__*/external_React_default().createElement("span", null, "$", (line.price || 0).toFixed(2)) : /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: line.price,
    onChange: function onChange(e) {
      return onUpdate(index, 'price', parseFloat(e.target.value) || 0);
    },
    min: "0",
    step: "0.01"
  })), /*#__PURE__*/external_React_default().createElement("td", null, readonly ? /*#__PURE__*/external_React_default().createElement("span", null, "$", (line.discount || 0).toFixed(2)) : /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: line.discount,
    onChange: function onChange(e) {
      return onUpdate(index, 'discount', parseFloat(e.target.value) || 0);
    },
    min: "0",
    step: "0.01"
  })), /*#__PURE__*/external_React_default().createElement("td", {
    className: "text-end"
  }, /*#__PURE__*/external_React_default().createElement("strong", null, "$", (line.extended || 0).toFixed(2))), !readonly && /*#__PURE__*/external_React_default().createElement("td", {
    className: "text-center"
  }, /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-sm btn-link text-danger p-0",
    onClick: function onClick() {
      return onRemove(index);
    }
  }, /*#__PURE__*/external_React_default().createElement(Trash2, {
    size: 16
  }))));
};
var PartInput = function PartInput(_ref12) {
  var value = _ref12.value,
    _onChange2 = _ref12.onChange,
    onPartSelect = _ref12.onPartSelect,
    api_call = _ref12.api_call;
  var _useState27 = (0,external_React_namespaceObject.useState)(value || ''),
    _useState28 = _slicedToArray(_useState27, 2),
    searchTerm = _useState28[0],
    setSearchTerm = _useState28[1];
  var _useState29 = (0,external_React_namespaceObject.useState)([]),
    _useState30 = _slicedToArray(_useState29, 2),
    suggestions = _useState30[0],
    setSuggestions = _useState30[1];
  var _useState31 = (0,external_React_namespaceObject.useState)(false),
    _useState32 = _slicedToArray(_useState31, 2),
    showDropdown = _useState32[0],
    setShowDropdown = _useState32[1];
  var _useState33 = (0,external_React_namespaceObject.useState)(false),
    _useState34 = _slicedToArray(_useState33, 2),
    loading = _useState34[0],
    setLoading = _useState34[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    setSearchTerm(value || '');
  }, [value]);
  var search_parts = /*#__PURE__*/function () {
    var _ref13 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee8(term) {
      var result, _t6;
      return _regenerator().w(function (_context8) {
        while (1) switch (_context8.n) {
          case 0:
            if (!(term.length < 2)) {
              _context8.n = 1;
              break;
            }
            setSuggestions([]);
            return _context8.a(2);
          case 1:
            setLoading(true);
            _context8.p = 2;
            _context8.n = 3;
            return api_call('list', 'JADVDATA_dbo_part_meta', {
              return_columns: ["part", "inventory_description"],
              filters: {
                part: {
                  operator: "ilike",
                  value: "".concat(term, "%")
                }
              },
              start: 0,
              length: 10
            });
          case 3:
            result = _context8.v;
            if (result.success && result.data) {
              setSuggestions(result.data);
            }
            _context8.n = 5;
            break;
          case 4:
            _context8.p = 4;
            _t6 = _context8.v;
            console.error('Error searching parts:', _t6);
            setSuggestions([]);
          case 5:
            setLoading(false);
          case 6:
            return _context8.a(2);
        }
      }, _callee8, null, [[2, 4]]);
    }));
    return function search_parts(_x6) {
      return _ref13.apply(this, arguments);
    };
  }();
  (0,external_React_namespaceObject.useEffect)(function () {
    var timer = setTimeout(function () {
      if (searchTerm && searchTerm !== value) {
        search_parts(searchTerm);
      }
    }, 300);
    return function () {
      return clearTimeout(timer);
    };
  }, [searchTerm]);
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "position-relative"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: searchTerm,
    onChange: function onChange(e) {
      setSearchTerm(e.target.value);
      _onChange2(e.target.value);
      setShowDropdown(true);
    },
    onFocus: function onFocus() {
      return setShowDropdown(true);
    },
    onBlur: function onBlur() {
      return setTimeout(function () {
        return setShowDropdown(false);
      }, 200);
    },
    placeholder: "Part #"
  }), showDropdown && (suggestions.length > 0 || loading) && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-menu d-block position-absolute mt-1",
    style: {
      maxHeight: '200px',
      overflowY: 'auto',
      minWidth: '300px',
      zIndex: 1050
    }
  }, loading && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-item-text text-center"
  }, /*#__PURE__*/external_React_default().createElement("small", {
    className: "text-muted"
  }, "Searching...")), !loading && suggestions.map(function (part) {
    return /*#__PURE__*/external_React_default().createElement("button", {
      key: part.part,
      className: "dropdown-item",
      type: "button",
      onClick: function onClick() {
        onPartSelect(part);
        setShowDropdown(false);
      }
    }, /*#__PURE__*/external_React_default().createElement("strong", null, part.part), part.inventory_description && /*#__PURE__*/external_React_default().createElement("small", {
      className: "text-muted ms-2"
    }, part.inventory_description));
  })));
};
var TotalsCard = function TotalsCard(_ref14) {
  var totals = _ref14.totals;
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "card"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body p-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between mb-1"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "small"
  }, "Subtotal:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "small"
  }, "$", totals.subtotal.toFixed(2))), totals.total_freight > 0 && /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between mb-1"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "small"
  }, "Part Freight:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "small"
  }, "$", totals.total_freight.toFixed(2))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between mb-1"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "small"
  }, "Order Freight:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "small"
  }, "$", totals.order_freight.toFixed(2))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between mb-1"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "small"
  }, "Tax:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "small"
  }, "$", totals.tax_amount.toFixed(2))), /*#__PURE__*/external_React_default().createElement("hr", {
    className: "my-2"
  }), /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between"
  }, /*#__PURE__*/external_React_default().createElement("span", null, "Total:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "h5 mb-0"
  }, "$", totals.total.toFixed(2)))));
};
var LocationSelect = function LocationSelect(_ref15) {
  var value = _ref15.value,
    _onChange3 = _ref15.onChange,
    api_call = _ref15.api_call,
    company = _ref15.company,
    disabled = _ref15.disabled,
    _ref15$size = _ref15.size,
    size = _ref15$size === void 0 ? "md" : _ref15$size;
  var _useState35 = (0,external_React_namespaceObject.useState)([]),
    _useState36 = _slicedToArray(_useState35, 2),
    locations = _useState36[0],
    setLocations = _useState36[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    var load_locations = /*#__PURE__*/function () {
      var _ref16 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee9() {
        var result;
        return _regenerator().w(function (_context9) {
          while (1) switch (_context9.n) {
            case 0:
              _context9.n = 1;
              return api_call('list', 'JADVDATA_dbo_locations', {
                filters: {
                  company: {
                    operator: "eq",
                    value: company
                  },
                  active: {
                    operator: "eq",
                    value: "1"
                  }
                },
                start: 0,
                length: 50
              });
            case 1:
              result = _context9.v;
              if (result.success && result.data) {
                setLocations(result.data);
              }
            case 2:
              return _context9.a(2);
          }
        }, _callee9);
      }));
      return function load_locations() {
        return _ref16.apply(this, arguments);
      };
    }();
    load_locations();
  }, [company]);
  return /*#__PURE__*/external_React_default().createElement("select", {
    className: "form-select form-select-".concat(size),
    value: value || '',
    onChange: function onChange(e) {
      return _onChange3(e.target.value);
    },
    disabled: disabled
  }, /*#__PURE__*/external_React_default().createElement("option", {
    value: ""
  }, "Select..."), locations.map(function (loc) {
    return /*#__PURE__*/external_React_default().createElement("option", {
      key: loc.location,
      value: loc.location
    }, loc.location, " - ", loc.location_name);
  }));
};
var ShipViaSelect = function ShipViaSelect(_ref17) {
  var value = _ref17.value,
    _onChange4 = _ref17.onChange,
    api_call = _ref17.api_call,
    disabled = _ref17.disabled,
    _ref17$size = _ref17.size,
    size = _ref17$size === void 0 ? "md" : _ref17$size;
  var _useState37 = (0,external_React_namespaceObject.useState)([]),
    _useState38 = _slicedToArray(_useState37, 2),
    options = _useState38[0],
    setOptions = _useState38[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    var load_options = /*#__PURE__*/function () {
      var _ref18 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee0() {
        var model, result;
        return _regenerator().w(function (_context0) {
          while (1) switch (_context0.n) {
            case 0:
              model = 'GPACIFIC_dbo_BKSHPVIA'; // Would need to handle CANADA too
              _context0.n = 1;
              return api_call('list', model, {
                start: 0,
                length: 50
              });
            case 1:
              result = _context0.v;
              if (result.success && result.data) {
                setOptions(result.data);
              }
            case 2:
              return _context0.a(2);
          }
        }, _callee0);
      }));
      return function load_options() {
        return _ref18.apply(this, arguments);
      };
    }();
    load_options();
  }, []);
  return /*#__PURE__*/external_React_default().createElement("select", {
    className: "form-select form-select-".concat(size),
    value: value || '',
    onChange: function onChange(e) {
      var selected = options.find(function (o) {
        return o.text === e.target.value;
      });
      _onChange4(e.target.value, (selected === null || selected === void 0 ? void 0 : selected.num) || 0);
    },
    disabled: disabled
  }, /*#__PURE__*/external_React_default().createElement("option", {
    value: ""
  }, "Select..."), options.map(function (opt) {
    return /*#__PURE__*/external_React_default().createElement("option", {
      key: opt.num,
      value: opt.text
    }, opt.text);
  }));
};
var TermsSelect = function TermsSelect(_ref19) {
  var value = _ref19.value,
    _onChange5 = _ref19.onChange,
    api_call = _ref19.api_call,
    disabled = _ref19.disabled,
    _ref19$size = _ref19.size,
    size = _ref19$size === void 0 ? "md" : _ref19$size;
  var _useState39 = (0,external_React_namespaceObject.useState)([]),
    _useState40 = _slicedToArray(_useState39, 2),
    terms = _useState40[0],
    setTerms = _useState40[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    var load_terms = /*#__PURE__*/function () {
      var _ref20 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee1() {
        var result;
        return _regenerator().w(function (_context1) {
          while (1) switch (_context1.n) {
            case 0:
              _context1.n = 1;
              return api_call('list', 'GPACIFIC_dbo_BKSYTERM', {
                start: 0,
                length: 50
              });
            case 1:
              result = _context1.v;
              if (result.success && result.data) {
                setTerms(result.data);
              }
            case 2:
              return _context1.a(2);
          }
        }, _callee1);
      }));
      return function load_terms() {
        return _ref20.apply(this, arguments);
      };
    }();
    load_terms();
  }, []);
  return /*#__PURE__*/external_React_default().createElement("select", {
    className: "form-select form-select-".concat(size),
    value: value || '',
    onChange: function onChange(e) {
      return _onChange5(e.target.value);
    },
    disabled: disabled
  }, /*#__PURE__*/external_React_default().createElement("option", {
    value: ""
  }, "Select..."), terms.map(function (term) {
    return /*#__PURE__*/external_React_default().createElement("option", {
      key: term.num,
      value: term.num
    }, term.desc);
  }));
};
var CancelButton = function CancelButton(_ref21) {
  var navigation = _ref21.navigation;
  return /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-secondary",
    onClick: function onClick() {
      if (navigation) {
        navigation.navigate_to('SalesOrders');
      }
    }
  }, /*#__PURE__*/external_React_default().createElement(X, {
    size: 16,
    className: "me-1"
  }), "Cancel");
};

// Helper functions
function get_default_header(config) {
  var today = new Date().toISOString().split('T')[0];
  return {
    customer_code: '',
    order_date: today,
    invoice_date: today,
    ship_date: '',
    location: config.location || 'TAC',
    entered_by: '',
    sales_person: '',
    custom_po: '',
    terms: '',
    ship_via: '',
    ship_via_id: 0,
    freight: 0,
    tax_amount: 0,
    taxable: false,
    tax_rate: 0,
    tax_key: '',
    admin_id: null,
    cod: 'N',
    billing: {
      name: '',
      address1: '',
      address2: '',
      city: '',
      state: '',
      zip: '',
      country: 'USA'
    },
    shipping: {
      name: '',
      attention: '',
      address1: '',
      address2: '',
      city: '',
      state: '',
      zip: '',
      country: 'USA'
    }
  };
}
function map_header_data(header) {
  var _header$shipping, _header$shipping2, _header$payment;
  return {
    customer_code: header.customer_code || '',
    order_date: format_date(header.order_date),
    invoice_date: format_date(header.invoice_date),
    ship_date: format_date(header.ship_date),
    location: header.location || 'TAC',
    entered_by: header.entered_by || '',
    sales_person: header.sales_person || '',
    custom_po: header.custom_po || '',
    terms: header.terms || '',
    ship_via: ((_header$shipping = header.shipping) === null || _header$shipping === void 0 ? void 0 : _header$shipping.via) || '',
    ship_via_id: ((_header$shipping2 = header.shipping) === null || _header$shipping2 === void 0 ? void 0 : _header$shipping2.via_id) || 0,
    freight: parseFloat(header.freight || 0),
    tax_amount: parseFloat(header.tax_amount || 0),
    taxable: header.taxable === 'Y',
    tax_rate: parseFloat(header.tax_rate || 0),
    tax_key: header.tax_key || '',
    cod: ((_header$payment = header.payment) === null || _header$payment === void 0 ? void 0 : _header$payment.cod) || 'N',
    billing: header.billing || get_default_header().billing,
    shipping: header.shipping || get_default_header().shipping
  };
}
function format_date(date) {
  if (!date) return '';
  if (typeof date === 'string') return date.split('T')[0];
  return '';
}
/* harmony default export */ const user_components_SalesOrderDetail = (SalesOrderDetail);
window["components/SalesOrderDetail"] = __webpack_exports__["default"];
/******/ })()
;
//# sourceMappingURL=SalesOrderDetail.bundle.js.map