// Auto-generated Playwright JavaScript test script
// This script uses Playwright's high-level APIs with automatic waiting
// All elements are located by ID or class name with proper handling for duplicates
const { chromium } = require('playwright');

async function runTests() {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    let lastError = null;

    try {

        // Initial Navigation: Load the base page
        console.log("Initial: Navigating to https://www.amazon.in...");
        try {
            await page.goto("https://www.amazon.in", { waitUntil: "load", timeout: 30000 });
            await page.waitForTimeout(1000);
            console.log("  [OK] Page loaded successfully");
        } catch (error) {
            console.warn("  [WARN] Page load warning: " + error.message + " (continuing anyway)");
        }

        // Step 0: Wait for element
        console.log("Step 0: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 0: " + error.message);
        }
        // Step 1: Click on element
        console.log("Step 1: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(0);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 1: " + error.message);
        }
        // Step 2: Click on element
        console.log("Step 2: Clicking on element...");
        try {
            const locator = page.locator('.nav-search-dropdown').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 2: " + error.message);
        }
        // Step 3: Click on element
        console.log("Step 3: Clicking on element...");
        try {
            const locator = page.locator('#nav_cs_3').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 3: " + error.message);
        }
        // Step 4: Wait for element
        console.log("Step 4: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 4: " + error.message);
        }
        // Step 5: Click on element
        console.log("Step 5: Clicking on element...");
        try {
            const locator = page.locator('.hm-icon-label').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 5: " + error.message);
        }
        // Step 6: Click on element
        console.log("Step 6: Clicking on element...");
        try {
            const locator = page.locator('#hmenu-customer-profile').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 6: " + error.message);
        }
        // Step 7: Click on element
        console.log("Step 7: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(1);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 7: " + error.message);
        }
        // Step 8: Click on element
        console.log("Step 8: Clicking on element...");
        try {
            const locator = page.locator('.s-heavy').nth(0);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 8: " + error.message);
        }
        // Step 9: Wait for element
        console.log("Step 9: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 9: " + error.message);
        }
        // Step 10: Wait for element
        console.log("Step 10: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 10: " + error.message);
        }
        // Step 11: Click on element
        console.log("Step 11: Clicking on element...");
        try {
            const locator = page.locator('.sc-fba-badge').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 11: " + error.message);
        }
        // Step 12: Click on element
        console.log("Step 12: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(2);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 12: " + error.message);
        }
        // Step 13: Click on element
        console.log("Step 13: Clicking on element...");
        try {
            const locator = page.locator('.s-heavy').nth(1);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 13: " + error.message);
        }
        // Step 14: Wait for element
        console.log("Step 14: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 14: " + error.message);
        }
        // Step 15: Click on element
        console.log("Step 15: Clicking on element...");
        try {
            const locator = page.locator('.s-image').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 15: " + error.message);
        }
        // Step 16: Wait for element
        console.log("Step 16: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 16: " + error.message);
        }
        // Step 17: Click on element
        console.log("Step 17: Clicking on element...");
        try {
            const locator = page.locator('[name=\'3\']').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 17: " + error.message);
        }
        // Step 18: Wait for element
        console.log("Step 18: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 18: " + error.message);
        }
        // Step 19: Click on element
        console.log("Step 19: Clicking on element...");
        try {
            const locator = page.locator('#add-to-cart-button').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 19: " + error.message);
        }
        // Step 20: Wait for element
        console.log("Step 20: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 20: " + error.message);
        }
        // Step 21: Wait for element
        console.log("Step 21: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 21: " + error.message);
        }
        // Step 22: Click on element
        console.log("Step 22: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(3);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 22: " + error.message);
        }
        // Step 23: Click on element
        console.log("Step 23: Clicking on element...");
        try {
            const locator = page.locator('.s-suggestion').nth(0);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 23: " + error.message);
        }
        // Step 24: Wait for element
        console.log("Step 24: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 24: " + error.message);
        }
        // Step 25: Click on element
        console.log("Step 25: Clicking on element...");
        try {
            const locator = page.locator('#ax-atc-EUIC_AddToCart_Search-content').nth(0);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 25: " + error.message);
        }
        // Step 26: Click on element
        console.log("Step 26: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(4);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 26: " + error.message);
        }
        // Step 27: Fill input field
        console.log("Step 27: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(5);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 27: " + error.message);
        }
        // Step 28: Click on element
        console.log("Step 28: Clicking on element...");
        try {
            const locator = page.locator('.s-heavy').nth(2);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 28: " + error.message);
        }
        // Step 29: Wait for element
        console.log("Step 29: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 29: " + error.message);
        }
        // Step 30: Click on element
        console.log("Step 30: Clicking on element...");
        try {
            const locator = page.locator('#ax-atc-EUIC_AddToCart_Search-content').nth(1);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 30: " + error.message);
        }
        // Step 31: Click on element
        console.log("Step 31: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(6);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 31: " + error.message);
        }
        // Step 32: Fill input field
        console.log("Step 32: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(7);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 32: " + error.message);
        }
        // Step 33: Click on element
        console.log("Step 33: Clicking on element...");
        try {
            const locator = page.locator('.s-suggestion').nth(1);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 33: " + error.message);
        }
        // Step 34: Wait for element
        console.log("Step 34: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 34: " + error.message);
        }
        // Step 35: Click on element
        console.log("Step 35: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(8);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 35: " + error.message);
        }
        // Step 36: Fill input field
        console.log("Step 36: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(9);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 36: " + error.message);
        }
        // Step 37: Wait for element
        console.log("Step 37: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 37: " + error.message);
        }
        // Step 38: Click on element
        console.log("Step 38: Clicking on element...");
        try {
            const locator = page.locator('.a-section').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 38: " + error.message);
        }
        // Step 39: Wait for element
        console.log("Step 39: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 39: " + error.message);
        }
        // Step 40: Wait for element
        console.log("Step 40: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 40: " + error.message);
        }
        // Step 41: Click on element
        console.log("Step 41: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(10);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 41: " + error.message);
        }
        // Step 42: Fill input field
        console.log("Step 42: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(11);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 42: " + error.message);
        }
        // Step 43: Click on element
        console.log("Step 43: Clicking on element...");
        try {
            const locator = page.locator('#nav-logo').nth(0);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 43: " + error.message);
        }
        // Step 44: Wait for element
        console.log("Step 44: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 44: " + error.message);
        }
        // Step 45: Fill input field
        console.log("Step 45: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(12);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 45: " + error.message);
        }
        // Step 46: Click on element
        console.log("Step 46: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(13);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 46: " + error.message);
        }
        // Step 47: Fill input field
        console.log("Step 47: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(14);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 47: " + error.message);
        }
        // Step 48: Click on element
        console.log("Step 48: Clicking on element...");
        try {
            const locator = page.locator('.s-suggestion').nth(2);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 48: " + error.message);
        }
        // Step 49: Wait for element
        console.log("Step 49: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 49: " + error.message);
        }
        // Step 50: Click on element
        console.log("Step 50: Clicking on element...");
        try {
            const locator = page.locator('.s-color-swatch-inner-circle-border').first();
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 50: " + error.message);
        }
        // Step 51: Wait for element
        console.log("Step 51: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 51: " + error.message);
        }
        // Step 52: Wait for element
        console.log("Step 52: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 52: " + error.message);
        }
        // Step 53: Click on element
        console.log("Step 53: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(15);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 53: " + error.message);
        }
        // Step 54: Fill input field
        console.log("Step 54: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(16);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 54: " + error.message);
        }
        // Step 55: Click on element
        console.log("Step 55: Clicking on element...");
        try {
            const locator = page.locator('.s-heavy').nth(3);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 55: " + error.message);
        }
        // Step 56: Wait for element
        console.log("Step 56: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 56: " + error.message);
        }
        // Step 57: Click on element
        console.log("Step 57: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(17);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 57: " + error.message);
        }
        // Step 58: Fill input field
        console.log("Step 58: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(18);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 58: " + error.message);
        }
        // Step 59: Wait for element
        console.log("Step 59: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 59: " + error.message);
        }
        // Step 60: Click on element
        console.log("Step 60: Clicking on element...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(19);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 60: " + error.message);
        }
        // Step 61: Fill input field
        console.log("Step 61: Filling input field...");
        try {
            const locator = page.locator('#twotabsearchtextbox').nth(20);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.fill("");
            console.log("  [OK] Fill action complete");
        } catch (error) {
            throw new Error("Fill failed at step 61: " + error.message);
        }
        // Step 62: Click on element
        console.log("Step 62: Clicking on element...");
        try {
            const locator = page.locator('#nav-logo').nth(1);
            await locator.waitFor({ state: "visible", timeout: 5000 });
            await locator.click();
            await page.waitForTimeout(500);
            console.log("  [OK] Click action complete");
        } catch (error) {
            throw new Error("Click failed at step 62: " + error.message);
        }
        // Step 63: Wait for element
        console.log("Step 63: Waiting 5000ms...");
        try {
            await page.waitForTimeout(5000);
            console.log("  [OK] Wait complete");
        } catch (error) {
            throw new Error("Wait failed at step 63: " + error.message);
        }

        console.log('[OK] All steps completed successfully');
    } catch (error) {
        console.error('[FAIL] Test execution failed:', error.message);
        lastError = error;
    } finally {
        await browser.close();
    }
}

runTests().catch(error => {
    console.error('[FAIL] Unrecoverable error:', error);
    process.exit(1);
});