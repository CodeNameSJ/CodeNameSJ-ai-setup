# Skill: Vue 3 Conventions (ai-frontend / ghl-crm-frontend legacy / spm-ts)

Reference for code-reviewer, qa-bug-hunter, debug, and code-writer on frontend work.

## i18n — hard rules

- All user-visible strings via `t('key')` from `useI18n()` — never hardcoded
- Add every new key to `ai-frontend/apps/{app}/src/locales/en.json` before using in template
- For legacy `ghl-crm-frontend` work only, add keys to `apps/{app}/src/locales/en_US.json`
- Nested keys: `t('parent.child')` — JSON must match exactly (no camelCase/snake_case mix)
- After changing `en_US.json`, sync the other locale files in the same PR

## Pinia store rules

- Never modify state directly outside an action — always go through `store.actionName()`
- Template reads from `computed(() => store.value)` — never copy to a local `ref` (goes stale)
- Async actions: caller must `await` — UI that updates before the action completes shows stale state
- Add new state in `state()` — properties added later are not reactive

## Component patterns

- `ref` vs `reactive`: mutating a `ref` object's property requires `.value`
- `watch` with side effects needs a cleanup — stop watchers when component unmounts
- Async in `setup()` must be handled — component renders before data arrives otherwise
- `data-testid` attributes on interactive elements — required for Playwright selectors

## Module federation (spm-ts host + AI remotes)

- `spm-ts` is the shell/host — it composes the remotes
- Primary Voice AI frontend app is `ai-frontend/apps/voice-ai/`
- Legacy CRM remotes remain under `ghl-crm-frontend/apps/`
- Shared dependencies must match versions across host and remotes or runtime errors occur
- ESLint rules from `@platform-ui` package — run `yarn lint:check` before claiming done

## Common review flags

- `🔴` User string hardcoded in template
- `🔴` Pinia state mutated directly (not via action)
- `🟠` Component holds copy of store state in local `ref`
- `🟠` Missing `await` on async store action
- `🟡` `watch` without cleanup for side effects
- `🟡` New locale key used but not added to `en.json` (`en_US.json` for legacy CRM only)

## Test patterns (Vitest + Vue Test Utils)

```typescript
// Store test — no need to mount component
const store = useMyStore()
await store.someAction()
expect(store.value).toBe(expected)

// Component test
const wrapper = mount(MyComponent, { props: { ... } })
await wrapper.find('[data-testid="btn"]').trigger('click')
expect(wrapper.emitted('event')).toBeTruthy()

// i18n rendering — verify key resolves, not hardcoded string
expect(wrapper.text()).toContain(i18n.t('some.key'))
```
