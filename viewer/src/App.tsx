import { useEffect, useMemo, useState } from 'react'
import { ReactFlow, Background, Controls, MiniMap, type Edge, type Node } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  BookOpen,
  Brain,
  CircleAlert,
  Database,
  FileSearch,
  GitBranch,
  Layers,
  Pin,
  RefreshCw,
  Search,
  Wrench,
} from 'lucide-react'
import styles from './App.module.css'

type Scope = 'all' | 'global' | 'project'
type Tab =
  | 'overview'
  | 'context'
  | 'search'
  | 'projects'
  | 'pins'
  | 'memories'
  | 'wiki'
  | 'knowledge'
  | 'jobs'
  | 'audit'
  | 'graph'

type AnyRecord = Record<string, any>

type AppState = {
  health: AnyRecord | null
  index: AnyRecord | null
  projects: AnyRecord[]
  pins: AnyRecord[]
  memories: AnyRecord[]
  summaries: AnyRecord[]
  wikiPages: AnyRecord[]
  knowledge: AnyRecord[]
  candidates: AnyRecord[]
  llmJobs: AnyRecord[]
  wikiJobs: AnyRecord[]
  audit: AnyRecord[]
}

const emptyState: AppState = {
  health: null,
  index: null,
  projects: [],
  pins: [],
  memories: [],
  summaries: [],
  wikiPages: [],
  knowledge: [],
  candidates: [],
  llmJobs: [],
  wikiJobs: [],
  audit: [],
}

const tabs: Array<{ id: Tab; label: string; icon: any }> = [
  { id: 'overview', label: 'Overview', icon: Layers },
  { id: 'context', label: 'Context', icon: Brain },
  { id: 'search', label: 'Search', icon: Search },
  { id: 'projects', label: 'Projects', icon: Database },
  { id: 'pins', label: 'Pins', icon: Pin },
  { id: 'memories', label: 'Memories', icon: BookOpen },
  { id: 'wiki', label: 'Wiki', icon: FileSearch },
  { id: 'knowledge', label: 'Knowledge', icon: Brain },
  { id: 'jobs', label: 'Jobs', icon: CircleAlert },
  { id: 'audit', label: 'Audit', icon: GitBranch },
  { id: 'graph', label: 'Graph', icon: GitBranch },
]

async function api(path: string, options: RequestInit = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`)
  }
  return response.json()
}

function App() {
  const [data, setData] = useState<AppState>(emptyState)
  const [tab, setTab] = useState<Tab>('overview')
  const [scope, setScope] = useState<Scope>('all')
  const [projectId, setProjectId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [maintenanceRunning, setMaintenanceRunning] = useState(false)
  const [maintenanceResult, setMaintenanceResult] = useState<AnyRecord | null>(null)
  const [query, setQuery] = useState('memory context Wiki knowledge')
  const [mode, setMode] = useState('hybrid')
  const [searchResult, setSearchResult] = useState<AnyRecord | null>(null)
  const [smartResult, setSmartResult] = useState<AnyRecord | null>(null)
  const [contextResult, setContextResult] = useState<AnyRecord | null>(null)

  const selectedProject = data.projects.find((project) => project.id === projectId) ?? null

  async function loadAll() {
    setLoading(true)
    setError('')
    try {
      const [
        health,
        index,
        projects,
        pins,
        memories,
        summaries,
        wikiPages,
        knowledge,
        candidates,
        llmJobs,
        wikiJobs,
        audit,
      ] = await Promise.all([
        api('/agentmemory/health'),
        api('/agentmemory/index/status'),
        api('/agentmemory/projects'),
        api('/agentmemory/pins'),
        api('/agentmemory/memories'),
        api('/agentmemory/summaries'),
        api('/agentmemory/wiki/pages'),
        api('/agentmemory/wiki/knowledge'),
        api('/agentmemory/memory-candidates'),
        api('/agentmemory/llm-processing-jobs'),
        api('/agentmemory/wiki/jobs'),
        api('/agentmemory/audit'),
      ])
      const next = {
        health,
        index,
        projects: projects.projects ?? [],
        pins: pins.pinnedMemory ?? [],
        memories: memories.memories ?? [],
        summaries: summaries.summaries ?? [],
        wikiPages: wikiPages.wikiPages ?? [],
        knowledge: knowledge.knowledge ?? [],
        candidates: candidates.memoryCandidates ?? [],
        llmJobs: llmJobs.llmProcessingJobs ?? [],
        wikiJobs: wikiJobs.wikiUpdateJobs ?? [],
        audit: audit.audit ?? [],
      }
      setData(next)
      if (!projectId && next.projects.length) {
        setProjectId(next.projects[0].id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadAll()
  }, [])

  const filtered = useMemo(() => filterData(data, scope, projectId), [data, scope, projectId])
  const graph = useMemo(() => buildGraph(filtered), [filtered])

  async function runSearch(kind: 'search' | 'smart' | 'context') {
    if (!query.trim()) return
    const body: AnyRecord = { query, limit: 10 }
    if (kind !== 'context') body.mode = mode
    if (scope !== 'all') body.scope = scope
    if (projectId) body.projectId = projectId
    const path = kind === 'search' ? '/agentmemory/search' : kind === 'smart' ? '/agentmemory/smart-search' : '/agentmemory/context'
    const result = await api(path, { method: 'POST', body: JSON.stringify(body) })
    if (kind === 'search') setSearchResult(result)
    if (kind === 'smart') setSmartResult(result)
    if (kind === 'context') setContextResult(result)
  }

  async function runMaintenance() {
    setMaintenanceRunning(true)
    setError('')
    try {
      const result = await api('/agentmemory/maintenance/run', {
        method: 'POST',
        body: JSON.stringify({ limit: data.health?.config?.maintenance?.limit ?? 25 }),
      })
      setMaintenanceResult(result)
      await loadAll()
      setTab('jobs')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setMaintenanceRunning(false)
    }
  }

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div>
          <h1>AgentMemory Viewer</h1>
          <p>Global / Project memory, LLM Wiki, context evidence and graph inspection</p>
        </div>
        <div className={styles.headerActions}>
          <select value={projectId} onChange={(event) => setProjectId(event.target.value)} aria-label="Project">
            <option value="">No project selected</option>
            {data.projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name} · {project.root}
              </option>
            ))}
          </select>
          <div className={styles.segmented}>
            {(['all', 'global', 'project'] as Scope[]).map((item) => (
              <button key={item} className={scope === item ? styles.active : ''} onClick={() => setScope(item)}>
                {item}
              </button>
            ))}
          </div>
          <button className={styles.iconButton} onClick={loadAll} disabled={loading} aria-label="Refresh">
            <RefreshCw size={16} />
          </button>
          <button className={styles.primary} onClick={runMaintenance} disabled={maintenanceRunning} aria-label="Run maintenance">
            <Wrench size={15} />
            <span>{maintenanceRunning ? 'Processing' : 'Run Maintenance'}</span>
          </button>
        </div>
      </header>

      <main className={styles.layout}>
        <aside className={styles.sidebar}>
          <StatusPanel data={data} error={error} selectedProject={selectedProject} />
          <nav className={styles.nav}>
            {tabs.map(({ id, label, icon: Icon }) => (
              <button key={id} className={tab === id ? styles.activeNav : ''} onClick={() => setTab(id)}>
                <Icon size={15} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </aside>

        <section className={styles.content}>
          {error ? <div className={styles.error}>{error}</div> : null}
          {tab === 'overview' && <Overview data={filtered} selectedProject={selectedProject} />}
          {tab === 'context' && (
            <ContextView
              query={query}
              setQuery={setQuery}
              runContext={() => void runSearch('context')}
              result={contextResult}
            />
          )}
          {tab === 'search' && (
            <SearchView
              query={query}
              setQuery={setQuery}
              mode={mode}
              setMode={setMode}
              runSearch={() => void runSearch('search')}
              runSmart={() => void runSearch('smart')}
              searchResult={searchResult}
              smartResult={smartResult}
            />
          )}
          {tab === 'projects' && <RecordList title="Projects" records={data.projects} />}
          {tab === 'pins' && <RecordList title="Pinned Memory" records={filtered.pins} />}
          {tab === 'memories' && <RecordList title="Memories" records={filtered.memories} />}
          {tab === 'wiki' && <RecordList title="Wiki Pages" records={filtered.wikiPages} />}
          {tab === 'knowledge' && <RecordList title="Knowledge" records={filtered.knowledge} />}
          {tab === 'jobs' && <RecordList title="Jobs" records={[...filtered.llmJobs, ...filtered.wikiJobs, ...filtered.candidates]} />}
          {tab === 'jobs' && maintenanceResult ? <MaintenanceResult result={maintenanceResult} /> : null}
          {tab === 'audit' && <RecordList title="Audit" records={filtered.audit} />}
          {tab === 'graph' && <GraphView nodes={graph.nodes} edges={graph.edges} />}
        </section>
      </main>
    </div>
  )
}

function MaintenanceResult({ result }: { result: AnyRecord }) {
  const indexJobs = result.index?.jobs?.length ?? 0
  const llmJobs = result.llm?.jobs?.length ?? 0
  const wikiJobs = result.wiki?.jobs?.length ?? 0
  const pages = result.wiki?.pages?.length ?? 0
  const knowledge = result.wiki?.knowledge?.length ?? 0
  const errors = result.errors?.length ?? 0
  return (
    <section className={styles.panel}>
      <h2>Last Maintenance</h2>
      <div className={styles.cards}>
        <Stat label="Index Jobs" value={indexJobs} detail="processed" />
        <Stat label="LLM Jobs" value={llmJobs} detail="processed" />
        <Stat label="Wiki Jobs" value={wikiJobs} detail={`${pages} pages`} />
        <Stat label="Knowledge" value={knowledge} detail={`${errors} errors`} />
      </div>
    </section>
  )
}

function StatusPanel({ data, error, selectedProject }: { data: AppState; error: string; selectedProject: AnyRecord | null }) {
  const provider = data.health?.providers ?? {}
  return (
    <section className={styles.panel}>
      <div className={styles.statusLine}>
        <span className={`${styles.dot} ${data.health?.status === 'ok' ? styles.ok : error ? styles.bad : styles.warn}`} />
        <strong>{error || data.health?.status || 'loading'}</strong>
      </div>
      <div className={styles.stats}>
        <Stat label="Documents" value={data.index?.documents ?? 0} detail={`${data.index?.failedJobs ?? 0} failed`} />
        <Stat label="Projects" value={data.projects.length} detail={selectedProject?.name ?? 'none'} />
        <Stat label="LLM" value={provider.llm?.ready ? 'ready' : 'unknown'} detail={provider.llm?.model ?? ''} />
        <Stat label="Embedding" value={provider.embedding?.ready ? 'ready' : 'unknown'} detail={provider.embedding?.model ?? ''} />
      </div>
    </section>
  )
}

function Stat({ label, value, detail }: { label: string; value: any; detail: string }) {
  return (
    <div className={styles.stat}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  )
}

function Overview({ data, selectedProject }: { data: AppState; selectedProject: AnyRecord | null }) {
  const globalPins = data.pins.filter((item) => item.scope === 'global')
  const projectPins = data.pins.filter((item) => item.scope === 'project')
  return (
    <div className={styles.stack}>
      <div className={styles.scopeGrid}>
        <section className={styles.panel}>
          <h2>Global</h2>
          <RecordList compact title="Pinned" records={globalPins} />
          <RecordList compact title="Global Memories" records={data.memories.filter((item) => item.scope === 'global')} />
        </section>
        <section className={styles.panel}>
          <h2>Project</h2>
          <p className={styles.muted}>{selectedProject ? `${selectedProject.name} · ${selectedProject.root}` : 'No project selected'}</p>
          <RecordList compact title="Pinned" records={projectPins} />
          <RecordList compact title="Project Knowledge" records={data.knowledge} />
        </section>
      </div>
      <div className={styles.cards}>
        <Stat label="Projects" value={data.projects.length} detail="scoped evidence" />
        <Stat label="Memories" value={data.memories.length} detail="explicit records" />
        <Stat label="Wiki Pages" value={data.wikiPages.length} detail="topic and dynamic pages" />
        <Stat label="Knowledge" value={data.knowledge.length} detail="semantic/procedural/lesson/crystal" />
      </div>
    </div>
  )
}

function ContextView({
  query,
  setQuery,
  runContext,
  result,
}: {
  query: string
  setQuery: (value: string) => void
  runContext: () => void
  result: AnyRecord | null
}) {
  return (
    <div className={styles.stack}>
      <div className={styles.toolbar}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Context query" />
        <button className={styles.primary} onClick={runContext}>
          Context
        </button>
      </div>
      {result ? (
        <>
          <div className={styles.sectionGrid}>
            {(result.sections ?? []).map((section: AnyRecord) => (
              <article key={section.name} className={styles.record}>
                <div className={styles.recordTitle}>
                  <strong>{section.name}</strong>
                  <code>{section.empty ? 'empty' : `${(section.sourceIds ?? []).length} sources`}</code>
                </div>
                <pre className={styles.softPre}>{section.content}</pre>
              </article>
            ))}
          </div>
          <RecordList title="Evidence" records={result.evidence ?? []} />
        </>
      ) : (
        <Empty message="Run context to inspect fixed sections." />
      )}
    </div>
  )
}

function SearchView({
  query,
  setQuery,
  mode,
  setMode,
  runSearch,
  runSmart,
  searchResult,
  smartResult,
}: {
  query: string
  setQuery: (value: string) => void
  mode: string
  setMode: (value: string) => void
  runSearch: () => void
  runSmart: () => void
  searchResult: AnyRecord | null
  smartResult: AnyRecord | null
}) {
  return (
    <div className={styles.stack}>
      <div className={styles.toolbar}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search memory evidence" />
        <select value={mode} onChange={(event) => setMode(event.target.value)}>
          <option value="keyword">keyword</option>
          <option value="vector">vector</option>
          <option value="hybrid">hybrid</option>
        </select>
        <button className={styles.primary} onClick={runSearch}>
          Search
        </button>
        <button onClick={runSmart}>Smart</button>
      </div>
      {searchResult ? <RecordList title="Search Results" records={searchResult.results ?? []} /> : null}
      {smartResult ? (
        <section className={styles.panel}>
          <h2>Smart Search</h2>
          <p>{smartResult.answer}</p>
          <RecordList compact title="Results" records={smartResult.results ?? []} />
        </section>
      ) : null}
    </div>
  )
}

function RecordList({ title, records, compact = false }: { title: string; records: AnyRecord[]; compact?: boolean }) {
  return (
    <section className={compact ? styles.compactList : styles.stack}>
      <h2>{title}</h2>
      {records.length ? (
        <div className={styles.records}>
          {records.map((record, index) => (
            <RecordCard key={record.id ?? record.sourceId ?? `${title}-${index}`} record={record} />
          ))}
        </div>
      ) : (
        <Empty message="No records." />
      )}
    </section>
  )
}

function RecordCard({ record }: { record: AnyRecord }) {
  const id = record.id ?? record.sourceId ?? record.documentId ?? record.targetId ?? ''
  const title = record.title ?? record.kind ?? record.type ?? record.status ?? record.sourceType ?? record.action ?? 'record'
  const body = record.content ?? record.answer ?? record.lastError ?? record.root ?? JSON.stringify(record.details ?? record)
  const tags = [
    record.scope,
    record.project,
    record.projectId,
    record.topic,
    record.language,
    record.enabled === false ? 'disabled' : null,
    ...(record.concepts ?? []),
    ...(record.matchSources ?? []),
  ].filter(Boolean)
  return (
    <article className={styles.record}>
      <div className={styles.recordTitle}>
        <strong>{title}</strong>
        <code>{id}</code>
      </div>
      <p>{short(body)}</p>
      {tags.length ? (
        <div className={styles.tags}>
          {tags.slice(0, 10).map((tag: string) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
      ) : null}
    </article>
  )
}

function GraphView({ nodes, edges }: { nodes: Node[]; edges: Edge[] }) {
  if (!nodes.length) return <Empty message="No graph records yet." />
  return (
    <div className={styles.graph}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  )
}

function Empty({ message }: { message: string }) {
  return <div className={styles.empty}>{message}</div>
}

function filterData(data: AppState, scope: Scope, projectId: string): AppState {
  const visible = (item: AnyRecord) => {
    if (scope === 'global') return item.scope === 'global'
    if (scope === 'project') return item.scope === 'project' && (!projectId || item.projectId === projectId)
    if (projectId && item.scope === 'project') return item.projectId === projectId
    return true
  }
  return {
    ...data,
    pins: data.pins.filter(visible),
    memories: data.memories.filter(visible),
    summaries: data.summaries.filter(visible),
    wikiPages: data.wikiPages.filter(visible),
    knowledge: data.knowledge.filter(visible),
    candidates: data.candidates,
    llmJobs: data.llmJobs,
    wikiJobs: data.wikiJobs.filter(visible),
    audit: data.audit,
  }
}

function buildGraph(data: AppState): { nodes: Node[]; edges: Edge[] } {
  const nodes = new Map<string, Node>()
  const edges: Edge[] = []
  const addNode = (id: string, label: string, type: string) => {
    if (!nodes.has(id)) {
      nodes.set(id, { id, type, position: { x: 0, y: 0 }, data: { label } })
    }
  }
  const addEdge = (source: string, target: string, label: string) => {
    if (nodes.has(source) && nodes.has(target)) {
      edges.push({ id: `${source}-${target}-${edges.length}`, source, target, label })
    }
  }
  for (const project of data.projects) addNode(`project:${project.id}`, project.name, 'project')
  for (const pin of data.pins) {
    addNode(`pin:${pin.id}`, short(pin.content, 28), 'pin')
    if (pin.projectId) addEdge(`pin:${pin.id}`, `project:${pin.projectId}`, 'pinned_to')
  }
  for (const memory of data.memories) {
    addNode(`memory:${memory.id}`, short(memory.content, 28), 'memory')
    if (memory.projectId) addEdge(`memory:${memory.id}`, `project:${memory.projectId}`, 'scoped_to')
    for (const concept of memory.concepts ?? []) {
      addNode(`concept:${concept}`, concept, 'concept')
      addEdge(`memory:${memory.id}`, `concept:${concept}`, 'mentions')
    }
  }
  for (const page of data.wikiPages) {
    addNode(`wiki:${page.id}`, page.title ?? page.topic, 'wiki')
    if (page.projectId) addEdge(`wiki:${page.id}`, `project:${page.projectId}`, 'scoped_to')
  }
  const count = nodes.size || 1
  Array.from(nodes.values()).forEach((node, index) => {
    const angle = (index / count) * Math.PI * 2
    node.position = { x: Math.cos(angle) * 320 + 420, y: Math.sin(angle) * 220 + 260 }
  })
  return { nodes: Array.from(nodes.values()), edges }
}

function short(value: unknown, max = 260) {
  const text = String(value ?? '')
  return text.length > max ? `${text.slice(0, max)}...` : text
}

export default App
