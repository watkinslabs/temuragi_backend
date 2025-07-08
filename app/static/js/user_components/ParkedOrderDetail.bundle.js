// Ensure window.Components exists
window.Components = window.Components || {};
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	// The require scope
/******/ 	var __webpack_require__ = {};
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
/************************************************************************/
var __webpack_exports__ = {};
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
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
/**
 * @routes ["ParkedOrderDetail"]
*/

var ParkedOrderDetail = function ParkedOrderDetail() {
  // Get React from window
  var React = window.React;
  var useState = React.useState,
    useEffect = React.useEffect;

  // Get hooks from window
  var useNavigation = window.useNavigation;
  var useSite = window.useSite;
  var config = window.config;

  // State
  var _useState = useState(true),
    _useState2 = _slicedToArray(_useState, 2),
    loading = _useState2[0],
    set_loading = _useState2[1];
  var _useState3 = useState(null),
    _useState4 = _slicedToArray(_useState3, 2),
    order = _useState4[0],
    set_order = _useState4[1];
  var _useState5 = useState(null),
    _useState6 = _slicedToArray(_useState5, 2),
    error = _useState6[0],
    set_error = _useState6[1];

  // Now use the hooks
  var _useNavigation = useNavigation(),
    navigate_to = _useNavigation.navigate_to,
    view_params = _useNavigation.view_params;
  var _useSite = useSite(),
    current_context = _useSite.current_context;

  // Get the order_id from view_params
  var order_id = view_params === null || view_params === void 0 ? void 0 : view_params.id;

  // Load order data
  useEffect(function () {
    var load_order = /*#__PURE__*/function () {
      var _ref = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
        var response, data, _t;
        return _regenerator().w(function (_context) {
          while (1) switch (_context.n) {
            case 0:
              _context.p = 0;
              set_loading(true);
              _context.n = 1;
              return config.apiCall('/v2/api/data', {
                method: 'POST',
                headers: config.getAuthHeaders(),
                body: JSON.stringify({
                  model: 'ParkedOrderDetails',
                  operation: 'get',
                  company: 'PACIFIC',
                  pr_repair_order_id: order_id
                })
              });
            case 1:
              response = _context.v;
              if (response.ok) {
                _context.n = 2;
                break;
              }
              throw new Error('Failed to load order details');
            case 2:
              _context.n = 3;
              return response.json();
            case 3:
              data = _context.v;
              if (!data.success) {
                _context.n = 4;
                break;
              }
              set_order(data.order);
              _context.n = 5;
              break;
            case 4:
              throw new Error(data.error || 'Failed to load order');
            case 5:
              _context.n = 7;
              break;
            case 6:
              _context.p = 6;
              _t = _context.v;
              console.error('Error loading order:', _t);
              set_error(_t.message);
            case 7:
              _context.p = 7;
              set_loading(false);
              return _context.f(7);
            case 8:
              return _context.a(2);
          }
        }, _callee, null, [[0, 6, 7, 8]]);
      }));
      return function load_order() {
        return _ref.apply(this, arguments);
      };
    }();
    if (order_id) {
      // Only load if we have an order_id
      load_order();
    }
  }, [order_id, current_context]);

  // Handle navigation actions
  var handle_create_po = function handle_create_po(part) {
    navigate_to('PurchaseOrder', {
      line: part.line,
      order: order.order_info.pr_repair_order_id,
      warehouse_code: order.closest_warehouse.code,
      mode: 'parked_order_populate'
    });
  };
  var handle_view_po = function handle_view_po(po_number) {
    navigate_to('PurchaseOrder', {
      po_number: po_number,
      mode: 'view',
      order: order.order_info.pr_repair_order_id
    });
  };
  var handle_view_so = function handle_view_so(so_number) {
    navigate_to('SalesOrderDetail', {
      so_number: so_number,
      mode: 'view',
      from: {
        view: "ParkedOrderDetails",
        order_id: order.order_info.pr_repair_order_id
      }
    });
  };
  var handle_back_to_list = function handle_back_to_list() {
    navigate_to('ParkedOrders');
  };

  // Get part status badge
  var get_part_status_badge = function get_part_status_badge(part) {
    if (part.status === 'FULLY_INVOICED') {
      return /*#__PURE__*/React.createElement("span", {
        className: "badge bg-success"
      }, "FULLY INVOICED");
    } else if (part.quantity_ordered > 0 && part.quantity_ordered < part.quantity_needed) {
      return /*#__PURE__*/React.createElement("span", {
        className: "badge bg-warning"
      }, "PARTIAL");
    } else if (part.quantity_ordered === 0) {
      return /*#__PURE__*/React.createElement("span", {
        className: "badge bg-danger"
      }, "NOT ORDERED");
    } else {
      return /*#__PURE__*/React.createElement("span", {
        className: "badge bg-secondary"
      }, part.status);
    }
  };
  if (loading) {
    return /*#__PURE__*/React.createElement("div", {
      className: "d-flex justify-content-center align-items-center",
      style: {
        minHeight: '400px'
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center"
    }, /*#__PURE__*/React.createElement("div", {
      className: "spinner-border text-primary mb-3",
      role: "status"
    }, /*#__PURE__*/React.createElement("span", {
      className: "visually-hidden"
    }, "Loading...")), /*#__PURE__*/React.createElement("p", null, "Loading order details...")));
  }
  if (error) {
    return /*#__PURE__*/React.createElement("div", {
      className: "container-fluid"
    }, /*#__PURE__*/React.createElement("div", {
      className: "alert alert-danger"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fas fa-exclamation-circle me-2"
    }), error));
  }
  if (!order) {
    return /*#__PURE__*/React.createElement("div", {
      className: "container-fluid"
    }, /*#__PURE__*/React.createElement("div", {
      className: "alert alert-warning"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fas fa-exclamation-triangle me-2"
    }), "No order data found"));
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "container-fluid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/React.createElement("h1", {
    className: "h2"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-clipboard-list me-3"
  }), "Parked Order #", order.order_info.pt_order_id))), /*#__PURE__*/React.createElement("div", {
    className: "row mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/React.createElement("h5", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-file-alt me-2"
  }), "Order Information")), /*#__PURE__*/React.createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/React.createElement("table", {
    className: "table table-sm table-borderless mb-0"
  }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
    className: "text-muted small"
  }, "Parts Trader Order"), /*#__PURE__*/React.createElement("td", {
    className: "fw-bold text-end"
  }, order.order_info.pt_order_id)), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
    className: "text-muted small"
  }, "Performance Radiator RO"), /*#__PURE__*/React.createElement("td", {
    className: "fw-bold text-end"
  }, "#", order.order_info.pr_repair_order_id)), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
    className: "text-muted small"
  }, "Status"), /*#__PURE__*/React.createElement("td", {
    className: "fw-bold text-end"
  }, order.order_info.status)), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
    className: "text-muted small"
  }, "Created Date"), /*#__PURE__*/React.createElement("td", {
    className: "fw-bold text-end"
  }, order.order_info.created_at))))))), /*#__PURE__*/React.createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/React.createElement("h5", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-building me-2"
  }), "Performance Radiator Customer")), /*#__PURE__*/React.createElement("div", {
    className: "card-body"
  }, order.customer ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "customer-section mb-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "customer-details"
  }, /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, /*#__PURE__*/React.createElement("strong", null, order.customer.name)), /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, order.customer.address_1), order.customer.address_2 && /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, order.customer.address_2), /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, order.customer.city, ", ", order.customer.state, " ", order.customer.zip), /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-muted"
  }, "Customer Code:"), ' ', /*#__PURE__*/React.createElement("strong", null, order.customer.customer_code)), order.customer.phone && /*#__PURE__*/React.createElement("p", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-phone me-2 text-muted"
  }), /*#__PURE__*/React.createElement("a", {
    href: "tel:".concat(order.customer.phone)
  }, order.customer.phone)))), /*#__PURE__*/React.createElement("hr", {
    className: "my-3"
  }), order.closest_warehouse ? /*#__PURE__*/React.createElement("div", {
    className: "warehouse-section"
  }, /*#__PURE__*/React.createElement("h6", {
    className: "text-muted small mb-2"
  }, "Customer Assigned Location"), /*#__PURE__*/React.createElement("div", {
    className: "warehouse-details"
  }, /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, /*#__PURE__*/React.createElement("strong", null, order.closest_warehouse.name, " (", order.closest_warehouse.code, ")")), /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, order.closest_warehouse.address), /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, order.closest_warehouse.city, ", ", order.closest_warehouse.state, ' ', order.closest_warehouse.zip), order.closest_warehouse.distance_miles && /*#__PURE__*/React.createElement("p", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-muted"
  }, "Distance:"), ' ', /*#__PURE__*/React.createElement("strong", null, order.closest_warehouse.distance_miles, " miles")))) : /*#__PURE__*/React.createElement("div", {
    className: "alert alert-warning mb-0"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-exclamation-triangle me-2"
  }), /*#__PURE__*/React.createElement("strong", null, "No warehouse assigned"))) : /*#__PURE__*/React.createElement("div", {
    className: "alert alert-danger"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-exclamation-circle me-2"
  }), /*#__PURE__*/React.createElement("strong", null, "NEEDS CUSTOMER MAPPING"), /*#__PURE__*/React.createElement("p", {
    className: "mb-0 mt-2 small"
  }, "Customer information is missing. PO creation is disabled until customer is mapped."))))), /*#__PURE__*/React.createElement("div", {
    className: "col-md-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/React.createElement("h5", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-user me-2"
  }), "PartsTrader Customer")), /*#__PURE__*/React.createElement("div", {
    className: "card-body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "col-md-12"
  }, /*#__PURE__*/React.createElement("div", {
    className: "repairer-section mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "repairer-details"
  }, /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, /*#__PURE__*/React.createElement("strong", null, order.repairer.name)), /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, order.repairer.address), order.repairer.address2 && /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, order.repairer.address2), /*#__PURE__*/React.createElement("p", {
    className: "mb-2"
  }, order.repairer.city, ", ", order.repairer.state_province, ",", ' ', order.repairer.postal_code), /*#__PURE__*/React.createElement("p", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-muted"
  }, "Customer Code:"), ' ', /*#__PURE__*/React.createElement("strong", null, order.repairer.customer_code)))), /*#__PURE__*/React.createElement("div", {
    className: "requester-section"
  }, /*#__PURE__*/React.createElement("div", {
    className: "requester-details"
  }, /*#__PURE__*/React.createElement("p", {
    className: "mb-2"
  }, /*#__PURE__*/React.createElement("strong", null, order.requester.name)), /*#__PURE__*/React.createElement("p", {
    className: "mb-1"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-envelope me-2 text-muted"
  }), /*#__PURE__*/React.createElement("a", {
    href: "mailto:".concat(order.requester.email)
  }, order.requester.email)), /*#__PURE__*/React.createElement("p", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-phone me-2 text-muted"
  }), /*#__PURE__*/React.createElement("a", {
    href: "tel:".concat(order.requester.phone)
  }, order.requester.phone)))))))))), /*#__PURE__*/React.createElement("div", {
    className: "row mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/React.createElement("div", {
    className: "alert alert-info"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-info-circle me-2"
  }), /*#__PURE__*/React.createElement("strong", null, "Order Summary:"), ' ', "Total Parts: ", order.order_summary.total_parts, " |", ' ', "POs Created: ", order.order_summary.total_pos_created, order.order_summary.parts_fully_ordered > 0 && /*#__PURE__*/React.createElement(React.Fragment, null, " | Fully Ordered: ", order.order_summary.parts_fully_ordered), order.order_summary.parts_partially_ordered > 0 && /*#__PURE__*/React.createElement(React.Fragment, null, " | Partially Ordered: ", order.order_summary.parts_partially_ordered), order.order_summary.parts_not_ordered > 0 && /*#__PURE__*/React.createElement(React.Fragment, null, " | Not Ordered: ", order.order_summary.parts_not_ordered)))), /*#__PURE__*/React.createElement("div", {
    className: "row mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "card-header"
  }, /*#__PURE__*/React.createElement("h5", {
    className: "mb-0"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-boxes me-2"
  }), "Parts Details")), /*#__PURE__*/React.createElement("div", {
    className: "card-body p-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "table-responsive"
  }, /*#__PURE__*/React.createElement("table", {
    className: "table table-hover mb-0"
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Line"), /*#__PURE__*/React.createElement("th", null, "Part Number"), /*#__PURE__*/React.createElement("th", null, "Description"), /*#__PURE__*/React.createElement("th", {
    className: "text-center"
  }, "Qty"), /*#__PURE__*/React.createElement("th", null, "Status"), /*#__PURE__*/React.createElement("th", null, "Action"))), /*#__PURE__*/React.createElement("tbody", null, order.parts.map(function (part) {
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: part.line
    }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, part.line), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("strong", null, part.part_number)), /*#__PURE__*/React.createElement("td", null, part.description || 'N/A'), /*#__PURE__*/React.createElement("td", {
      className: "text-center"
    }, part.quantity_needed), /*#__PURE__*/React.createElement("td", null, get_part_status_badge(part)), /*#__PURE__*/React.createElement("td", null, part.quantity_ordered < part.quantity_needed && /*#__PURE__*/React.createElement(React.Fragment, null, order.customer && order.closest_warehouse ? /*#__PURE__*/React.createElement("button", {
      className: "btn btn-sm btn-success",
      onClick: function onClick() {
        return handle_create_po(part);
      }
    }, /*#__PURE__*/React.createElement("i", {
      className: "fas fa-plus me-1"
    }), "Create PO") : /*#__PURE__*/React.createElement("button", {
      className: "btn btn-sm btn-danger",
      disabled: true,
      title: "Customer mapping required"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fas fa-exclamation-circle me-1"
    }), "No Customer")))), part.purchase_orders && part.purchase_orders.map(function (po) {
      return /*#__PURE__*/React.createElement("tr", {
        key: "po-".concat(po.po_number),
        className: "table-secondary"
      }, /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", {
        colSpan: "5"
      }, /*#__PURE__*/React.createElement("i", {
        className: "fas fa-level-up-alt me-2"
      }), /*#__PURE__*/React.createElement("strong", null, "PO #", po.po_number), " - Quantity: ", po.quantity, /*#__PURE__*/React.createElement("button", {
        className: "btn btn-sm btn-outline-primary ms-3",
        onClick: function onClick() {
          return handle_view_po(po.po_number);
        }
      }, /*#__PURE__*/React.createElement("i", {
        className: "fas fa-eye me-1"
      }), "View PO")));
    }), part.sales_orders && part.sales_orders.map(function (so) {
      return /*#__PURE__*/React.createElement("tr", {
        key: "so-".concat(so.so_number),
        className: "table-info"
      }, /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", {
        colSpan: "5"
      }, /*#__PURE__*/React.createElement("i", {
        className: "fas fa-level-up-alt me-2"
      }), /*#__PURE__*/React.createElement("strong", null, "SO #", so.so_number), " - Quantity: ", so.quantity, " | Status: ", so.status, so.inv_number && so.inv_number !== 999999 && /*#__PURE__*/React.createElement(React.Fragment, null, " | Invoice #", so.inv_number), /*#__PURE__*/React.createElement("button", {
        className: "btn btn-sm btn-outline-info ms-3",
        onClick: function onClick() {
          return handle_view_so(so.so_number);
        }
      }, /*#__PURE__*/React.createElement("i", {
        className: "fas fa-eye me-1"
      }), "View SO")));
    }));
  })))))))), /*#__PURE__*/React.createElement("div", {
    className: "row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "col-12"
  }, /*#__PURE__*/React.createElement("button", {
    className: "btn btn-secondary",
    onClick: handle_back_to_list
  }, /*#__PURE__*/React.createElement("i", {
    className: "fas fa-arrow-left me-2"
  }), "Back to List"))));
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (ParkedOrderDetail);
window["components/ParkedOrderDetail"] = __webpack_exports__["default"];
/******/ })()
;
//# sourceMappingURL=ParkedOrderDetail.bundle.js.map