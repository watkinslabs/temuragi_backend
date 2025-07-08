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
  "default": () => (/* binding */ user_components_ParkedOrders)
});

;// external "React"
const external_React_namespaceObject = window["React"];
var external_React_default = /*#__PURE__*/__webpack_require__.n(external_React_namespaceObject);
;// ./src/user_components/ParkedOrders.js
/**
 * @routes ["ParkedOrders"]
*/


var ParkedOrders = function ParkedOrders() {
  var _window$Components;
  // Use the global ServerDataTable directly
  var ServerDataTable = (_window$Components = window.Components) === null || _window$Components === void 0 ? void 0 : _window$Components.ServerDataTable;
  if (!ServerDataTable) {
    console.error('ServerDataTable not found in window.Components:', window.Components);
    return /*#__PURE__*/external_React_default().createElement("div", null, "Error: ServerDataTable component not found");
  }
  return /*#__PURE__*/external_React_default().createElement(ServerDataTable, {
    report_id: "fb2d204e-5943-43b2-a20b-fe19fb1d1853"
  });
};
/* harmony default export */ const user_components_ParkedOrders = (ParkedOrders);
window["components/ParkedOrders"] = __webpack_exports__["default"];
/******/ })()
;
//# sourceMappingURL=ParkedOrders.bundle.js.map