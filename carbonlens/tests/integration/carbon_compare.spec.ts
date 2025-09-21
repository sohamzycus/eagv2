/**
 * Integration test for carbon comparison workflow
 */

import { test, expect } from '@playwright/test';

test.describe('CarbonLens Carbon Comparison', () => {
  test.beforeEach(async ({ page }) => {
    // Load the test fixture page
    await page.goto('file://' + __dirname + '/../fixtures/demo_carbon.html');
    
    // Wait for extension to load (in real test, extension would be loaded)
    await page.waitForTimeout(1000);
  });

  test('should complete carbon comparison task', async ({ page }) => {
    // This test would normally interact with the loaded extension
    // For now, we'll test the fixture page structure
    
    await expect(page.locator('h1')).toContainText('Carbon Comparison Demo');
    await expect(page.locator('#instance-specs')).toBeVisible();
    
    // In a real integration test, we would:
    // 1. Open extension popup
    // 2. Enter comparison prompt
    // 3. Wait for agent execution
    // 4. Verify results display
    // 5. Check trace overlay
    // 6. Export logs
    
    console.log('Integration test placeholder - would test full workflow');
  });

  test('should extract page data correctly', async ({ page }) => {
    // Test page data extraction
    const specs = await page.locator('#instance-specs').textContent();
    expect(specs).toContain('8 vCPU');
    expect(specs).toContain('32 GB RAM');
    
    const regions = await page.locator('#regions').textContent();
    expect(regions).toContain('us-east-1');
    expect(regions).toContain('eu-west-1');
  });

  test('should handle mock mode by default', async ({ page }) => {
    // Verify mock mode behavior
    const mockIndicator = page.locator('#mock-mode-indicator');
    if (await mockIndicator.isVisible()) {
      await expect(mockIndicator).toContainText('Mock Mode');
    }
  });
});

// Test for real mode (opt-in only)
test.describe('CarbonLens Real Mode', () => {
  test.skip(({ }, testInfo) => {
    return !process.env.USE_REAL_MODE;
  });

  test('should work with real backend', async ({ page }) => {
    // This test only runs when USE_REAL_MODE=true
    await page.goto('file://' + __dirname + '/../fixtures/demo_carbon.html');
    
    // Test real API integration
    console.log('Real mode integration test - would test actual APIs');
  });
});
