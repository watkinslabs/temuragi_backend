module.exports = {
  "mode": "production",
  "entry": {
    "DefaultLayout": "/web/ahoy2.radiatorusa.com/react/src/components/dynamic/DefaultLayout.js",
    "PurchaseOrderBuilder": "/web/ahoy2.radiatorusa.com/react/src/components/dynamic/PurchaseOrderBuilder.js"
  },
  "output": {
    "path": "/web/ahoy2.radiatorusa.com/app/static/js/components",
    "filename": "[name].bundle.js",
    "library": [
      "Components",
      "[name]"
    ],
    "libraryTarget": "window"
  },
  "module": {
    "rules": [
      {
        "test": {},
        "exclude": {},
        "use": {
          "loader": "babel-loader",
          "options": {
            "presets": [
              "@babel/preset-react"
            ]
          }
        }
      }
    ]
  },
  "externals": {
    "react": "React",
    "react-dom": "ReactDOM",
    "react-router-dom": "ReactRouterDOM"
  }
};