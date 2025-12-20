const { test, expect } = require('@playwright/test');

test('homepage has been updated', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Wait for the canvas to be visible
  await page.waitForSelector('#canvas-container canvas');

  // Take a screenshot
  await page.screenshot({ path: '/home/jules/verification/index.png' });
});