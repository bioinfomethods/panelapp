const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const path = require("path");
const webpack = require("webpack");
const BundleTracker = require("webpack-bundle-tracker");

module.exports = {
  entry: "./frontend/panel_app.ts",
  output: {
    filename: "app.js",
    path: path.resolve(__dirname, "dist"),
    clean: true,
    filename: "[contenthash].js",
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "[contenthash].css",
    }),
    new webpack.ProvidePlugin({
      $: "jquery/src/jquery",
      jQuery: "jquery/src/jquery",
    }),
    new BundleTracker({ path: __dirname, filename: "webpack-stats.json" }),
  ],
  resolve: {
    extensions: [".tsx", ".ts", ".js"],
    alias: {
      "@": path.resolve("./frontend"),
    },
  },
  module: {
    rules: [
      // https://getbootstrap.com/docs/5.3/getting-started/webpack/#extracting-svg-files
      // Necessary to have a Content Security Policy without wildcards due to embedded svgs
      {
        mimetype: "image/svg+xml",
        scheme: "data",
        type: "asset/resource",
        generator: {
          filename: "icon/[contenthash].svg",
        },
      },
      {
        test: /\.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          // Interprets `@import` and `url()` like `import/require()` and will resolve them
          { loader: "css-loader", options: { sourceMap: true } },
          {
            // Loader for webpack to process CSS with PostCSS
            loader: "postcss-loader",
            options: {
              postcssOptions: {
                plugins: () => [autoprefixer],
              },
            },
          },
          {
            // Loads a SASS/SCSS file and compiles it to CSS
            loader: "sass-loader",
          },
        ],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: "asset/resource",
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: "asset/resource",
      },
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: "/node_modules/",
      },
    ],
  },
};
