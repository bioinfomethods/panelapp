import { expect, test } from "@sand4rt/experimental-ct-web";
import HomePages from "../../frontend/components/HomePages";

test.describe("visual", () => {
  test("primary", async ({ mount }) => {
    const component = await mount(HomePages, {
      props: { active: "Introduction" },
    });
    await expect(component).toHaveScreenshot();
  });
});

test("change page", async ({ mount }) => {
  const component = await mount(HomePages, {
    props: { active: "Introduction" },
    slots: {
      Introduction: "<div>This is the introduction</div>",
      News: "<div>This is the news</div>",
    },
  });

  await expect(component.getByText("This is the introduction")).toBeVisible();
  await expect(component.getByText("This is the news")).not.toBeVisible();

  await component.getByRole("link", { name: "News" }).click();

  await expect(
    component.getByText("This is the introduction")
  ).not.toBeVisible();
  await expect(component.getByText("This is the news")).toBeVisible();
});
