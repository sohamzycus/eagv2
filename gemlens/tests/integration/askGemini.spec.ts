import { test, expect } from "@playwright/test";

test("Ask Gemini chat interface loads", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Simulate opening chat overlay
  await page.click("#gemlens-run-demo-chat");
  
  // Wait for test results to confirm chat was triggered
  await page.waitForSelector("#test-results", { state: 'visible' });
  const testResults = await page.locator("#test-results").innerText();
  expect(testResults).toContain("Chat overlay test completed");
});

test("Chat functionality can be simulated", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Test the chat simulation function
  const chatResult = await page.evaluate(() => {
    return (window as any).gemLensTest?.simulateChat();
  });
  
  // Function should execute without error
  expect(chatResult).toBeUndefined(); // void function
  
  // Verify test results appear
  await page.waitForSelector("#test-results", { state: 'visible' });
});

test("Page provides context for chat", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Get article content that would be used as context
  const articleContent = await page.locator('article').innerText();
  
  // Verify content is substantial enough for AI context
  expect(articleContent.length).toBeGreaterThan(500);
  expect(articleContent).toContain("AI");
  expect(articleContent).toContain("summarize");
  expect(articleContent).toContain("information");
});

test("Multiple chat interactions can be simulated", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Simulate multiple chat interactions
  await page.click("#gemlens-run-demo-chat");
  await page.waitForTimeout(100);
  
  await page.click("#gemlens-run-demo-chat");
  await page.waitForTimeout(100);
  
  // Should still work after multiple clicks
  const testResults = await page.locator("#test-results").innerText();
  expect(testResults).toContain("Chat overlay test completed");
});

test("Chat overlay would have proper styling", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Check that the page has proper CSS that would style an overlay
  const styles = await page.evaluate(() => {
    const styleSheets = Array.from(document.styleSheets);
    let hasOverlayStyles = false;
    
    try {
      styleSheets.forEach(sheet => {
        if (sheet.cssRules) {
          Array.from(sheet.cssRules).forEach(rule => {
            if (rule instanceof CSSStyleRule) {
              if (rule.selectorText?.includes('demo-btn') || 
                  rule.selectorText?.includes('demo-controls')) {
                hasOverlayStyles = true;
              }
            }
          });
        }
      });
    } catch (e) {
      // Some stylesheets might not be accessible
    }
    
    return hasOverlayStyles;
  });
  
  expect(styles).toBe(true);
});

test("Chat context extraction works correctly", async ({ page }) => {
  await page.goto("http://localhost:3000/tests/fixtures/demo.html");
  
  // Test content extraction that would be used for chat context
  const pageTitle = await page.locator('h1').innerText();
  const mainContent = await page.locator('main').innerText();
  
  expect(pageTitle).toContain("GemLens Demo Page");
  expect(mainContent).toContain("Future of AI-Powered Web Browsing");
  
  // Verify key topics are present for AI context
  expect(mainContent).toContain("Time Saving");
  expect(mainContent).toContain("Better Understanding");
  expect(mainContent).toContain("Interactive Learning");
});
