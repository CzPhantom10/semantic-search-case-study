/**
 * Evaluation workbench: define test queries, grade passages by hand, run the
 * paired BM25/semantic experiment, then read the metrics.
 *
 * No quality score appears until a person supplies relevance judgments, and
 * judgment coverage travels with every result so partial labelling is visible
 * rather than hidden.
 */
import { useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ErrorBar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api'
import type { EvaluationRow, ExperimentResults, JudgmentSet, TestQuery } from '../api'
import { Empty, Meter, Metric, Notice, PageHead, Spinner, useAsync } from '../components'

const QUALITY_METRICS = [
  { key: 'precision_at_k', label: 'Precision@K' },
  { key: 'recall_at_k', label: 'Recall@K' },
  { key: 'mrr', label: 'MRR' },
  { key: 'ndcg_at_k', label: 'NDCG@K' },
] as const

const METHOD_COLOR: Record<string, string> = { Keyword: '#ffc93c', Semantic: '#8c6bff' }

/** Mean of the defined values only, so nulls do not drag an average to zero. */
function mean(rows: EvaluationRow[], key: keyof EvaluationRow) {
  const values = rows.map((row) => row[key]).filter((value): value is number => typeof value === 'number')
  return values.length ? values.reduce((total, value) => total + value, 0) / values.length : null
}

export default function Evaluation() {
  const queries = useAsync(() => api.queries(), [])
  const experiments = useAsync(() => api.experiments(), [])

  const [selectedQuery, setSelectedQuery] = useState<number | null>(null)
  const [draft, setDraft] = useState({ query_text: '', category: '', expected_information: '' })
  const [showForm, setShowForm] = useState(false)
  const [grades, setGrades] = useState<Record<string, number> | null>(null)
  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [message, setMessage] = useState<{ kind: 'success' | 'error' | 'warn'; text: string } | null>(null)
  const [experimentName, setExperimentName] = useState('BM25 vs semantic retrieval')
  const [selectedExperiment, setSelectedExperiment] = useState<number | null>(null)
  const [metric, setMetric] = useState<(typeof QUALITY_METRICS)[number]['key']>('ndcg_at_k')
  const [category, setCategory] = useState('All groups')

  const queryId = selectedQuery ?? queries.data?.[0]?.query_id ?? null

  // Grades are loaded per query and then held locally until saved.
  const judgments = useAsync<JudgmentSet | null>(
    () => (queryId == null ? Promise.resolve(null) : api.judgments(queryId)),
    [queryId],
  )

  const saved = useMemo(() => {
    const entries = judgments.data?.chunks.filter((chunk) => chunk.grade != null) ?? []
    return Object.fromEntries(entries.map((chunk) => [chunk.chunk_id, chunk.grade as number]))
  }, [judgments.data])

  const working = grades ?? saved
  const dirty = useMemo(() => JSON.stringify(working) !== JSON.stringify(saved), [working, saved])
  const corpus = judgments.data?.corpus_chunks ?? 0
  const coverage = corpus ? Object.keys(working).length / corpus : 0

  const experimentId = selectedExperiment ?? experiments.data?.[0]?.experiment_id ?? null
  const results = useAsync<ExperimentResults | null>(
    () => (experimentId == null ? Promise.resolve(null) : api.experimentResults(experimentId)),
    [experimentId],
  )

  const addQuery = async () => {
    if (!draft.query_text.trim()) return
    try {
      const { query_id } = await api.addQuery(draft)
      setDraft({ query_text: '', category: '', expected_information: '' })
      setShowForm(false)
      setSelectedQuery(query_id)
      setGrades(null)
      queries.reload()
      setMessage({ kind: 'success', text: 'Query saved. Now grade the passages below.' })
    } catch (cause) {
      setMessage({ kind: 'error', text: cause instanceof Error ? cause.message : String(cause) })
    }
  }

  const setGrade = (chunkId: string, grade: number) => {
    const next = { ...working }
    // Clicking the active grade clears it back to unjudged.
    if (next[chunkId] === grade) delete next[chunkId]
    else next[chunkId] = grade
    setGrades(next)
  }

  const saveGrades = async () => {
    if (queryId == null) return
    setSaving(true)
    setMessage(null)
    try {
      const { saved: count } = await api.saveJudgments(queryId, working)
      setGrades(null)
      judgments.reload()
      setMessage({ kind: 'success', text: `Saved ${count} explicit grade${count === 1 ? '' : 's'}.` })
    } catch (cause) {
      setMessage({ kind: 'error', text: cause instanceof Error ? cause.message : String(cause) })
    } finally {
      setSaving(false)
    }
  }

  const runExperiment = async () => {
    if (dirty) {
      setMessage({ kind: 'warn', text: 'Save your pending relevance grades before running the experiment.' })
      return
    }
    setRunning(true)
    setMessage(null)
    try {
      const { experiment_id, queries: count } = await api.runExperiment(experimentName)
      setSelectedExperiment(experiment_id)
      experiments.reload()
      setMessage({ kind: 'success', text: `Experiment #${experiment_id} completed over ${count} judged queries.` })
    } catch (cause) {
      setMessage({ kind: 'error', text: cause instanceof Error ? cause.message : String(cause) })
    } finally {
      setRunning(false)
    }
  }

  const rows = results.data?.rows ?? []
  const categories = useMemo(
    () => Array.from(new Set(rows.map((row) => row.query_category))).sort(),
    [rows],
  )
  const visible = category === 'All groups' ? rows : rows.filter((row) => row.query_category === category)

  const byMethod = useMemo(
    () =>
      ['Keyword', 'Semantic'].map((method) => {
        const group = visible.filter((row) => row.method === method)
        return {
          method,
          quality: mean(group, metric) ?? 0,
          retrieval: mean(group, 'latency_ms') ?? 0,
          retrievalSd: mean(group, 'latency_std_ms') ?? 0,
          endToEnd: mean(group, 'end_to_end_ms') ?? 0,
          endToEndSd: mean(group, 'end_to_end_std_ms') ?? 0,
        }
      }),
    [visible, metric],
  )

  const minCoverage = Math.min(
    ...visible.map((row) => row.judgment_coverage ?? 1),
    1,
  )

  return (
    <>
      <PageHead eyebrow="Measurement" title="Evaluation workbench">
        Build a repeatable comparison from your corpus, your test queries, and your own relevance grades. Model
        loading and shared passage loading are excluded from query timing.
      </PageHead>

      {message ? (
        <div style={{ marginBottom: 20 }}>
          <Notice kind={message.kind}>{message.text}</Notice>
        </div>
      ) : null}

      {/* ---------------------------------------------- step 1: test queries */}
      <h2 style={{ fontSize: 21, marginBottom: 14 }}>1 · Test queries</h2>
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row">
          <div className="field" style={{ flex: '1 1 320px' }}>
            <label htmlFor="pick-query">Working query</label>
            <select
              id="pick-query"
              className="select"
              value={queryId ?? ''}
              onChange={(event) => {
                setSelectedQuery(Number(event.target.value))
                setGrades(null)
              }}
              disabled={!queries.data?.length}
            >
              {queries.data?.length ? (
                queries.data.map((query: TestQuery) => (
                  <option key={query.query_id} value={query.query_id}>
                    Q{query.query_id} · {query.category || 'Uncategorized'}: {query.query_text}
                  </option>
                ))
              ) : (
                <option value="">No test queries yet</option>
              )}
            </select>
          </div>
          <button className="btn" onClick={() => setShowForm((value) => !value)} style={{ alignSelf: 'flex-end' }}>
            {showForm ? 'Cancel' : '+ New query'}
          </button>
        </div>

        {showForm ? (
          <div className="stack" style={{ marginTop: 16 }}>
            <div className="field">
              <label htmlFor="new-query">Query text</label>
              <input
                id="new-query"
                className="input input--mono"
                value={draft.query_text}
                onChange={(event) => setDraft({ ...draft, query_text: event.target.value })}
                placeholder="How can I protect my computer from hackers?"
              />
            </div>
            <div className="row" style={{ gap: 14 }}>
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="new-category">Category</label>
                <input
                  id="new-category"
                  className="input"
                  value={draft.category}
                  onChange={(event) => setDraft({ ...draft, category: event.target.value })}
                  placeholder="e.g. conceptual, factual, paraphrase"
                />
              </div>
              <div className="field" style={{ flex: 2 }}>
                <label htmlFor="new-expected">Expected relevant information</label>
                <input
                  id="new-expected"
                  className="input"
                  value={draft.expected_information}
                  onChange={(event) => setDraft({ ...draft, expected_information: event.target.value })}
                  placeholder="What a correct passage should contain"
                />
              </div>
            </div>
            <div className="row">
              <button className="btn btn--primary" onClick={addQuery} disabled={!draft.query_text.trim()}>
                Save query
              </button>
            </div>
          </div>
        ) : null}
      </div>

      {/* --------------------------------------------- step 2: grade passages */}
      <h2 style={{ fontSize: 21, margin: '28px 0 14px' }}>2 · Grade the passages</h2>

      {!queries.data?.length ? (
        <Empty art="✍️" title="Create a test query first">
          <p className="muted tiny" style={{ margin: 0, maxWidth: '46ch' }}>
            Metrics are computed against grades you assign by hand. Define a query above to begin.
          </p>
        </Empty>
      ) : judgments.loading ? (
        <Spinner />
      ) : judgments.data && !judgments.data.chunks.length ? (
        <Notice kind="warn">No indexed passages yet. Add a document before grading.</Notice>
      ) : judgments.data ? (
        <>
          <div className="card card--tint" style={{ marginBottom: 16 }}>
            <div className="row" style={{ marginBottom: 11 }}>
              <strong style={{ fontFamily: 'var(--font-comic)', fontSize: 14 }}>
                Judgment coverage: {Object.keys(working).length} of {corpus} passages ({(coverage * 100).toFixed(0)}%)
              </strong>
              <div className="spacer" />
              {dirty ? <span className="chip chip--coral">unsaved changes</span> : null}
              <button className="btn btn--sm btn--primary" onClick={saveGrades} disabled={saving || !dirty}>
                {saving ? 'Saving…' : 'Save grades'}
              </button>
            </div>
            <Meter value={coverage} />
            <p className="tiny muted" style={{ margin: '11px 0 0', lineHeight: 1.6 }}>
              Grade <strong>0</strong> means you assessed the passage and judged it not relevant. Leaving a passage
              unjudged means you have not assessed it — the two are different, and partial coverage biases Recall and
              the ranking metrics. Click an active grade again to clear it.
            </p>
            <div className="row" style={{ marginTop: 11, gap: 7 }}>
              <span className="chip chip--ghost">0 not relevant</span>
              <span className="chip chip--gold">1 marginal</span>
              <span className="chip chip--turquoise">2 relevant</span>
              <span className="chip chip--coral">3 highly relevant</span>
            </div>
          </div>

          <div className="judge">
            {judgments.data.chunks.map((chunk) => (
              <div className="judge__row" key={chunk.chunk_id}>
                <div>
                  <div className="row" style={{ gap: 7, marginBottom: 7 }}>
                    <span className="chip chip--ghost">{chunk.document}</span>
                    {chunk.page != null ? <span className="chip chip--ghost">p. {chunk.page}</span> : null}
                  </div>
                  <div className="judge__passage">{chunk.text}</div>
                </div>
                <div className="judge__grades">
                  {[0, 1, 2, 3].map((grade) => (
                    <button
                      key={grade}
                      className="grade-btn"
                      data-grade={grade}
                      aria-pressed={working[chunk.chunk_id] === grade}
                      onClick={() => setGrade(chunk.chunk_id, grade)}
                      title={['Not relevant', 'Marginally relevant', 'Relevant', 'Highly relevant'][grade]}
                    >
                      {grade}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {/* ------------------------------------------- step 3: run the experiment */}
      <h2 style={{ fontSize: 21, margin: '32px 0 14px' }}>3 · Run the paired experiment</h2>
      <div className="card">
        <div className="row">
          <div className="field" style={{ flex: '1 1 300px' }}>
            <label htmlFor="experiment-name">Experiment name</label>
            <input
              id="experiment-name"
              className="input"
              value={experimentName}
              onChange={(event) => setExperimentName(event.target.value)}
            />
          </div>
          <button
            className="btn btn--primary"
            onClick={runExperiment}
            disabled={running || !queries.data?.length}
            style={{ alignSelf: 'flex-end' }}
          >
            {running ? <Spinner /> : null}
            {running ? 'Running…' : 'Run for all judged queries'}
          </button>
        </div>
        <p className="tiny muted" style={{ margin: '13px 0 0', lineHeight: 1.6 }}>
          Every query with saved grades is run through both methods. Each measurement is repeated according to{' '}
          <code>SEMSEARCH_LATENCY_RUNS</code> and reported as mean ± standard deviation.
        </p>
      </div>

      {/* ------------------------------------------------- step 4: read results */}
      <h2 style={{ fontSize: 21, margin: '32px 0 14px' }}>4 · Results</h2>

      {!experiments.data?.length ? (
        <Empty art="📊" title="No experiments yet">
          <p className="muted tiny" style={{ margin: 0, maxWidth: '46ch' }}>
            Grade at least one query, then run the paired experiment to populate this dashboard.
          </p>
        </Empty>
      ) : (
        <>
          <div className="card" style={{ marginBottom: 18 }}>
            <div className="row" style={{ gap: 14 }}>
              <div className="field" style={{ flex: '1 1 260px' }}>
                <label htmlFor="pick-experiment">Experiment</label>
                <select
                  id="pick-experiment"
                  className="select"
                  value={experimentId ?? ''}
                  onChange={(event) => setSelectedExperiment(Number(event.target.value))}
                >
                  {experiments.data.map((experiment) => (
                    <option key={experiment.experiment_id} value={experiment.experiment_id}>
                      #{experiment.experiment_id} · {experiment.experiment_name} ·{' '}
                      {experiment.timestamp.replace('T', ' ').replace('+00:00', '')}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field" style={{ flex: '0 1 190px' }}>
                <label htmlFor="pick-group">Query group</label>
                <select
                  id="pick-group"
                  className="select"
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                >
                  {['All groups', ...categories].map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field" style={{ flex: '0 1 190px' }}>
                <label htmlFor="pick-metric">Quality metric</label>
                <select
                  id="pick-metric"
                  className="select"
                  value={metric}
                  onChange={(event) => setMetric(event.target.value as typeof metric)}
                >
                  {QUALITY_METRICS.map((option) => (
                    <option key={option.key} value={option.key}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              {experimentId != null ? (
                <a
                  className="btn"
                  href={api.exportUrl(experimentId)}
                  download
                  style={{ alignSelf: 'flex-end' }}
                >
                  ⬇ Export CSV
                </a>
              ) : null}
            </div>
          </div>

          {results.loading ? <Spinner /> : null}
          {results.error ? <Notice kind="error">{results.error}</Notice> : null}

          {visible.length ? (
            <>
              {minCoverage < 1 ? (
                <div style={{ marginBottom: 18 }}>
                  <Notice kind="warn">
                    Some queries do not have grades for every corpus passage (lowest coverage{' '}
                    {(minCoverage * 100).toFixed(0)}%). Recall and ranking metrics may be biased — review coverage
                    before reporting these numbers.
                  </Notice>
                </div>
              ) : null}

              <div className="metric-row">
                {byMethod.map((entry) => (
                  <Metric
                    key={entry.method}
                    label={`${entry.method} · ${QUALITY_METRICS.find((option) => option.key === metric)!.label}`}
                    value={entry.quality.toFixed(3)}
                    hint={`end to end ${entry.endToEnd.toFixed(2)} ms`}
                  />
                ))}
                <Metric
                  label="Queries evaluated"
                  value={new Set(visible.map((row) => row.query)).size}
                  hint={`top K ${String(results.data?.configuration.top_k ?? '—')}`}
                />
              </div>

              <div className="chart-grid" style={{ marginBottom: 20 }}>
                <div className="chart-card">
                  <h3>{QUALITY_METRICS.find((option) => option.key === metric)!.label} · mean</h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={byMethod} margin={{ top: 4, right: 12, bottom: 4, left: -18 }}>
                      <CartesianGrid stroke="rgba(18,16,31,.12)" vertical={false} />
                      <XAxis dataKey="method" tick={{ fontSize: 12 }} />
                      <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(value: number) => value.toFixed(4)} />
                      <Bar dataKey="quality" stroke="#12101f" strokeWidth={2} radius={[6, 6, 0, 0]}>
                        {byMethod.map((entry) => (
                          <Cell key={entry.method} fill={METHOD_COLOR[entry.method]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-card">
                  <h3>Retrieval only · mean ± SD (ms)</h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={byMethod} margin={{ top: 4, right: 12, bottom: 4, left: -18 }}>
                      <CartesianGrid stroke="rgba(18,16,31,.12)" vertical={false} />
                      <XAxis dataKey="method" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(value: number) => `${value.toFixed(3)} ms`} />
                      <Bar dataKey="retrieval" stroke="#12101f" strokeWidth={2} radius={[6, 6, 0, 0]}>
                        {byMethod.map((entry) => (
                          <Cell key={entry.method} fill={METHOD_COLOR[entry.method]} />
                        ))}
                        <ErrorBar dataKey="retrievalSd" stroke="#12101f" strokeWidth={2} width={6} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-card">
                  <h3>End to end · mean ± SD (ms)</h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={byMethod} margin={{ top: 4, right: 12, bottom: 4, left: -18 }}>
                      <CartesianGrid stroke="rgba(18,16,31,.12)" vertical={false} />
                      <XAxis dataKey="method" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(value: number) => `${value.toFixed(3)} ms`} />
                      <Bar dataKey="endToEnd" stroke="#12101f" strokeWidth={2} radius={[6, 6, 0, 0]}>
                        {byMethod.map((entry) => (
                          <Cell key={entry.method} fill={METHOD_COLOR[entry.method]} />
                        ))}
                        <ErrorBar dataKey="endToEndSd" stroke="#12101f" strokeWidth={2} width={6} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {results.data?.summary ? (
                <div className="speech-bubble" style={{ marginBottom: 20, maxWidth: '72ch' }}>
                  <p>{results.data.summary}</p>
                </div>
              ) : null}

              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Query</th>
                      <th>Group</th>
                      <th>Method</th>
                      <th>P@K</th>
                      <th>R@K</th>
                      <th>MRR</th>
                      <th>NDCG@K</th>
                      <th>Retrieval</th>
                      <th>End to end</th>
                      <th>Coverage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((row, position) => (
                      <tr key={`${row.query}-${row.method}-${position}`}>
                        <td>{row.query}</td>
                        <td className="tiny muted">{row.query_category}</td>
                        <td>
                          <span className={`chip ${row.method === 'Semantic' ? 'chip--violet' : 'chip--gold'}`}>
                            {row.method}
                          </span>
                        </td>
                        <td className="num">{row.precision_at_k?.toFixed(3) ?? '—'}</td>
                        <td className="num">{row.recall_at_k?.toFixed(3) ?? '—'}</td>
                        <td className="num">{row.mrr?.toFixed(3) ?? '—'}</td>
                        <td className="num">{row.ndcg_at_k?.toFixed(3) ?? '—'}</td>
                        <td className="num">{row.latency_ms?.toFixed(2) ?? '—'}</td>
                        <td className="num">{row.end_to_end_ms?.toFixed(2) ?? '—'}</td>
                        <td className="num">
                          {row.judgment_coverage != null ? `${(row.judgment_coverage * 100).toFixed(0)}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </>
      )}
    </>
  )
}
