import type { Preview } from "@storybook/web-components";
import "../frontend/panel_app";
import "../frontend/panel_app.scss";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
};

export default preview;
