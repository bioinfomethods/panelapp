import type { Meta, StoryObj } from "@storybook/web-components";
import { html } from "lit";

const meta: Meta = {
  component: "x-home-pages",
  argTypes: {
    active: {
      options: [
        "Introduction",
        "News",
        "Navigating",
        "Reviewers",
        "Guidelines",
        "API",
        "FAQs",
        "Content",
      ],
      control: { type: "select" },
    },
  },
  render: ({ active }) => html`
    <x-home-pages active="${active}">
      <div slot="Introduction">Introduction</div>
      <div slot="News">News</div>
      <div slot="Navigating">Navigating</div>
      <div slot="Reviewers">Reviewers</div>
      <div slot="Guidelines">Guidelines</div>
      <div slot="API">API</div>
      <div slot="FAQs">FAQs</div>
      <div slot="Content">Content</div>
    </x-home-pages>
  `,
};

export default meta;
type Story = StoryObj;

export const Primary: Story = {
  args: {
    active: "Introduction",
  },
};
