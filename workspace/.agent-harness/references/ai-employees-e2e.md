# Skill: AI Employees Playwright E2E Framework (ai-frontend)

Standalone reference for generating or modifying tests in the AI Employees module (`apps/ai-employees/tests/`). This suite is separate from the Voice AI `test_automation` suite — do not mix their POM layers or conventions.

## Framework Overview

- **Test runner:** Playwright 1.58 (`@playwright/test`)
- **Core library:** `@gohighlevel/sdet-platform-core` (aliased as `@framework`)
- **Language:** TypeScript (ES2021)
- **Pattern:** Page Object Model (POM) with isolated browser contexts per test
- **Parallelism:** 6 workers, each test fully isolated
- **Tests location:** `apps/ai-employees/tests/framework/E2ETests/employees.test.ts`

## Directory Structure

```
apps/ai-employees/tests/
├── framework/
│   ├── APIhelpers/
│   │   ├── apiPaths.ts                  ← API endpoint constants
│   │   └── ConversationsAI.apis.ts      ← API client methods (CRUD for AI employees)
│   ├── E2ETests/
│   │   └── employees.test.ts            ← ALL test cases go here
│   ├── config/
│   │   ├── environments/
│   │   │   ├── staging.ts               ← Staging URLs, credentials, locationIds
│   │   │   ├── prod.ts                  ← Prod config
│   │   │   └── interop.ts               ← Interop config
│   │   ├── navigationHelper.ts          ← Centralized URL builder (supports VERSION env var)
│   │   ├── TokenManager.ts              ← Singleton token cache with JWT expiry
│   │   └── cleanupHelper.ts             ← Deletes non-primary employees before suite
│   ├── pageObjects/
│   │   ├── CommonPage.ts                ← loginToApplicationViaAPI() (API login with session caching)
│   │   ├── Employees.Object.ts          ← XPath/selector constants ONLY (no methods)
│   │   ├── MenuAndSubmenus.Objects.ts   ← Navigation route constants
│   │   └── employeesList.ts             ← Main page object (~24k lines, all UI actions)
│   ├── helpers/
│   │   └── quickPoll.ts                 ← Adaptive polling utility
│   ├── state/
│   │   └── EmployeesTestState.ts        ← Test state interface + tracker helpers
│   └── testData/
│       ├── Constants.ts                 ← Enums: Intents, MessageType
│       └── aiEmployee.data.ts           ← Bot payloads, conversation keyword sets
├── testConfig.ts                        ← Environment config loader (staging/prod/interop)
└── playwright.config.ts                 ← Playwright configuration
```

## Rule 1 — Test File Structure

All tests live in `employees.test.ts`.

**Always use API login, never UI login:**
- Use `commonPage.loginToApplicationViaAPI()` instead of `commonPage.loginToApplication()`.
- Use `navigationHelper.getEmployeesListUrl()` for direct URL navigation instead of sidebar menu navigation.
- `signInViaAPI` has built-in disk-based session caching with cross-worker locking — the first worker performs the actual API login and caches the session to disk; all subsequent workers reuse the cached session automatically. Saves ~30s per test, avoids rate-limiting.
- Do NOT add `CommonUtils.delay()` after login — API login + direct navigation is fast and doesn't need static waits.

```typescript
import { Page, test, expect, ProjectHelper } from '@framework';
import { EmployeesListPage } from '../pageObjects/employeesList';
import { MenuAndSubmenu } from '../pageObjects/MenuAndSubmenus.Objects';
import { CommonPage } from '../pageObjects/CommonPage';
import { ConversationAIApis } from '../APIhelpers/ConversationsAI.apis';
import { navigationHelper } from '../config/navigationHelper';
import { createEmployeesTestState, trackEmployee, logTestContext, EmployeesTestState } from '../state/EmployeesTestState';
import testConfig from '../../testConfig';

test.describe.parallel(
  `@AI_TEXT-UI-STAGING <Feature Group Name> Tests`,
  () => {
    const UILocationId = testConfig.conversationAI.UICredentials.locationId;
    let page: Page;
    let context: any;
    let commonPage: CommonPage;
    let employeesListPage: EmployeesListPage;
    let conversationAIAPI: ConversationAIApis;
    let testState: EmployeesTestState;
    const allCreatedEmployeeIds: string[] = [];

    test.describe.configure({ timeout: 120000 }); // 2 minutes per test

    test.beforeEach(async ({ browser }) => {
      await new Promise(resolve => setTimeout(resolve, 200)); // stagger startup

      context = await browser.newContext({ storageState: undefined });
      page = await context.newPage();

      commonPage = new CommonPage(page);
      employeesListPage = new EmployeesListPage(page);
      conversationAIAPI = new ConversationAIApis();

      testState = createEmployeesTestState(page, {
        testName: test.info().title,
        locationId: UILocationId,
        username: testConfig.conversationAI.UICredentials.username,
        password: testConfig.conversationAI.UICredentials.password,
      });

      try {
        await commonPage.loginToApplicationViaAPI(testState.username, testState.password);
        await page.goto(navigationHelper.getEmployeesListUrl(UILocationId), {
          waitUntil: 'domcontentloaded',
        });
        await employeesListPage.ensureEmployeesListTabReady();
      } catch (error) {
        await context?.close();
        throw error;
      }
    });

    test.afterEach(async () => {
      try {
        logTestContext(testState);
      } finally {
        await context?.close();
      }
    });

    test.afterAll(async () => {
      for (const employeeId of allCreatedEmployeeIds) {
        try {
          await conversationAIAPI.deleteAIEmployee(UILocationId, employeeId);
        } catch (error) {
          console.warn(`Failed to delete runtime bot ${employeeId}:`, error.message);
        }
      }
    });

    // ─── TEST CASES GO HERE ───────────────────────────────────────────────────

    test('@AI_TEXT-UI_PROD <Test Case Name>', async () => {
      // test body
    });
  }
);
```

**Tagging rules:**
- Outer `describe` block: `@AI_TEXT-UI-STAGING <Feature> Tests`
- Each individual `test`: `@AI_TEXT-UI_PROD <Test Case Name>`

## Rule 2 — Page Object Methods

All UI interactions belong in `employeesList.ts`. Never put Playwright locator calls directly in the test file.

```typescript
async <methodName>(param?: string): Promise<void | ReturnType> {
  // 1. Wait for element with quickPoll (never use raw page.waitForSelector)
  await quickPoll(async () => {
    try {
      const isVisible = await this.page.locator(EmployeesObject.SOME_XPATH).isVisible();
      return isVisible ? true : null;
    } catch {
      return null;
    }
  }, 30000);

  // 2. Interact via UIActions or operation
  await this.uiActions.click(EmployeesObject.SOME_XPATH);

  // 3. Assert with expect
  await expect(this.page.locator(EmployeesObject.RESULT_XPATH)).toBeVisible();
}
```

## Rule 3 — Selectors (Employees.Object.ts)

Add XPath constants to `Employees.Object.ts`. Never inline XPaths in test files or page object methods.

```typescript
export const EmployeesObject = {
  NEW_FEATURE_BUTTON_XPATH: `//button[@data-testid='new-feature-button']`,
  getFeatureItemByNameXPath: (name: string) =>
    `//div[@class='feature-list']//span[text()="${name}"]`,
};
```

**XPath conventions:** prefer `@data-testid` > `@id` > `@placeholder` > `text()` > `@class`; use `//` (absolute) not `.//`; wrap string values in double quotes inside backtick template literals.

## Rule 4 — API Helpers (APIhelpers/ConversationsAI.apis.ts)

For tests that need API setup/teardown (faster than UI), add methods to `ConversationAIApis` with retry/backoff on 429/5xx, and register the endpoint in `apiPaths.ts`.

## Rule 5 — Waiting Strategies (in order of preference)

1. **`quickPoll`** — any condition that needs retrying (element visibility, API polling)
2. **`CommonUtils.delay(ms)`** — explicit waits after known async operations (animations, transitions) — never after login
3. **`page.waitForResponse`** — intercepting specific API calls
4. **`expect().toBeVisible({ timeout })`** — final assertions

## Rule 6 — Test Data (aiEmployee.data.ts)

Add new payloads to `aiEmployeeData.payloads` or keyword sets to `conversationData.keywordSets`. Runtime unique naming: `` `${namePrefix}-${Date.now()}-${Math.floor(Math.random() * 1000)}` ``.

## Rule 7 — Resource Tracking & Cleanup

Always track created resources so `afterAll` can clean them up:
```typescript
allCreatedEmployeeIds.push(employeeId);
trackEmployee(testState, employeeId);
```

## Rule 8 — API vs UI Setup

Prefer API setup for pre-conditions (faster, less flaky). Use UI actions only to test UI behavior itself. Use API teardown, never UI teardown.

## Rule 9 — Logging Conventions

`🖱️` click/UI action · `✅` success · `⚠️` non-fatal warning · `❌` error · `📤` API request · `📥` API response · `🧹` cleanup

## Rule 10 — Test Categories

Group under existing `describe` categories: LIST VIEW & NAVIGATION, EMPLOYEE CREATION, QUICK ACTIONS, STOP BOT ACTION, FORM BASED BOT, FLOW BASED BUILDER.

## Step-by-Step: Adding a New Test Case

1. Read `employeesList.ts` to see if page object methods already exist.
2. Add missing XPath constants to `Employees.Object.ts`.
3. Add page object methods to `employeesList.ts` (log with emoji, use `quickPoll`, assert with `expect`).
4. Add API helper methods to `ConversationsAI.apis.ts` + endpoint in `apiPaths.ts` if needed.
5. Add test data to `aiEmployee.data.ts` if needed.
6. Write the test in `employees.test.ts` inside the appropriate `describe` block (Arrange via API, Act via page object, Assert on result).

## Important Constraints

1. Never use `page.locator()` directly in test files — always go through page object methods.
2. Never skip `allCreatedEmployeeIds.push(employeeId)` — resource leak if omitted.
3. Never use `page.waitForTimeout()` — use `quickPoll` or `CommonUtils.delay` instead.
4. Never hardcode credentials or locationIds — always read from `testConfig`.
5. Keep tests independent — no test should depend on state left by another test.
6. Timeout budget per test: 120 seconds (`test.describe.configure({ timeout: 120000 })`).
7. Browser context is closed in `afterEach` — do not rely on browser state between tests.
8. Always use API login (`commonPage.loginToApplicationViaAPI()`), never `commonPage.loginToApplication()`.
9. Always use `navigationHelper` for URLs (supports `VERSION` env var for version deployments, e.g. `VERSION=abmodal` → `https://abmodal.version.gohighlevel.site`).
