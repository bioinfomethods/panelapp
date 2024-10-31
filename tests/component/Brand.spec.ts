import { expect, test } from "@sand4rt/experimental-ct-web";
import Brand from "../../frontend/components/Brand";

test.describe("visual", () => {
  test("primary", async ({ mount }) => {
    const component = await mount(Brand, { props: { title: "PanelApp" } });
    await expect(component).toHaveScreenshot();
  });
});
