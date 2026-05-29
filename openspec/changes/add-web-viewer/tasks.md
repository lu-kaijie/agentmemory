## 1. Viewer Hosting

- [x] 1.1 Add Viewer static asset location
- [x] 1.2 Add `GET /agentmemory/` route returning Viewer HTML
- [x] 1.3 Ensure Viewer route does not break existing API routes

## 2. Viewer UI

- [x] 2.1 Build status dashboard for health, providers, and index status
- [x] 2.2 Build read-only tabs or sections for sessions, memories, summaries, candidates, audit, and LLM jobs
- [x] 2.3 Build search form with keyword, vector, and hybrid modes
- [x] 2.4 Build smart-search form with answer, evidence, results, and context display
- [x] 2.5 Build lightweight relationship graph from existing records
- [x] 2.6 Ensure Viewer does not expose unsupported edit/delete/wiki/export/hook/mcp actions

## 3. Data Integration

- [x] 3.1 Fetch status from existing health and index endpoints
- [x] 3.2 Fetch record lists from existing sessions, memories, summaries, candidates, audit, and LLM job endpoints
- [x] 3.3 Fetch search and smart-search results from existing search endpoints
- [x] 3.4 Derive graph nodes and edges on the client from loaded records
- [x] 3.5 Handle loading, empty, and error states

## 4. Verification

- [x] 4.1 Add REST test for `/agentmemory/` returning HTML
- [x] 4.2 Add tests that existing API routes still return JSON
- [x] 4.3 Add tests or static checks for required Viewer sections
- [x] 4.4 Add tests or static checks excluding unsupported actions
- [x] 4.5 Run full pytest suite
- [x] 4.6 Verify OpenSpec status is complete for `add-web-viewer`
