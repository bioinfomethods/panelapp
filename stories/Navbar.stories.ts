import type { Meta, StoryObj } from "@storybook/web-components";

const meta: Meta = {
  component: "x-navbar",
  argTypes: {
    hideItems: {
      type: "boolean",
    },
    cognito: {
      type: "boolean",
    },
    username: {
      type: "string",
    },
    auth: {
      options: ["anonymous", "reviewer", "gel"],
      control: { type: "select" },
    },
  },
};

export default meta;
type Story = StoryObj;

export const Login: Story = {
  args: {
    hideItems: true,
  },
};

export const Anonymous: Story = {
  args: {
    auth: "anonymous",
  },
};

export const Reviewer: Story = {
  args: {
    auth: "reviewer",
    username: "User",
  },
};

export const Gel: Story = {
  args: {
    auth: "gel",
    username: "User",
  },
};
