import { expect, test } from "@sand4rt/experimental-ct-web";
import Navbar from "../../frontend/components/Navbar";

test.describe("visual", () => {
  test("anonymous", async ({ mount }) => {
    const component = await mount(Navbar, { props: { auth: "anonymous" } });
    await expect(component).toHaveScreenshot();
  });

  test("reviewer", async ({ mount }) => {
    const component = await mount(Navbar, {
      props: { auth: "reviewer", username: "test" },
    });
    await expect(component).toHaveScreenshot();
  });

  test("gel", async ({ mount }) => {
    const component = await mount(Navbar, {
      props: { auth: "gel", username: "test" },
    });
    await expect(component).toHaveScreenshot();
  });

  test("login", async ({ mount }) => {
    const component = await mount(Navbar, {
      props: { hideItems: true },
    });
    await expect(component).toHaveScreenshot();
  });

  test("link hover", async ({ mount, page }) => {
    const component = await mount(Navbar, {
      props: { auth: "gel", username: "test" },
    });

    await page.getByRole("link", { name: "Panels" }).hover();

    await expect(component).toHaveScreenshot();
  });
});
