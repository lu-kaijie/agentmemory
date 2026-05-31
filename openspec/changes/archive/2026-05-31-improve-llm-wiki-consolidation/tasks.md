## 1. Data Models And Indexing

- [x] 1.1 Extend knowledge lifecycle fields for lesson decay, deleted state, project and query provenance
- [x] 1.2 Add InsightRecord, Wiki lint issue/report models and query filing request/response models
- [x] 1.3 Extend SourceType and search document mapping for insight records
- [x] 1.4 Update export/import schema handling for new insight and lifecycle fields

## 2. Consolidation Core

- [x] 2.1 Implement wiki consolidation over summaries, memories and existing knowledge
- [x] 2.2 Add conservative semantic/procedural merge and fingerprint reuse
- [x] 2.3 Add service methods to list consolidation results and affected records
- [x] 2.4 Ensure consolidation creates or updates search documents

## 3. Lesson And Crystal Lifecycle

- [x] 3.1 Implement lesson recall with query, min confidence, project and limit filters
- [x] 3.2 Implement lesson strengthen and decay/soft-delete logic
- [x] 3.3 Implement crystal creation from source ids with stable sourceGroup reuse
- [x] 3.4 Make crystal-created lessons strengthen existing lesson records

## 4. Reflect, Lint And Query Filing

- [x] 4.1 Implement reflect insight generation from semantic/procedural/lesson/crystal clusters
- [x] 4.2 Implement insight reinforcement and indexing
- [x] 4.3 Implement wiki lint report for contradiction, stale, low-confidence, missing-source and orphan issues
- [x] 4.4 Implement query filing to save high-value answers as insight, knowledge or crystal

## 5. Interfaces And Maintenance

- [x] 5.1 Add CLI commands for consolidate, lessons, lesson-recall, crystallize, reflect, lint and file-answer
- [x] 5.2 Add REST endpoints under `/agentmemory/wiki/*` for the new operations
- [x] 5.3 Extend maintenance run to include consolidation, lesson decay and optional reflect summaries
- [x] 5.4 Update Skill and docs to describe LLM Wiki as structured compounding knowledge, not fixed pages

## 6. Tests And Validation

- [x] 6.1 Add service tests for consolidation, lesson lifecycle, crystal reuse and reflect insights
- [x] 6.2 Add service tests for wiki lint and query filing
- [x] 6.3 Add search/context tests for insight and lifecycle-filtered knowledge
- [x] 6.4 Add CLI and REST tests for new Wiki operations
- [x] 6.5 Run pytest and strict OpenSpec validation

## 7. Strong LLM Wiki Consolidation

- [x] 7.1 Make consolidation prefer LLM synthesis over concept grouping when an LLM provider is configured
- [x] 7.2 Persist LLM-created dynamic wiki pages for entity, concept, source, comparison and synthesis records
- [x] 7.3 Make wiki lint call the LLM for contradiction and stale detection, with deterministic checks as supplements
- [x] 7.4 Index dynamic wiki page type, slug and parent topic for search/context
- [x] 7.5 Add tests for LLM dynamic pages, LLM lint issues and dynamic page search
- [x] 7.6 Update docs and run pytest plus strict OpenSpec validation
