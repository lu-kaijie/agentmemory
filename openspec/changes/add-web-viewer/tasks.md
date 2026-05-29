## 1. Viewer Hosting

- [ ] 1.1 Add Viewer static asset location
- [ ] 1.2 Add `GET /agentmemory/` route returning Viewer HTML
- [ ] 1.3 Ensure Viewer route does not break existing API routes

## 2. Viewer UI

- [ ] 2.1 Build status dashboard for health, providers, and index status
- [ ] 2.2 Build read-only tabs or sections for sessions, memories, summaries, candidates, audit, and LLM jobs
- [ ] 2.3 Build search form with keyword, vector, and hybrid modes
- [ ] 2.4 Build smart-search form with answer, evidence, results, and context display
- [ ] 2.5 Build lightweight relationship graph from existing records
- [ ] 2.6 Ensure Viewer does not expose unsupported edit/delete/wiki/export/hook/mcp actions

## 3. Data Integration

- [ ] 3.1 Fetch status from existing health and index endpoints
- [ ] 3.2 Fetch record lists from existing sessions, memories, summaries, candidates, audit, and LLM job endpoints
- [ ] 3.3 Fetch search and smart-search results from existing search endpoints
- [ ] 3.4 Derive graph nodes and edges on the client from loaded records
- [ ] 3.5 Handle loading, empty, and error states

## 4. Verification

- [ ] 4.1 Add REST test for `/agentmemory/` returning HTML
- [ ] 4.2 Add tests that existing API routes still return JSON
- [ ] 4.3 Add tests or static checks for required Viewer sections
- [ ] 4.4 Add tests or static checks excluding unsupported actions
- [ ] 4.5 Run full pytest suite
- [ ] 4.6 Verify OpenSpec status is complete for `add-web-viewer`
