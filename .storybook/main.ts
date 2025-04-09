import type { StorybookConfig } from "@storybook/web-components-webpack5";
import webpack from "webpack";

const config: StorybookConfig = {
  stories: [
    "../stories/**/*.mdx",
    "../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)",
  ],
  addons: [
    "@storybook/addon-webpack5-compiler-swc",
    "@storybook/addon-essentials",
    "@chromatic-com/storybook",
    "@storybook/addon-styling-webpack",
    "@storybook/addon-a11y"
  ],
  framework: {
    name: "@storybook/web-components-webpack5",
    options: {},
  },
  webpackFinal: (config) => {
    config.module?.rules?.push({
      test: /\.scss$/,
      use: ["style-loader", "css-loader", "postcss-loader", "sass-loader"],
    });
    config.module?.rules?.push({
      test: /\.tsx?$/,
      use: "ts-loader",
      exclude: "/node_modules/",
    });

    config.plugins?.push(
      new webpack.ProvidePlugin({
        $: "jquery/src/jquery",
        jQuery: "jquery/src/jquery",
      })
    );

    return config;
  },
};
export default config;
