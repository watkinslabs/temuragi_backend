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
  "default": () => (/* binding */ user_components_PurchaseOrder)
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

;// ./node_modules/lucide-react/dist/esm/icons/plus.js
/**
 * @license lucide-react v0.525.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */



const __iconNode = [
  ["path", { d: "M5 12h14", key: "1ays0h" }],
  ["path", { d: "M12 5v14", key: "s699le" }]
];
const Plus = createLucideIcon("plus", __iconNode);


//# sourceMappingURL=plus.js.map

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

;// ./src/user_components/PurchaseOrder.js
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
 * @routes ["PurchaseOrder"]
*/




// Main Purchase Order Builder Component
var PurchaseOrder = function PurchaseOrder() {
  // Get config from props or window
  var config = window.config || {};

  // Get navigation hook at the top level
  var navigation = window.useNavigation ? window.useNavigation() : null;
  var view_params = (navigation === null || navigation === void 0 ? void 0 : navigation.view_params) || {};

  // Merge config with view_params for flexibility
  var merged_config = _objectSpread(_objectSpread(_objectSpread({}, config), view_params), {}, {
    company: config.company || 'PACIFIC',
    data_api: config.data_api || '/v2/api/data'
  });
  var is_view_mode = merged_config.mode === 'view';

  // Core state
  var _useState = (0,external_React_namespaceObject.useState)(false),
    _useState2 = _slicedToArray(_useState, 2),
    loading = _useState2[0],
    setLoading = _useState2[1];
  var _useState3 = (0,external_React_namespaceObject.useState)(''),
    _useState4 = _slicedToArray(_useState3, 2),
    loadingMessage = _useState4[0],
    setLoadingMessage = _useState4[1];
  var _useState5 = (0,external_React_namespaceObject.useState)(null),
    _useState6 = _slicedToArray(_useState5, 2),
    availableVendors = _useState6[0],
    setAvailableVendors = _useState6[1];

  // Determine if we're in edit mode based on po_number
  var po_number_param = merged_config.po_number || null;
  var is_new_po = !po_number_param || po_number_param === 'NEW';
  var _useState7 = (0,external_React_namespaceObject.useState)(is_new_po ? null : po_number_param),
    _useState8 = _slicedToArray(_useState7, 2),
    poNumber = _useState8[0],
    setPoNumber = _useState8[1];
  var _useState9 = (0,external_React_namespaceObject.useState)(!is_new_po || is_view_mode),
    _useState0 = _slicedToArray(_useState9, 2),
    isSaved = _useState0[0],
    setIsSaved = _useState0[1];

  // Compute isEditMode based on current state
  var isEditMode = (!is_new_po || poNumber && isSaved) && !is_view_mode;
  var _useState1 = (0,external_React_namespaceObject.useState)(null),
    _useState10 = _slicedToArray(_useState1, 2),
    toast = _useState10[0],
    setToast = _useState10[1];

  // PO Data state
  var _useState11 = (0,external_React_namespaceObject.useState)(null),
    _useState12 = _slicedToArray(_useState11, 2),
    vendor = _useState12[0],
    setVendor = _useState12[1];
  var _useState13 = (0,external_React_namespaceObject.useState)(get_default_header(merged_config)),
    _useState14 = _slicedToArray(_useState13, 2),
    header = _useState14[0],
    setHeader = _useState14[1];
  var _useState15 = (0,external_React_namespaceObject.useState)([]),
    _useState16 = _slicedToArray(_useState15, 2),
    lines = _useState16[0],
    setLines = _useState16[1];
  var _useState17 = (0,external_React_namespaceObject.useState)([]),
    _useState18 = _slicedToArray(_useState17, 2),
    deletedLineIds = _useState18[0],
    setDeletedLineIds = _useState18[1];

  // UI State
  var _useState19 = (0,external_React_namespaceObject.useState)({
      show: false,
      comments1: '',
      comments2: ''
    }),
    _useState20 = _slicedToArray(_useState19, 2),
    vendorComments = _useState20[0],
    setVendorComments = _useState20[1];

  // Virtual inventory state (part -> inventory data)
  var _useState21 = (0,external_React_namespaceObject.useState)({}),
    _useState22 = _slicedToArray(_useState21, 2),
    virtualInventory = _useState22[0],
    setVirtualInventory = _useState22[1];
  var _useState23 = (0,external_React_namespaceObject.useState)({}),
    _useState24 = _slicedToArray(_useState23, 2),
    inventoryLoading = _useState24[0],
    setInventoryLoading = _useState24[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    console.log('=== PO STATE DEBUG ===', {
      po_number_param: po_number_param,
      is_new_po: is_new_po,
      poNumber: poNumber,
      isSaved: isSaved,
      isEditMode: isEditMode,
      loading: loading,
      has_po_number: !!poNumber,
      button_conditions: {
        show_save: !isSaved,
        show_receive_invoice: isSaved && poNumber,
        actual_condition: !!poNumber
      }
    });
  }, [po_number_param, is_new_po, poNumber, isSaved, isEditMode, loading]);

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
            }, params); // Use existing API manager if available, otherwise use fetch
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
        var prefill_result, prefill_data, pre_pop, new_lines, _t2;
        return _regenerator().w(function (_context2) {
          while (1) switch (_context2.n) {
            case 0:
              if (!is_new_po) {
                _context2.n = 5;
                break;
              }
              if (!(merged_config.mode === 'parked_order_populate' && merged_config.order && merged_config.line)) {
                _context2.n = 4;
                break;
              }
              console.log('Detected parked order populate mode', {
                order: merged_config.order,
                line: merged_config.line
              });
              _context2.p = 1;
              _context2.n = 2;
              return api_call('prefill', 'PurchaseOrder', {
                order_id: merged_config.order,
                line: merged_config.line
              });
            case 2:
              prefill_result = _context2.v;
              console.log('Prefill API response:', prefill_result);
              if (prefill_result.success && prefill_result.data) {
                prefill_data = prefill_result.data;
                console.log('Prefill data received:', prefill_data);

                // Apply pre-populate data to header
                if (prefill_data.pre_populate_data) {
                  pre_pop = prefill_data.pre_populate_data; // Set available vendors if provided
                  if (prefill_data.vendors && prefill_data.vendors.length > 0) {
                    console.log('Setting available vendors:', prefill_data.vendors);
                    setAvailableVendors(prefill_data.vendors);
                  }

                  // Update header with location and ship_via
                  setHeader(function (prev) {
                    return _objectSpread(_objectSpread({}, prev), {}, {
                      location: pre_pop.location || prev.location,
                      ship_via: pre_pop.ship_via || prev.ship_via,
                      ordered_by_customer: pre_pop.customer_code || prev.ordered_by_customer,
                      shipping: pre_pop.shipping_address ? {
                        name: pre_pop.shipping_address.name || '',
                        attention: pre_pop.shipping_address.attention || '',
                        address1: pre_pop.shipping_address.address1 || '',
                        address2: pre_pop.shipping_address.address2 || '',
                        city: pre_pop.shipping_address.city || '',
                        state: pre_pop.shipping_address.state || '',
                        zip: pre_pop.shipping_address.zip || '',
                        country: 'USA'
                      } : prev.shipping
                    });
                  });

                  // Add initial items as lines
                  if (pre_pop.initial_items && pre_pop.initial_items.length > 0) {
                    new_lines = pre_pop.initial_items.map(function (item) {
                      if (item.type === 'note') {
                        return {
                          _source: 'active',
                          type: 'X',
                          message: item.message || '',
                          msg: item.message || '',
                          part: '',
                          pcode: '',
                          description: '',
                          pdesc: '',
                          quantity: 0,
                          pqty: 0,
                          price: 0,
                          pprce: 0,
                          discount: 0,
                          pdisc: 0,
                          extended: 0,
                          pext: 0,
                          received_qty: 0,
                          rqty: 0,
                          erd: header.expected_receipt_date,
                          taxable: false
                        };
                      } else {
                        // Part line
                        var qty = item.qty || 1;
                        var price = item.price || 0;
                        var extended = qty * price;
                        return {
                          _source: 'active',
                          part: item.part || '',
                          pcode: item.part || '',
                          description: item.description || '',
                          pdesc: item.description || '',
                          quantity: qty,
                          pqty: qty,
                          price: price,
                          pprce: price,
                          discount: 0,
                          pdisc: 0,
                          extended: extended,
                          pext: extended,
                          received_qty: 0,
                          rqty: 0,
                          erd: header.expected_receipt_date,
                          type: 'R',
                          taxable: false,
                          message: '',
                          msg: ''
                        };
                      }
                    });
                    setLines(new_lines);
                  }
                }
              } else {
                console.error('Prefill failed:', prefill_result.error || 'Unknown error');
              }
              _context2.n = 4;
              break;
            case 3:
              _context2.p = 3;
              _t2 = _context2.v;
              console.error('Error calling prefill:', _t2);
            case 4:
              // Only add empty line if we didn't prepopulate
              if (!merged_config.mode || merged_config.mode !== 'parked_order_populate') {
                add_line();
              }
              _context2.n = 6;
              break;
            case 5:
              _context2.n = 6;
              return load_existing_po();
            case 6:
              return _context2.a(2);
          }
        }, _callee2, null, [[1, 3]]);
      }));
      return function init() {
        return _ref2.apply(this, arguments);
      };
    }();
    init();
  }, []);

  // Load existing PO
  var load_existing_po = /*#__PURE__*/function () {
    var _ref3 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee3() {
      var result, _cleaned_data$header, cleaned_data, _t3;
      return _regenerator().w(function (_context3) {
        while (1) switch (_context3.n) {
          case 0:
            if (poNumber) {
              _context3.n = 1;
              break;
            }
            return _context3.a(2);
          case 1:
            setLoading(true);
            setLoadingMessage('Loading purchase order...');
            _context3.p = 2;
            _context3.n = 3;
            return api_call('get', 'PurchaseOrder', {
              po_number: poNumber
            });
          case 3:
            result = _context3.v;
            if (!result.success) {
              _context3.n = 5;
              break;
            }
            cleaned_data = clean_po_data(result);
            setHeader(map_header_data(cleaned_data.header || {}));
            setLines(cleaned_data.lines || []);

            // Load vendor info if we have vendor code
            if (!((_cleaned_data$header = cleaned_data.header) !== null && _cleaned_data$header !== void 0 && _cleaned_data$header.vendor_code)) {
              _context3.n = 4;
              break;
            }
            _context3.n = 4;
            return load_vendor_details(cleaned_data.header.vendor_code);
          case 4:
            _context3.n = 6;
            break;
          case 5:
            show_error('Failed to load purchase order: ' + (result.error || 'Unknown error'));
          case 6:
            _context3.n = 8;
            break;
          case 7:
            _context3.p = 7;
            _t3 = _context3.v;
            console.error('Error loading PO:', _t3);
            show_error('Failed to load purchase order');
          case 8:
            _context3.p = 8;
            setLoading(false);
            return _context3.f(8);
          case 9:
            return _context3.a(2);
        }
      }, _callee3, null, [[2, 7, 8, 9]]);
    }));
    return function load_existing_po() {
      return _ref3.apply(this, arguments);
    };
  }();

  // Vendor handling
  var handle_vendor_change = /*#__PURE__*/function () {
    var _ref4 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee4(vendor_data) {
      return _regenerator().w(function (_context4) {
        while (1) switch (_context4.n) {
          case 0:
            if (vendor_data) {
              _context4.n = 1;
              break;
            }
            setVendor(null);
            setHeader(function (prev) {
              return _objectSpread(_objectSpread({}, prev), {}, {
                vendor_code: '',
                vendor_name: '',
                billing: {
                  name: '',
                  address1: '',
                  address2: '',
                  city: '',
                  state: '',
                  zip: '',
                  country: 'USA'
                }
              });
            });
            return _context4.a(2);
          case 1:
            setVendor(vendor_data);

            // Update header
            setHeader(function (prev) {
              return _objectSpread(_objectSpread({}, prev), {}, {
                vendor_code: vendor_data.code || '',
                vendor_name: vendor_data.name || '',
                billing: {
                  name: vendor_data.name || '',
                  address1: vendor_data.add1 || '',
                  address2: vendor_data.add2 || '',
                  city: vendor_data.city || '',
                  state: vendor_data.state || '',
                  zip: vendor_data.zip_ || vendor_data.zip || '',
                  country: vendor_data.country || 'USA'
                },
                terms: vendor_data.terms_num || prev.terms
              });
            });

            // Show vendor comments if any
            if (vendor_data.comments1 || vendor_data.comments2) {
              setVendorComments({
                show: true,
                comments1: vendor_data.comments1 || '',
                comments2: vendor_data.comments2 || ''
              });
            } else {
              setVendorComments({
                show: false,
                comments1: '',
                comments2: ''
              });
            }
          case 2:
            return _context4.a(2);
        }
      }, _callee4);
    }));
    return function handle_vendor_change(_x3) {
      return _ref4.apply(this, arguments);
    };
  }();
  var load_vendor_details = /*#__PURE__*/function () {
    var _ref5 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee5(vendor_code) {
      var result, _t4;
      return _regenerator().w(function (_context5) {
        while (1) switch (_context5.n) {
          case 0:
            if (vendor_code) {
              _context5.n = 1;
              break;
            }
            return _context5.a(2);
          case 1:
            console.log('Loading vendor details for:', vendor_code);
            _context5.p = 2;
            _context5.n = 3;
            return api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
              filters: {
                code: {
                  operator: "eq",
                  value: vendor_code
                }
              },
              start: 0,
              length: 1
            });
          case 3:
            result = _context5.v;
            if (!(!result.success || !result.data || result.data.length === 0)) {
              _context5.n = 5;
              break;
            }
            _context5.n = 4;
            return api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
              filters: {
                code: {
                  operator: "ilike",
                  value: vendor_code
                }
              },
              start: 0,
              length: 1
            });
          case 4:
            result = _context5.v;
          case 5:
            if (!(result.success && result.data && result.data.length > 0)) {
              _context5.n = 7;
              break;
            }
            console.log('Found vendor:', result.data[0]);
            _context5.n = 6;
            return handle_vendor_change(result.data[0]);
          case 6:
            return _context5.a(2, result.data[0]);
          case 7:
            console.log('No vendor found for code:', vendor_code);
          case 8:
            _context5.n = 10;
            break;
          case 9:
            _context5.p = 9;
            _t4 = _context5.v;
            console.error('Error loading vendor details:', _t4);
          case 10:
            return _context5.a(2, null);
        }
      }, _callee5, null, [[2, 9]]);
    }));
    return function load_vendor_details(_x4) {
      return _ref5.apply(this, arguments);
    };
  }();

  // Line management
  var add_line = function add_line() {
    var new_line = {
      _source: 'active',
      part: '',
      pcode: '',
      description: '',
      pdesc: '',
      quantity: 1,
      pqty: 1,
      price: 0,
      pprce: 0,
      discount: 0,
      pdisc: 0,
      extended: 0,
      pext: 0,
      received_qty: 0,
      rqty: 0,
      erd: header.expected_receipt_date,
      type: 'R',
      taxable: false,
      message: '',
      msg: ''
    };
    setLines(function (prev) {
      return [].concat(_toConsumableArray(prev), [new_line]);
    });
  };
  var add_note_line = function add_note_line() {
    var new_note = {
      _source: 'active',
      type: 'X',
      message: '',
      msg: '',
      part: '',
      pcode: '',
      description: '',
      pdesc: '',
      quantity: 0,
      pqty: 0,
      price: 0,
      pprce: 0,
      discount: 0,
      pdisc: 0,
      extended: 0,
      pext: 0,
      received_qty: 0,
      rqty: 0,
      erd: header.expected_receipt_date,
      taxable: false
    };
    setLines(function (prev) {
      return [].concat(_toConsumableArray(prev), [new_note]);
    });
  };
  var remove_line = function remove_line(index) {
    var line = lines[index];
    if (line.rqty > 0) {
      show_error('Cannot remove received lines');
      return;
    }
    if (confirm('Remove this line?')) {
      if (line.record) {
        setDeletedLineIds(function (prev) {
          return [].concat(_toConsumableArray(prev), [line.record]);
        });
      }
      setLines(function (prev) {
        return prev.filter(function (_, i) {
          return i !== index;
        });
      });
    }
  };
  var update_line = function update_line(index, field, value) {
    setLines(function (prev) {
      var updated = _toConsumableArray(prev);
      var line = _objectSpread({}, updated[index]);

      // Update both field formats
      line[field] = value;

      // Map fields
      var field_map = {
        'part': 'pcode',
        'description': 'pdesc',
        'quantity': 'pqty',
        'price': 'pprce',
        'discount': 'pdisc',
        'message': 'msg'
      };
      if (field_map[field]) {
        line[field_map[field]] = value;
      }

      // Recalculate extended if needed
      if (line.type !== 'X' && ['quantity', 'price', 'discount'].includes(field)) {
        var qty = parseFloat(line.quantity || line.pqty || 0);
        var price = parseFloat(line.price || line.pprce || 0);
        var discount = parseFloat(line.discount || line.pdisc || 0);
        var extended = qty * (price - discount);
        line.extended = extended;
        line.pext = extended;
      }
      updated[index] = line;
      return updated;
    });
  };

  // Virtual inventory
  var fetch_virtual_inventory = /*#__PURE__*/function () {
    var _ref6 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee6(part, index) {
      var result, _t5;
      return _regenerator().w(function (_context6) {
        while (1) switch (_context6.n) {
          case 0:
            if (part) {
              _context6.n = 1;
              break;
            }
            return _context6.a(2);
          case 1:
            setInventoryLoading(function (prev) {
              return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, index, true));
            });
            _context6.p = 2;
            _context6.n = 3;
            return api_call('list', 'JADVDATA_dbo_virtual_inventory', {
              filters: {
                part: {
                  operator: "eq",
                  value: part
                }
              },
              start: 0,
              length: 50
            });
          case 3:
            result = _context6.v;
            if (result.success && result.data && result.data.length > 0) {
              setVirtualInventory(function (prev) {
                return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, index, result.data));
              });
            } else {
              setVirtualInventory(function (prev) {
                return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, index, []));
              });
            }
            _context6.n = 5;
            break;
          case 4:
            _context6.p = 4;
            _t5 = _context6.v;
            console.error('Error fetching virtual inventory:', _t5);
            setVirtualInventory(function (prev) {
              return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, index, []));
            });
          case 5:
            _context6.p = 5;
            setInventoryLoading(function (prev) {
              return _objectSpread(_objectSpread({}, prev), {}, _defineProperty({}, index, false));
            });
            return _context6.f(5);
          case 6:
            return _context6.a(2);
        }
      }, _callee6, null, [[2, 4, 5, 6]]);
    }));
    return function fetch_virtual_inventory(_x5, _x6) {
      return _ref6.apply(this, arguments);
    };
  }();
  var select_vendor_from_inventory = /*#__PURE__*/function () {
    var _ref7 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee7(vendor_code, line_index) {
      var vendor_data;
      return _regenerator().w(function (_context7) {
        while (1) switch (_context7.n) {
          case 0:
            _context7.n = 1;
            return load_vendor_details(vendor_code);
          case 1:
            vendor_data = _context7.v;
            return _context7.a(2, vendor_data);
        }
      }, _callee7);
    }));
    return function select_vendor_from_inventory(_x7, _x8) {
      return _ref7.apply(this, arguments);
    };
  }();

  // Save PO
  var save_po = /*#__PURE__*/function () {
    var _ref8 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee8() {
      var lines_with_numbers, save_data, operation, result, _result$data, _result$data2, _t6;
      return _regenerator().w(function (_context8) {
        while (1) switch (_context8.n) {
          case 0:
            if (validate_po()) {
              _context8.n = 1;
              break;
            }
            return _context8.a(2);
          case 1:
            setLoading(true);
            setLoadingMessage('Saving purchase order...');
            _context8.p = 2;
            // Add line numbers to each line
            lines_with_numbers = lines.map(function (line, index) {
              return _objectSpread(_objectSpread({}, line), {}, {
                line_number: index + 1
              });
            });
            save_data = {
              header: header,
              lines: lines_with_numbers,
              deleted_line_ids: deletedLineIds
            };
            if (isEditMode) {
              save_data.po_number = poNumber;
            }
            operation = isEditMode ? 'update' : 'create';
            _context8.n = 3;
            return api_call(operation, 'PurchaseOrder', {
              data: save_data
            });
          case 3:
            result = _context8.v;
            if (result.success) {
              console.log('SAVE SUCCESS - Before state updates:', {
                current_poNumber: poNumber,
                current_isSaved: isSaved,
                new_po_number: (_result$data = result.data) === null || _result$data === void 0 ? void 0 : _result$data.po_number
              });
              show_toast('Purchase order saved successfully!', 'success');
              setIsSaved(true);
              if (!isEditMode && (_result$data2 = result.data) !== null && _result$data2 !== void 0 && _result$data2.po_number) {
                // Set the PO number for the current session
                setPoNumber(result.data.po_number);
                console.log('SAVE SUCCESS - After setPoNumber:', {
                  poNumber: result.data.po_number,
                  isSaved: true
                });
              }
              console.log('SAVE SUCCESS - Final state (may not be updated yet):', {
                poNumber: poNumber,
                isSaved: isSaved,
                isEditMode: isEditMode
              });
              setDeletedLineIds([]);
            } else {
              show_toast(result.error || result.message || 'Failed to save purchase order', 'error');
            }
            _context8.n = 5;
            break;
          case 4:
            _context8.p = 4;
            _t6 = _context8.v;
            console.error('Error saving PO:', _t6);
            show_toast('Failed to save purchase order', 'error');
          case 5:
            _context8.p = 5;
            setLoading(false);
            return _context8.f(5);
          case 6:
            return _context8.a(2);
        }
      }, _callee8, null, [[2, 4, 5, 6]]);
    }));
    return function save_po() {
      return _ref8.apply(this, arguments);
    };
  }();

  // Calculations
  var totals = (0,external_React_namespaceObject.useMemo)(function () {
    var subtotal = 0;
    lines.forEach(function (line) {
      var extended = parseFloat(line.extended || line.pext || 0);
      subtotal += extended;
    });
    var freight = parseFloat(header.freight || 0);
    var tax_amount = parseFloat(header.tax_amount || 0);
    var total = subtotal + freight + tax_amount;
    return {
      subtotal: subtotal,
      freight: freight,
      tax_amount: tax_amount,
      total: total
    };
  }, [lines, header.freight, header.tax_amount]);

  // Sync calculated totals back to header
  (0,external_React_namespaceObject.useEffect)(function () {
    setHeader(function (prev) {
      return _objectSpread(_objectSpread({}, prev), {}, {
        subtotal: totals.subtotal,
        total: totals.total
      });
    });
  }, [totals.subtotal, totals.total]);

  // Sync line count to header
  (0,external_React_namespaceObject.useEffect)(function () {
    setHeader(function (prev) {
      return _objectSpread(_objectSpread({}, prev), {}, {
        line_count: lines.length
      });
    });
  }, [lines.length]);

  // Validation
  var validate_po = function validate_po() {
    var errors = [];
    if (!header.vendor_code) {
      errors.push('Please select a vendor');
    }
    if (!header.order_date) {
      errors.push('Order date is required');
    }
    if (!header.expected_receipt_date) {
      errors.push('Expected receipt date is required');
    }
    if (lines.length === 0) {
      errors.push('At least one line item is required');
    }
    var has_valid_line = false;
    lines.forEach(function (line) {
      var part = line.part || line.pcode;
      var qty = parseFloat(line.quantity || line.pqty || 0);
      if (part && qty > 0) {
        has_valid_line = true;
      }
    });
    if (!has_valid_line) {
      errors.push('At least one line must have a part and quantity');
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
  var show_success = function show_success(message) {
    show_toast(message, 'success');
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

  // Render helpers
  var is_partially_received = lines.some(function (line) {
    return line.rqty > 0;
  });
  var can_edit_header = !is_partially_received && !isSaved && !is_view_mode;
  var can_edit_lines = !isSaved && !is_view_mode;
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "container-fluid mt-3"
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
  })), /*#__PURE__*/external_React_default().createElement("h4", {
    className: "mb-3"
  }, "Purchase Order", poNumber && /*#__PURE__*/external_React_default().createElement("span", {
    className: "ms-2"
  }, "#", poNumber), header.printed && /*#__PURE__*/external_React_default().createElement("span", {
    className: "badge bg-success ms-2"
  }, "Printed")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-6 mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card h-100"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0"
  }, "Order Details")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
  }, "Vendor ", /*#__PURE__*/external_React_default().createElement("span", {
    className: "text-danger"
  }, "*")), /*#__PURE__*/external_React_default().createElement(VendorSelect, {
    value: header.vendor_code,
    vendor_name: header.vendor_name,
    vendors: availableVendors,
    onVendorChange: handle_vendor_change,
    api_call: api_call,
    disabled: !can_edit_header || is_view_mode
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
  }, "Ordered By"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: header.ordered_by_customer || '',
    onChange: function onChange(e) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          ordered_by_customer: e.target.value
        });
      });
    },
    placeholder: "Name...",
    disabled: is_view_mode
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
  }, "Order Date ", /*#__PURE__*/external_React_default().createElement("span", {
    className: "text-danger"
  }, "*")), /*#__PURE__*/external_React_default().createElement("input", {
    type: "date",
    className: "form-control form-control-sm",
    value: header.order_date,
    onChange: function onChange(e) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          order_date: e.target.value
        });
      });
    },
    disabled: !can_edit_header,
    required: true
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-6"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
  }, "Expected Date ", /*#__PURE__*/external_React_default().createElement("span", {
    className: "text-danger"
  }, "*")), /*#__PURE__*/external_React_default().createElement("input", {
    type: "date",
    className: "form-control form-control-sm",
    value: header.expected_receipt_date,
    onChange: function onChange(e) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          expected_receipt_date: e.target.value
        });
      });
    },
    disabled: !can_edit_header // Add disabled prop
    ,
    required: true
  })))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-6 mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card h-100"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0"
  }, "Shipping Details")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
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
    disabled: !can_edit_header
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
  }, "Ship Via"), /*#__PURE__*/external_React_default().createElement(ShipViaInput, {
    value: header.ship_via,
    onChange: function onChange(value) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          ship_via: value
        });
      });
    },
    api_call: api_call,
    disabled: !can_edit_header
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
  }, "Freight"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: header.freight,
    onChange: function onChange(e) {
      var val = parseFloat(e.target.value) || 0;
      setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          freight: Math.max(0, val)
        });
      });
    },
    min: "0",
    step: "0.01",
    disabled: is_view_mode
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-12"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label"
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
    disabled: !can_edit_header // Add disabled prop
  }))))))), vendorComments.show && /*#__PURE__*/external_React_default().createElement("div", {
    className: "alert alert-warning"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "alert-heading"
  }, "Vendor Notes:"), vendorComments.comments1 && /*#__PURE__*/external_React_default().createElement("p", {
    className: "mb-2"
  }, vendorComments.comments1), vendorComments.comments2 && /*#__PURE__*/external_React_default().createElement("p", {
    className: "mb-0"
  }, vendorComments.comments2)), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-3 mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-6"
  }, /*#__PURE__*/external_React_default().createElement(AddressCard, {
    title: "Billing Address",
    address: header.billing,
    onChange: function onChange(billing) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          billing: billing
        });
      });
    },
    readonly: !can_edit_header || is_view_mode
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-lg-6"
  }, /*#__PURE__*/external_React_default().createElement(AddressCard, {
    title: "Shipping Address",
    address: header.shipping,
    onChange: function onChange(shipping) {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          shipping: shipping
        });
      });
    },
    showCopyButton: true,
    onCopy: function onCopy() {
      return setHeader(function (prev) {
        return _objectSpread(_objectSpread({}, prev), {}, {
          shipping: _objectSpread(_objectSpread({}, prev.billing), {}, {
            attention: prev.shipping.attention
          })
        });
      });
    },
    readonly: is_view_mode
  }))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0"
  }, "Line Items"), /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement(AddLineButton, {
    onClick: add_line,
    label: "Add Line",
    icon: Plus,
    disabled: isSaved || is_view_mode
  }), /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-secondary btn-sm ms-2",
    onClick: add_note_line,
    disabled: isSaved || is_view_mode
  }, /*#__PURE__*/external_React_default().createElement(MessageSquare, {
    size: 16,
    className: "me-1"
  }), "Add Note"))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, lines.length === 0 ? /*#__PURE__*/external_React_default().createElement("div", {
    className: "text-muted text-center p-4"
  }, "No lines added. Click \"Add Line\" to start.") : lines.map(function (line, index) {
    return /*#__PURE__*/external_React_default().createElement(LineItem, {
      key: index,
      line: line,
      index: index,
      onUpdate: update_line,
      onRemove: remove_line,
      api_call: api_call,
      virtualInventory: virtualInventory[index],
      inventoryLoading: inventoryLoading[index],
      onFetchInventory: function onFetchInventory(part) {
        return fetch_virtual_inventory(part, index);
      },
      onSelectVendor: select_vendor_from_inventory,
      readonly: isSaved || is_view_mode
    });
  }))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row mb-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-4 offset-md-8"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between mb-2"
  }, /*#__PURE__*/external_React_default().createElement("span", null, "Subtotal:"), /*#__PURE__*/external_React_default().createElement("strong", null, "$", totals.subtotal.toFixed(2))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between mb-2"
  }, /*#__PURE__*/external_React_default().createElement("span", null, "Tax:"), /*#__PURE__*/external_React_default().createElement("strong", null, "$", totals.tax_amount.toFixed(2))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between mb-2"
  }, /*#__PURE__*/external_React_default().createElement("span", null, "Freight:"), /*#__PURE__*/external_React_default().createElement("strong", null, "$", totals.freight.toFixed(2))), /*#__PURE__*/external_React_default().createElement("hr", null), /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "h5"
  }, "Total:"), /*#__PURE__*/external_React_default().createElement("strong", {
    className: "h5"
  }, "$", totals.total.toFixed(2))))))), /*#__PURE__*/external_React_default().createElement("div", {
    className: "mb-4"
  }, !isSaved && !is_view_mode && /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-success me-2",
    onClick: save_po,
    disabled: loading
  }, /*#__PURE__*/external_React_default().createElement(Save, {
    size: 16,
    className: "me-1"
  }), isEditMode ? 'Update PO' : 'Create PO'), isSaved && poNumber && !is_view_mode && /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-primary me-2",
    onClick: /*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee9() {
      var _window$app2, _window$app3, _window$app4, _window$app5, _window$app6, user, result, order_id, _t7;
      return _regenerator().w(function (_context9) {
        while (1) switch (_context9.n) {
          case 0:
            setLoading(true);
            setLoadingMessage('Processing receive and invoice...');
            _context9.p = 1;
            // Debug: Check all possible user locations
            console.log('=== USER DEBUG ===', {
              config: config,
              config_user: config.user,
              window_user: window.user,
              window_app: window.app,
              window_app_user: (_window$app2 = window.app) === null || _window$app2 === void 0 ? void 0 : _window$app2.user,
              window_app_state: (_window$app3 = window.app) === null || _window$app3 === void 0 ? void 0 : _window$app3.state,
              window_app_state_user: (_window$app4 = window.app) === null || _window$app4 === void 0 || (_window$app4 = _window$app4.state) === null || _window$app4 === void 0 ? void 0 : _window$app4.user,
              merged_config: merged_config,
              merged_config_user: merged_config.user,
              localStorage_user: localStorage.getItem('user'),
              sessionStorage_user: sessionStorage.getItem('user')
            });

            // Try multiple sources for user
            user = config.user || window.user || ((_window$app5 = window.app) === null || _window$app5 === void 0 ? void 0 : _window$app5.user) || ((_window$app6 = window.app) === null || _window$app6 === void 0 || (_window$app6 = _window$app6.state) === null || _window$app6 === void 0 ? void 0 : _window$app6.user) || merged_config.user || (localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null) || null;
            console.log('Final user found:', user);
            _context9.n = 2;
            return api_call('rni_inv', 'PurchaseOrder', {
              po_number: poNumber,
              parked_order_id: merged_config.order || merged_config.parked_order_id || null,
              parked_order_line: merged_config.line || null,
              user: user,
              user_id: (user === null || user === void 0 ? void 0 : user.id) || (user === null || user === void 0 ? void 0 : user.user_id) || null,
              user_name: (user === null || user === void 0 ? void 0 : user.name) || (user === null || user === void 0 ? void 0 : user.username) || null
            });
          case 2:
            result = _context9.v;
            if (result.success) {
              show_toast('Successfully received and invoiced PO', 'success');
              // Navigate back to parked order or PO list
              if (merged_config.order || merged_config.parked_order_id) {
                order_id = merged_config.order || merged_config.parked_order_id;
                if (navigation) {
                  navigation.navigate_to('ParkedOrderDetail', {
                    id: order_id
                  });
                }
              } else {
                if (navigation) {
                  navigation.navigate_to('PurchaseOrders');
                }
              }
            } else {
              show_error(result.message || 'Failed to receive and invoice PO');
            }
            _context9.n = 4;
            break;
          case 3:
            _context9.p = 3;
            _t7 = _context9.v;
            console.error('Error processing receive and invoice:', _t7);
            show_error('Failed to receive and invoice PO');
          case 4:
            _context9.p = 4;
            setLoading(false);
            return _context9.f(4);
          case 5:
            return _context9.a(2);
        }
      }, _callee9, null, [[1, 3, 4, 5]]);
    })),
    disabled: loading
  }, /*#__PURE__*/external_React_default().createElement(Truck, {
    size: 16,
    className: "me-1"
  }), "Receive & Invoice"), /*#__PURE__*/external_React_default().createElement(CancelButton, {
    navigation: navigation,
    merged_config: merged_config
  })));
};

// Sub-components

var CancelButton = function CancelButton(_ref0) {
  var navigation = _ref0.navigation,
    merged_config = _ref0.merged_config;
  var handle_cancel = function handle_cancel() {
    // If we came from a parked order, go back to it
    if (merged_config.order || merged_config.parked_order_id) {
      var order_id = merged_config.order || merged_config.parked_order_id;
      if (navigation) {
        navigation.navigate_to('ParkedOrderDetail', {
          id: order_id
        });
      }
    } else {
      // Otherwise go to purchase orders list
      if (navigation) {
        navigation.navigate_to('PurchaseOrders');
      }
    }
  };

  // In view mode, you might want to show "Back" instead of "Cancel"
  var button_label = merged_config.mode === 'view' ? 'Back' : 'Cancel';
  return /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-secondary",
    onClick: handle_cancel
  }, /*#__PURE__*/external_React_default().createElement(X, {
    size: 16,
    className: "me-1"
  }), button_label);
};
var VendorSelect = function VendorSelect(_ref1) {
  var value = _ref1.value,
    vendor_name = _ref1.vendor_name,
    vendors = _ref1.vendors,
    onVendorChange = _ref1.onVendorChange,
    api_call = _ref1.api_call,
    disabled = _ref1.disabled;
  var _useState25 = (0,external_React_namespaceObject.useState)(''),
    _useState26 = _slicedToArray(_useState25, 2),
    searchTerm = _useState26[0],
    setSearchTerm = _useState26[1];
  var _useState27 = (0,external_React_namespaceObject.useState)([]),
    _useState28 = _slicedToArray(_useState27, 2),
    suggestions = _useState28[0],
    setSuggestions = _useState28[1];
  var _useState29 = (0,external_React_namespaceObject.useState)(false),
    _useState30 = _slicedToArray(_useState29, 2),
    loading = _useState30[0],
    setLoading = _useState30[1];
  var _useState31 = (0,external_React_namespaceObject.useState)(false),
    _useState32 = _slicedToArray(_useState31, 2),
    showDropdown = _useState32[0],
    setShowDropdown = _useState32[1];

  // Update search term when value changes (e.g., when selected from virtual inventory)
  (0,external_React_namespaceObject.useEffect)(function () {
    if (value && vendor_name) {
      setSearchTerm("".concat(value, " - ").concat(vendor_name));
    } else if (value) {
      setSearchTerm(value);
    }
  }, [value, vendor_name]);

  // Search vendors function
  var search_vendors = /*#__PURE__*/function () {
    var _ref10 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee0(term) {
      var result, _t8;
      return _regenerator().w(function (_context0) {
        while (1) switch (_context0.n) {
          case 0:
            if (!(term.length < 2)) {
              _context0.n = 1;
              break;
            }
            setSuggestions([]);
            return _context0.a(2);
          case 1:
            setLoading(true);
            _context0.p = 2;
            _context0.n = 3;
            return api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
              filters: {
                name: {
                  operator: "ilike",
                  value: "%".concat(term, "%")
                }
              },
              start: 0,
              length: 10
            });
          case 3:
            result = _context0.v;
            if (result.success && result.data) {
              setSuggestions(result.data);
            }
            _context0.n = 5;
            break;
          case 4:
            _context0.p = 4;
            _t8 = _context0.v;
            console.error('Error searching vendors:', _t8);
            setSuggestions([]);
          case 5:
            setLoading(false);
          case 6:
            return _context0.a(2);
        }
      }, _callee0, null, [[2, 4]]);
    }));
    return function search_vendors(_x9) {
      return _ref10.apply(this, arguments);
    };
  }();
  (0,external_React_namespaceObject.useEffect)(function () {
    var timer = setTimeout(function () {
      if (searchTerm && !value) {
        search_vendors(searchTerm);
      }
    }, 300);
    return function () {
      return clearTimeout(timer);
    };
  }, [searchTerm, value]);

  // Static vendors mode
  if (vendors && vendors.length > 0) {
    return /*#__PURE__*/external_React_default().createElement("select", {
      className: "form-select form-select-sm",
      value: value || '',
      onChange: (/*#__PURE__*/function () {
        var _ref11 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee1(e) {
          var _result$data3;
          var vendor_code, result;
          return _regenerator().w(function (_context1) {
            while (1) switch (_context1.n) {
              case 0:
                vendor_code = e.target.value;
                if (vendor_code) {
                  _context1.n = 1;
                  break;
                }
                onVendorChange(null);
                return _context1.a(2);
              case 1:
                _context1.n = 2;
                return api_call('list', 'GPACIFIC_dbo_BKAPVEND', {
                  filters: {
                    code: {
                      operator: "eq",
                      value: vendor_code
                    }
                  },
                  start: 0,
                  length: 1
                });
              case 2:
                result = _context1.v;
                if (result.success && (_result$data3 = result.data) !== null && _result$data3 !== void 0 && _result$data3[0]) {
                  onVendorChange(result.data[0]);
                }
              case 3:
                return _context1.a(2);
            }
          }, _callee1);
        }));
        return function (_x0) {
          return _ref11.apply(this, arguments);
        };
      }()),
      disabled: disabled,
      required: true
    }, /*#__PURE__*/external_React_default().createElement("option", {
      value: ""
    }, "Select vendor..."), vendors.map(function (v) {
      return /*#__PURE__*/external_React_default().createElement("option", {
        key: v.code,
        value: v.code
      }, v.code, " - ", v.company);
    }));
  }

  // Autocomplete mode
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
        onVendorChange(null);
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
    placeholder: "Search vendor by code or name...",
    disabled: disabled,
    required: true
  }), showDropdown && (suggestions.length > 0 || loading) && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-menu d-block position-absolute mt-1",
    style: {
      minWidth: '400px',
      maxHeight: '300px',
      overflowY: 'auto'
    }
  }, loading && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-item-text text-center"
  }, /*#__PURE__*/external_React_default().createElement("small", {
    className: "text-muted"
  }, "Loading...")), !loading && suggestions.map(function (vendor) {
    return /*#__PURE__*/external_React_default().createElement("button", {
      key: vendor.code,
      className: "dropdown-item text-truncate",
      type: "button",
      onClick: function onClick() {
        onVendorChange(vendor);
        setSearchTerm("".concat(vendor.code, " - ").concat(vendor.name));
        setShowDropdown(false);
      },
      title: "".concat(vendor.code, " - ").concat(vendor.name)
    }, /*#__PURE__*/external_React_default().createElement("strong", null, vendor.code), " - ", vendor.name);
  })));
};
var TermsSelect = function TermsSelect(_ref12) {
  var value = _ref12.value,
    _onChange = _ref12.onChange,
    api_call = _ref12.api_call,
    disabled = _ref12.disabled;
  var _useState33 = (0,external_React_namespaceObject.useState)([]),
    _useState34 = _slicedToArray(_useState33, 2),
    terms = _useState34[0],
    setTerms = _useState34[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    var load_terms = /*#__PURE__*/function () {
      var _ref13 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee10() {
        var result;
        return _regenerator().w(function (_context10) {
          while (1) switch (_context10.n) {
            case 0:
              _context10.n = 1;
              return api_call('list', 'GPACIFIC_dbo_BKSYTERM', {
                start: 0,
                length: 0,
                return_columns: ["num", "desc"],
                order: [{
                  column: 0,
                  dir: 'asc'
                }],
                columns: [{
                  name: 'num'
                }, {
                  name: 'desc'
                }]
              });
            case 1:
              result = _context10.v;
              if (result.success && result.data) {
                setTerms(result.data);
              }
            case 2:
              return _context10.a(2);
          }
        }, _callee10);
      }));
      return function load_terms() {
        return _ref13.apply(this, arguments);
      };
    }();
    load_terms();
  }, []);
  return /*#__PURE__*/external_React_default().createElement("select", {
    className: "form-select form-select-sm",
    value: value,
    onChange: function onChange(e) {
      return _onChange(e.target.value);
    },
    disabled: disabled
  }, /*#__PURE__*/external_React_default().createElement("option", {
    value: ""
  }, "Select Terms..."), terms.map(function (term) {
    return /*#__PURE__*/external_React_default().createElement("option", {
      key: term.num,
      value: term.num
    }, term.desc);
  }));
};
var LocationSelect = function LocationSelect(_ref14) {
  var value = _ref14.value,
    _onChange2 = _ref14.onChange,
    api_call = _ref14.api_call,
    company = _ref14.company,
    disabled = _ref14.disabled;
  var _useState35 = (0,external_React_namespaceObject.useState)([]),
    _useState36 = _slicedToArray(_useState35, 2),
    locations = _useState36[0],
    setLocations = _useState36[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    var load_locations = /*#__PURE__*/function () {
      var _ref15 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee11() {
        var result;
        return _regenerator().w(function (_context11) {
          while (1) switch (_context11.n) {
            case 0:
              _context11.n = 1;
              return api_call('list', 'JADVDATA_dbo_locations', {
                start: 0,
                length: 0,
                return_columns: ["location", "location_name"],
                order: [{
                  column: 1,
                  dir: 'asc'
                }],
                columns: [{
                  name: 'location'
                }, {
                  name: 'location_name'
                }],
                filters: {
                  company: {
                    operator: "eq",
                    value: company || "PACIFIC"
                  },
                  warehouse: {
                    operator: "eq",
                    value: "1"
                  },
                  active: {
                    operator: "eq",
                    value: "1"
                  }
                }
              });
            case 1:
              result = _context11.v;
              if (result.success && result.data) {
                setLocations(result.data);
              }
            case 2:
              return _context11.a(2);
          }
        }, _callee11);
      }));
      return function load_locations() {
        return _ref15.apply(this, arguments);
      };
    }();
    load_locations();
  }, []);
  return /*#__PURE__*/external_React_default().createElement("select", {
    className: "form-select form-select-sm",
    value: value,
    onChange: function onChange(e) {
      return _onChange2(e.target.value);
    },
    disabled: disabled // Add disabled prop
  }, /*#__PURE__*/external_React_default().createElement("option", {
    value: ""
  }, "Select Location..."), locations.map(function (loc) {
    return /*#__PURE__*/external_React_default().createElement("option", {
      key: loc.location,
      value: loc.location
    }, loc.location, " - ", loc.location_name);
  }));
};
var ShipViaInput = function ShipViaInput(_ref16) {
  var value = _ref16.value,
    _onChange3 = _ref16.onChange,
    api_call = _ref16.api_call,
    disabled = _ref16.disabled;
  var ship_options = ['UPS', 'FEDEX', 'WILL CALL', 'LOCAL', 'FREIGHT', 'USPS', 'DHL'];
  return /*#__PURE__*/external_React_default().createElement("select", {
    className: "form-select form-select-sm",
    value: value,
    onChange: function onChange(e) {
      return _onChange3(e.target.value);
    },
    disabled: disabled
  }, /*#__PURE__*/external_React_default().createElement("option", {
    value: ""
  }, "Select ship via..."), ship_options.map(function (opt) {
    return /*#__PURE__*/external_React_default().createElement("option", {
      key: opt,
      value: opt
    }, opt);
  }));
};
var AddressCard = function AddressCard(_ref17) {
  var title = _ref17.title,
    address = _ref17.address,
    _onChange4 = _ref17.onChange,
    readonly = _ref17.readonly,
    showCopyButton = _ref17.showCopyButton,
    onCopy = _ref17.onCopy;
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "card h-100"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header d-flex justify-content-between align-items-center"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0"
  }, title), showCopyButton && !readonly && /*#__PURE__*/external_React_default().createElement("button", {
    type: "button",
    className: "btn btn-sm btn-secondary",
    onClick: onCopy
  }, /*#__PURE__*/external_React_default().createElement(Copy, {
    size: 14,
    className: "me-1"
  }), "Copy from Billing")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.name,
    onChange: function onChange(e) {
      return _onChange4(_objectSpread(_objectSpread({}, address), {}, {
        name: e.target.value
      }));
    },
    placeholder: "Company Name",
    readOnly: readonly
  })), title === "Shipping Address" && /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.attention || '',
    onChange: function onChange(e) {
      return _onChange4(_objectSpread(_objectSpread({}, address), {}, {
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
    value: address.address1,
    onChange: function onChange(e) {
      return _onChange4(_objectSpread(_objectSpread({}, address), {}, {
        address1: e.target.value
      }));
    },
    placeholder: "Address Line 1",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.address2,
    onChange: function onChange(e) {
      return _onChange4(_objectSpread(_objectSpread({}, address), {}, {
        address2: e.target.value
      }));
    },
    placeholder: "Address Line 2",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-6"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.city,
    onChange: function onChange(e) {
      return _onChange4(_objectSpread(_objectSpread({}, address), {}, {
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
    value: address.state,
    onChange: function onChange(e) {
      return _onChange4(_objectSpread(_objectSpread({}, address), {}, {
        state: e.target.value
      }));
    },
    placeholder: "ST",
    maxLength: "2",
    readOnly: readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-4"
  }, /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: address.zip,
    onChange: function onChange(e) {
      return _onChange4(_objectSpread(_objectSpread({}, address), {}, {
        zip: e.target.value
      }));
    },
    placeholder: "ZIP",
    readOnly: readonly
  })))));
};
var LineItem = function LineItem(_ref18) {
  var line = _ref18.line,
    index = _ref18.index,
    onUpdate = _ref18.onUpdate,
    _onRemove = _ref18.onRemove,
    api_call = _ref18.api_call,
    virtualInventory = _ref18.virtualInventory,
    inventoryLoading = _ref18.inventoryLoading,
    onFetchInventory = _ref18.onFetchInventory,
    onSelectVendor = _ref18.onSelectVendor,
    readonly = _ref18.readonly;
  var is_received = parseFloat(line.rqty || 0) > 0;
  var is_historical = line._source === 'historical';
  var is_readonly = is_received || is_historical || readonly;
  var line_number = index + 1;
  var is_note_line = line.type === 'X' || !line.pcode && !line.part && line.msg;
  if (is_note_line) {
    return /*#__PURE__*/external_React_default().createElement("div", {
      className: "card mb-2"
    }, /*#__PURE__*/external_React_default().createElement("div", {
      className: "card-body"
    }, /*#__PURE__*/external_React_default().createElement("div", {
      className: "row align-items-center"
    }, /*#__PURE__*/external_React_default().createElement("div", {
      className: "col-auto"
    }, /*#__PURE__*/external_React_default().createElement("span", {
      className: "fw-bold text-muted"
    }, "Line ", line_number), is_received && /*#__PURE__*/external_React_default().createElement("span", {
      className: "badge bg-success ms-2"
    }, "RECEIVED")), /*#__PURE__*/external_React_default().createElement("div", {
      className: "col-auto"
    }, /*#__PURE__*/external_React_default().createElement("span", {
      className: "badge bg-info"
    }, "NOTE")), /*#__PURE__*/external_React_default().createElement("div", {
      className: "col"
    }, /*#__PURE__*/external_React_default().createElement("input", {
      type: "text",
      className: "form-control form-control-sm",
      value: line.message || line.msg || '',
      onChange: function onChange(e) {
        return onUpdate(index, 'message', e.target.value);
      },
      maxLength: "30",
      placeholder: "Note (max 30 characters)",
      readOnly: is_readonly
    })), !is_readonly && /*#__PURE__*/external_React_default().createElement("div", {
      className: "col-auto"
    }, /*#__PURE__*/external_React_default().createElement("button", {
      className: "btn btn-sm btn-danger",
      onClick: function onClick() {
        return _onRemove(index);
      }
    }, /*#__PURE__*/external_React_default().createElement(Trash2, {
      size: 16
    }))))));
  }
  return /*#__PURE__*/external_React_default().createElement("div", {
    className: "card mb-2 "
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "d-flex justify-content-between align-items-center mb-2"
  }, /*#__PURE__*/external_React_default().createElement("div", null, /*#__PURE__*/external_React_default().createElement("span", {
    className: "fw-bold text-muted"
  }, "Line ", line_number), is_received && /*#__PURE__*/external_React_default().createElement("span", {
    className: "badge bg-success ms-2"
  }, "RECEIVED")), !is_readonly && /*#__PURE__*/external_React_default().createElement(RemoveLineButton, {
    onRemove: function onRemove() {
      return _onRemove(index);
    }
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "row g-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-2"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Part #"), /*#__PURE__*/external_React_default().createElement(PartSearch, {
    value: line.part || line.pcode || '',
    onChange: function onChange(value) {
      return onUpdate(index, 'part', value);
    },
    onPartSelect: (/*#__PURE__*/function () {
      var _ref19 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee12(part) {
        var _cost_result$data;
        var cost_result;
        return _regenerator().w(function (_context12) {
          while (1) switch (_context12.n) {
            case 0:
              onUpdate(index, 'part', part.part);
              onUpdate(index, 'description', part.inventory_description);

              // Fetch cost
              _context12.n = 1;
              return api_call('list', 'GPACIFIC_dbo_BKICMSTR', {
                return_columns: ["code", "lstc"],
                order: [{
                  column: 0,
                  dir: 'asc'
                }],
                columns: [{
                  name: 'code'
                }, {
                  name: 'lstc'
                }],
                start: 0,
                length: 1,
                filters: {
                  code: {
                    operator: "eq",
                    value: part.part
                  }
                }
              });
            case 1:
              cost_result = _context12.v;
              if (cost_result.success && (_cost_result$data = cost_result.data) !== null && _cost_result$data !== void 0 && _cost_result$data[0]) {
                onUpdate(index, 'price', cost_result.data[0].lstc || 0);
              }

              // Fetch virtual inventory
              onFetchInventory(part.part);
            case 2:
              return _context12.a(2);
          }
        }, _callee12);
      }));
      return function (_x1) {
        return _ref19.apply(this, arguments);
      };
    }()),
    api_call: api_call,
    readonly: is_readonly || readonly,
    disabled: is_readonly || readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Description"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: line.description || line.pdesc || '',
    onChange: function onChange(e) {
      return onUpdate(index, 'description', e.target.value);
    },
    placeholder: "Part description",
    readOnly: is_readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-1"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Qty"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: line.quantity || line.pqty || 0,
    onChange: function onChange(e) {
      var val = parseFloat(e.target.value) || 0;
      onUpdate(index, 'quantity', Math.max(0, val));
    },
    min: "0",
    step: "1",
    readOnly: is_readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-1"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Price"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: line.price || line.pprce || 0,
    onChange: function onChange(e) {
      var val = parseFloat(e.target.value) || 0;
      onUpdate(index, 'price', Math.max(0, val));
    },
    min: "0",
    step: "0.01",
    readOnly: is_readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-1"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Disc"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "number",
    className: "form-control form-control-sm",
    value: line.discount || line.pdisc || 0,
    onChange: function onChange(e) {
      var val = parseFloat(e.target.value) || 0;
      onUpdate(index, 'discount', Math.max(0, val));
    },
    min: "0",
    readOnly: is_readonly
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-1"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Extended"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "text",
    className: "form-control form-control-sm",
    value: "$".concat((line.extended || line.pext || 0).toFixed(2)),
    readOnly: true
  })), /*#__PURE__*/external_React_default().createElement("div", {
    className: "col-md-2"
  }, /*#__PURE__*/external_React_default().createElement("label", {
    className: "form-label small mb-1"
  }, "Expected Date"), /*#__PURE__*/external_React_default().createElement("input", {
    type: "date",
    className: "form-control form-control-sm",
    value: line.erd || '',
    onChange: function onChange(e) {
      return onUpdate(index, 'erd', e.target.value);
    },
    readOnly: is_readonly || readonly // Add parent readonly prop
  }))), virtualInventory && virtualInventory.length > 0 && /*#__PURE__*/external_React_default().createElement("div", {
    className: "mt-3"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card border-secondary"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-header py-2"
  }, /*#__PURE__*/external_React_default().createElement("h6", {
    className: "mb-0 small"
  }, "Integrated vendor inventory availability")), /*#__PURE__*/external_React_default().createElement("div", {
    className: "card-body p-2"
  }, inventoryLoading ? /*#__PURE__*/external_React_default().createElement("div", {
    className: "text-center py-2"
  }, /*#__PURE__*/external_React_default().createElement("div", {
    className: "spinner-border spinner-border-sm text-primary",
    role: "status"
  }, /*#__PURE__*/external_React_default().createElement("span", {
    className: "visually-hidden"
  }, "Loading...")), /*#__PURE__*/external_React_default().createElement("span", {
    className: "ms-2 small text-muted"
  }, "Loading inventory...")) : /*#__PURE__*/external_React_default().createElement("div", {
    className: "table-responsive"
  }, /*#__PURE__*/external_React_default().createElement("table", {
    className: "table table-sm table-hover table-striped mb-0"
  }, /*#__PURE__*/external_React_default().createElement("thead", null, /*#__PURE__*/external_React_default().createElement("tr", null, /*#__PURE__*/external_React_default().createElement("th", null, "Company"), /*#__PURE__*/external_React_default().createElement("th", null, "Location"), /*#__PURE__*/external_React_default().createElement("th", null, "Qty"), /*#__PURE__*/external_React_default().createElement("th", {
    style: {
      width: '80px'
    }
  }, "Action"))), /*#__PURE__*/external_React_default().createElement("tbody", null, virtualInventory.map(function (item, idx) {
    return /*#__PURE__*/external_React_default().createElement("tr", {
      key: idx
    }, /*#__PURE__*/external_React_default().createElement("td", {
      className: "fw-bold"
    }, (item.company || '').toUpperCase()), /*#__PURE__*/external_React_default().createElement("td", null, item.loc || ''), /*#__PURE__*/external_React_default().createElement("td", null, item.qty || 0), /*#__PURE__*/external_React_default().createElement("td", null, /*#__PURE__*/external_React_default().createElement(UseVendorButton, {
      vendor_code: (item.company || '').toUpperCase(),
      onSelectVendor: onSelectVendor
    })));
  })))))))));
};
var PartSearch = function PartSearch(_ref20) {
  var value = _ref20.value,
    _onChange5 = _ref20.onChange,
    onPartSelect = _ref20.onPartSelect,
    api_call = _ref20.api_call,
    readonly = _ref20.readonly,
    disabled = _ref20.disabled;
  var _useState37 = (0,external_React_namespaceObject.useState)(value || ''),
    _useState38 = _slicedToArray(_useState37, 2),
    searchTerm = _useState38[0],
    setSearchTerm = _useState38[1];
  var _useState39 = (0,external_React_namespaceObject.useState)([]),
    _useState40 = _slicedToArray(_useState39, 2),
    suggestions = _useState40[0],
    setSuggestions = _useState40[1];
  var _useState41 = (0,external_React_namespaceObject.useState)(false),
    _useState42 = _slicedToArray(_useState41, 2),
    showDropdown = _useState42[0],
    setShowDropdown = _useState42[1];
  var _useState43 = (0,external_React_namespaceObject.useState)(false),
    _useState44 = _slicedToArray(_useState43, 2),
    loading = _useState44[0],
    setLoading = _useState44[1];
  (0,external_React_namespaceObject.useEffect)(function () {
    setSearchTerm(value || '');
  }, [value]);
  var search_parts = /*#__PURE__*/function () {
    var _ref21 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee13(term) {
      var result, _t9;
      return _regenerator().w(function (_context13) {
        while (1) switch (_context13.n) {
          case 0:
            if (!(term.length < 2)) {
              _context13.n = 1;
              break;
            }
            setSuggestions([]);
            return _context13.a(2);
          case 1:
            setLoading(true);
            _context13.p = 2;
            _context13.n = 3;
            return api_call('list', 'JADVDATA_dbo_part_meta', {
              return_columns: ["part", "inventory_description"],
              order: [{
                column: 0,
                dir: 'asc'
              }],
              columns: [{
                name: 'part'
              }, {
                name: 'inventory_description'
              }],
              filters: {
                part: {
                  operator: "ilike",
                  value: "".concat(term, "%")
                }
              },
              start: 0,
              length: 20
            });
          case 3:
            result = _context13.v;
            if (result.success && result.data) {
              setSuggestions(result.data);
            } else {
              setSuggestions([]);
            }
            _context13.n = 5;
            break;
          case 4:
            _context13.p = 4;
            _t9 = _context13.v;
            console.error('Error searching parts:', _t9);
            setSuggestions([]);
          case 5:
            setLoading(false);
          case 6:
            return _context13.a(2);
        }
      }, _callee13, null, [[2, 4]]);
    }));
    return function search_parts(_x10) {
      return _ref21.apply(this, arguments);
    };
  }();
  (0,external_React_namespaceObject.useEffect)(function () {
    var timer = setTimeout(function () {
      if (searchTerm) {
        search_parts(searchTerm);
      } else {
        setSuggestions([]);
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
      var new_value = e.target.value;
      setSearchTerm(new_value);
      _onChange5(new_value);
      setShowDropdown(true);
    },
    onFocus: function onFocus() {
      setShowDropdown(true);
      if (searchTerm && suggestions.length === 0) {
        search_parts(searchTerm);
      }
    },
    onBlur: function onBlur() {
      return setTimeout(function () {
        return setShowDropdown(false);
      }, 200);
    },
    placeholder: "Search part...",
    readOnly: readonly,
    disabled: disabled
  }), showDropdown && !disabled && (searchTerm.length >= 2 || suggestions.length > 0) && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-menu d-block position-absolute w-100 mt-1",
    style: {
      maxHeight: '200px',
      overflowY: 'auto'
    }
  }, loading && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-item-text text-center"
  }, /*#__PURE__*/external_React_default().createElement("small", {
    className: "text-muted"
  }, "Searching parts...")), !loading && suggestions.length === 0 && searchTerm.length >= 2 && /*#__PURE__*/external_React_default().createElement("div", {
    className: "dropdown-item-text text-center"
  }, /*#__PURE__*/external_React_default().createElement("small", {
    className: "text-muted"
  }, "No parts found")), !loading && suggestions.map(function (part) {
    return /*#__PURE__*/external_React_default().createElement("button", {
      key: part.part,
      className: "dropdown-item",
      type: "button",
      onClick: function onClick() {
        onPartSelect(part);
        setSearchTerm(part.part);
        setShowDropdown(false);
        setSuggestions([]);
      }
    }, /*#__PURE__*/external_React_default().createElement("strong", null, part.part), part.inventory_description && /*#__PURE__*/external_React_default().createElement("div", {
      className: "small text-muted"
    }, part.inventory_description));
  })));
};
var ReceiveModal = function ReceiveModal(_ref22) {
  var lines = _ref22.lines,
    onClose = _ref22.onClose,
    onReceive = _ref22.onReceive;
  var _useState45 = useState(new Set()),
    _useState46 = _slicedToArray(_useState45, 2),
    selected = _useState46[0],
    setSelected = _useState46[1];
  var receivable_lines = lines.map(function (line, index) {
    return {
      line: line,
      index: index
    };
  }).filter(function (_ref23) {
    var line = _ref23.line;
    return parseFloat(line.rqty || line.received_qty || 0) === 0;
  });
  if (receivable_lines.length === 0) {
    return /*#__PURE__*/React.createElement("div", {
      className: "modal d-block",
      style: {
        backgroundColor: 'rgba(0,0,0,0.5)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "modal-dialog"
    }, /*#__PURE__*/React.createElement("div", {
      className: "modal-content"
    }, /*#__PURE__*/React.createElement("div", {
      className: "modal-header"
    }, /*#__PURE__*/React.createElement("h5", {
      className: "modal-title"
    }, "Receive Purchase Order Lines"), /*#__PURE__*/React.createElement("button", {
      type: "button",
      className: "btn-close",
      onClick: onClose
    })), /*#__PURE__*/React.createElement("div", {
      className: "modal-body"
    }, /*#__PURE__*/React.createElement("p", {
      className: "text-muted"
    }, "All lines have been received.")), /*#__PURE__*/React.createElement("div", {
      className: "modal-footer"
    }, /*#__PURE__*/React.createElement("button", {
      type: "button",
      className: "btn btn-secondary",
      onClick: onClose
    }, "Close")))));
  }
  var toggle_all = function toggle_all() {
    if (selected.size === receivable_lines.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(receivable_lines.map(function (_ref24) {
        var index = _ref24.index;
        return index;
      })));
    }
  };
  var toggle_line = function toggle_line(index) {
    var new_selected = new Set(selected);
    if (new_selected.has(index)) {
      new_selected["delete"](index);
    } else {
      new_selected.add(index);
    }
    setSelected(new_selected);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "modal d-block",
    style: {
      backgroundColor: 'rgba(0,0,0,0.5)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "modal-dialog modal-lg"
  }, /*#__PURE__*/React.createElement("div", {
    className: "modal-content"
  }, /*#__PURE__*/React.createElement("div", {
    className: "modal-header"
  }, /*#__PURE__*/React.createElement("h5", {
    className: "modal-title"
  }, "Receive Purchase Order Lines"), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "btn-close",
    onClick: onClose
  })), /*#__PURE__*/React.createElement("div", {
    className: "modal-body"
  }, /*#__PURE__*/React.createElement("p", {
    className: "text-muted"
  }, "Select which lines to receive. Each selected line will be fully received."), /*#__PURE__*/React.createElement("div", {
    className: "table-responsive"
  }, /*#__PURE__*/React.createElement("table", {
    className: "table"
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    width: "50"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    className: "form-check-input",
    checked: selected.size === receivable_lines.length,
    onChange: toggle_all
  })), /*#__PURE__*/React.createElement("th", null, "Line"), /*#__PURE__*/React.createElement("th", null, "Part"), /*#__PURE__*/React.createElement("th", null, "Description"), /*#__PURE__*/React.createElement("th", null, "Quantity"))), /*#__PURE__*/React.createElement("tbody", null, receivable_lines.map(function (_ref25) {
    var line = _ref25.line,
      index = _ref25.index;
    return /*#__PURE__*/React.createElement("tr", {
      key: index
    }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      className: "form-check-input",
      checked: selected.has(index),
      onChange: function onChange() {
        return toggle_line(index);
      }
    })), /*#__PURE__*/React.createElement("td", null, index + 1), /*#__PURE__*/React.createElement("td", null, line.pcode || line.part || ''), /*#__PURE__*/React.createElement("td", null, line.pdesc || line.description || ''), /*#__PURE__*/React.createElement("td", null, line.pqty || line.quantity || 0));
  }))))), /*#__PURE__*/React.createElement("div", {
    className: "modal-footer"
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "btn btn-secondary",
    onClick: onClose
  }, "Cancel"), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "btn btn-primary",
    onClick: function onClick() {
      return onReceive(Array.from(selected));
    },
    disabled: selected.size === 0
  }, "Receive Selected Lines (", selected.size, ")")))));
};
var RemoveLineButton = function RemoveLineButton(_ref26) {
  var onRemove = _ref26.onRemove;
  return /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-sm btn-danger",
    onClick: onRemove
  }, /*#__PURE__*/external_React_default().createElement(Trash2, {
    size: 16
  }));
};
var UseVendorButton = function UseVendorButton(_ref27) {
  var vendor_code = _ref27.vendor_code,
    onSelectVendor = _ref27.onSelectVendor;
  var handle_click = /*#__PURE__*/function () {
    var _ref28 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee14() {
      return _regenerator().w(function (_context14) {
        while (1) switch (_context14.n) {
          case 0:
            _context14.n = 1;
            return onSelectVendor(vendor_code);
          case 1:
            return _context14.a(2);
        }
      }, _callee14);
    }));
    return function handle_click() {
      return _ref28.apply(this, arguments);
    };
  }();
  return /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-sm btn-primary",
    onClick: handle_click
  }, "Use");
};
var AddLineButton = function AddLineButton(_ref29) {
  var onClick = _ref29.onClick,
    label = _ref29.label,
    Icon = _ref29.icon,
    disabled = _ref29.disabled;
  return /*#__PURE__*/external_React_default().createElement("button", {
    className: "btn btn-sm btn-primary",
    onClick: onClick,
    disabled: disabled
  }, /*#__PURE__*/external_React_default().createElement(Icon, {
    size: 16,
    className: "me-1"
  }), label);
};

// Helper functions
function get_default_header(config) {
  var today = new Date().toISOString().split('T')[0];
  var expected_date = new Date();
  expected_date.setDate(expected_date.getDate() + 2);
  return {
    vendor_code: '',
    vendor_name: '',
    order_date: today,
    expected_receipt_date: expected_date.toISOString().split('T')[0],
    location: config.location || 'TAC',
    entered_by: '',
    ordered_by_customer: '',
    terms: '',
    ship_via: 'UPS',
    freight: 0.0,
    subtotal: 0.0,
    tax_amount: 0.0,
    total: 0.0,
    printed: false,
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
function clean_po_data(data) {
  if (data.lines) {
    data.lines = data.lines.map(function (line) {
      // Clean null characters from messages
      if (line.msg) {
        var clean_msg = line.msg.split('\x00')[0].trim();
        line.msg = clean_msg;
      }
      if (line.message) {
        var clean_message = line.message.split('\x00')[0].trim();
        line.message = clean_message;
      }

      // Clean null characters from other fields
      ['gla', 'gldpta', 'tskcod', 'cat'].forEach(function (field) {
        if (line[field] && typeof line[field] === 'string') {
          line[field] = line[field].replace(/\x00/g, '').trim();
        }
      });

      // Ensure both message formats are populated
      if (line.message && !line.msg) {
        line.msg = line.message;
      } else if (line.msg && !line.message) {
        line.message = line.msg;
      }
      return line;
    });
  }
  return {
    header: data.header || {},
    lines: data.lines || [],
    source_info: data.source_info || {},
    expected_receipt_date: data.expected_receipt_date || ''
  };
}
function map_header_data(header) {
  // For existing POs, check if we already have the modern structure
  var has_modern_structure = header.billing && _typeof(header.billing) === 'object';
  return {
    vendor_code: header.vendor_code || header.vndcod || '',
    vendor_name: header.vendor_name || header.vndnme || '',
    order_date: format_date(header.order_date || header.orddte),
    expected_receipt_date: format_date(header.expected_receipt_date || header.erd),
    location: header.location || header.loc || 'TAC',
    entered_by: header.entered_by || header.entby || '',
    terms: header.terms || header.termd || '',
    ship_via: header.ship_via || header.shpvia || 'UPS',
    freight: parseFloat(header.freight || header.frght || 0),
    subtotal: parseFloat(header.subtotal || header.subtot || 0),
    tax_amount: parseFloat(header.tax_amount || header.taxamt || 0),
    total: parseFloat(header.total || 0),
    printed: header.printed || header.prtd === 'Y' || false,
    ordered_by_customer: header.ordered_by_customer || header.obycus || '',
    // Handle billing - use modern structure if available, otherwise map old fields
    billing: has_modern_structure && header.billing ? header.billing : {
      name: header.vendor_name || header.vndnme || '',
      address1: header.vnda1 || '',
      address2: header.vnda2 || '',
      city: header.vndcty || '',
      state: header.vndst || '',
      zip: header.vndzip || '',
      country: header.vndctry || 'USA'
    },
    // Handle shipping - use modern structure if available, otherwise map old fields
    shipping: has_modern_structure && header.shipping ? header.shipping : {
      name: header.shpnme || '',
      attention: header.shpatn || '',
      address1: header.shpa1 || '',
      address2: header.shpa2 || '',
      city: header.shpcty || '',
      state: header.shpst || '',
      zip: header.shpzip || '',
      country: header.shpctry || 'USA'
    }
  };
}
function format_date(date) {
  if (!date) return '';
  if (typeof date === 'string') return date;
  if (date.year && date.month && date.day) {
    var year = date.year;
    var month = String(date.month).padStart(2, '0');
    var day = String(date.day).padStart(2, '0');
    return "".concat(year, "-").concat(month, "-").concat(day);
  }
  return '';
}

// Add CSS styles
var styles = "\n    .hover-bg-light:hover {\n        background-color: #f8f9fa;\n    }\n    .cursor-pointer {\n        cursor: pointer;\n    }\n";

// Add styles to head
if (typeof document !== 'undefined') {
  var style_element = document.createElement('style');
  style_element.textContent = styles;
  document.head.appendChild(style_element);
}
/* harmony default export */ const user_components_PurchaseOrder = (PurchaseOrder);
window["components/PurchaseOrder"] = __webpack_exports__["default"];
/******/ })()
;
//# sourceMappingURL=PurchaseOrder.bundle.js.map