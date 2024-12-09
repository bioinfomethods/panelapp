import type { Meta, StoryObj } from "@storybook/web-components";

const meta: Meta = {
  component: "x-rating-badge",
  argTypes: {
    rating: {
      options: ["green", "amber", "red", "grey"],
      control: {
        type: "select",
      },
    },
    ready: {
      type: "boolean",
    },
    block: {
      type: "boolean",
    },
    text: {
      options: ["short", "verbose"],
      control: {
        type: "select",
      },
    },
  },
};

export default meta;
type Story = StoryObj;

export const Green: Story = {
  args: {
    rating: "green",
  },
};

export const Amber: Story = {
  args: {
    rating: "amber",
  },
};

export const Red: Story = {
  args: {
    rating: "red",
  },
};

export const Grey: Story = {
  args: {
    rating: "grey",
  },
};

export const Ready: Story = {
  args: {
    rating: "green",
    ready: true,
  },
};

export const Block: Story = {
  args: {
    rating: "green",
    block: true,
  },
};
