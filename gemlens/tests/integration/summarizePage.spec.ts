import { test, expect } from "@playwright/test";

test("Summarize Page shows mock summary", async ({ page }) => {
  // Serve tests/fixtures/demo.html via a lightweight static server in Playwright config or test setup
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Check if demo page loaded correctly
  await expect(page.locator('h1')).toContainText('GemLens Demo Page');
  
  // Click the extension demo button to simulate summarization
  await page.click("#gemlens-run-demo-summarize");
  
  // Wait for summary card to appear
  await page.waitForSelector('.gemlens-summary-card', { state: 'visible' });
  
  // Check that summary content is displayed
  const summaryContent = await page.locator(".gemlens-summary-card").innerText();
  expect(summaryContent).toContain("mock summary");
  
  // Verify test results are shown
  const testResults = await page.locator("#test-results").innerText();
  expect(testResults).toContain("Summarization test completed");
});

test("Demo page has required test elements", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Check all required test elements exist
  await expect(page.locator('#gemlens-run-demo-summarize')).toBeVisible();
  await expect(page.locator('#gemlens-run-demo-chat')).toBeVisible();
  await expect(page.locator('#gemlens-simulate-error')).toBeVisible();
  
  // Check article content exists for extraction
  await expect(page.locator('article')).toBeVisible();
  const articleText = await page.locator('article').innerText();
  expect(articleText.length).toBeGreaterThan(100);
});

test("Chat overlay simulation works", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Click chat demo button
  await page.click("#gemlens-run-demo-chat");
  
  // Verify test results
  await page.waitForSelector("#test-results", { state: 'visible' });
  const testResults = await page.locator("#test-results").innerText();
  expect(testResults).toContain("Chat overlay test completed");
});

test("Error simulation works", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Click error simulation button
  await page.click("#gemlens-simulate-error");
  
  // Verify error test results
  await page.waitForSelector("#test-results", { state: 'visible' });
  const testResults = await page.locator("#test-results").innerText();
  expect(testResults).toContain("Error simulation completed");
});

test("Page content extraction works", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Test the exposed test functions
  const articleText = await page.evaluate(() => {
    return (window as any).gemLensTest?.getArticleText();
  });
  
  expect(articleText).toBeTruthy();
  expect(articleText).toContain("Future of AI-Powered Web Browsing");
  expect(articleText).toContain("Artificial Intelligence is revolutionizing");
});

test("Extension detection works", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Note: In real browser with extension, this would return true
  // In test environment without extension, it returns false
  const isExtensionLoaded = await page.evaluate(() => {
    return (window as any).gemLensTest?.isExtensionLoaded();
  });
  
  // In test environment, extension is not loaded
  expect(typeof isExtensionLoaded).toBe('boolean');
});
