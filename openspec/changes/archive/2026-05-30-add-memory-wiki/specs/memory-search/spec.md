## ADDED Requirements

### Requirement: Search Wiki Pages

系统 SHALL 支持搜索 Wiki pages。

Search sourceTypes MUST 支持 `wikiPage`。Keyword、vector 和 hybrid search MUST 能返回匹配的 Wiki page results，并保留 Wiki page source id。

Search sourceTypes MUST 支持 `knowledge`。Keyword、vector 和 hybrid search MUST 能返回匹配的 distilled knowledge results，并保留 knowledge source id。

#### Scenario: Keyword search finds wiki page

- **WHEN** 用户使用 keyword search 查询 Wiki 页面中的术语
- **THEN** 系统返回 sourceType 为 `wikiPage` 的结果

#### Scenario: Vector search finds wiki page

- **WHEN** 用户使用自然语言 vector search 查询 Wiki 页面语义相关内容
- **THEN** 系统返回 sourceType 为 `wikiPage` 的结果

#### Scenario: Filter search to wiki pages

- **WHEN** 用户指定 sourceTypes 包含 `wikiPage`
- **THEN** 系统只返回符合 source type 过滤条件的结果

#### Scenario: Search distilled knowledge

- **WHEN** 用户搜索已沉淀的 semantic、procedural、lesson 或 crystal 内容
- **THEN** 系统返回 sourceType 为 `knowledge` 的结果

#### Scenario: Filter search to distilled knowledge

- **WHEN** 用户指定 sourceTypes 包含 `knowledge`
- **THEN** 系统只返回符合 source type 过滤条件的 results
