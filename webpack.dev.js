const path = require("path");
const { merge } = require("webpack-merge");
const common = require("./webpack.common.js");

// TODO: https://stackoverflow.com/a/58040422
module.exports = merge(common, {
  mode: "development",
  devtool: "inline-source-map",
  devServer: {
    static: {
      directory: path.join(__dirname, "dist"),
    },
  },
});
