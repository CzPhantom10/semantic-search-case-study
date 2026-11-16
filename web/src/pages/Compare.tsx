/**
 * Side-by-side matchup: one query, the same indexed passages, both rankers.
 *
 * Beyond the two columns this view reports rank overlap — how many passages
 * both methods surfaced — which is the comparison the case study turns on.
 */
import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import type { CompareResponse } from '../api'
import { Metric, Notice, PageHead, ResultCard, ScoreGuide, Spinner } from '../components'
import { useStats } from '../stats-context'

export default function Compare() {
  const [params] = useSearchParams()
  const { reloadStats } = useStats()
  const [query, setQuery] = useState(params.get('q') ?? '')
  const [k, setK] = useState(5)
  const [response, setResponse] = useState<CompareResponse | null>(null)
  const [ran, setRan] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    const trimmed = query.trim()
    if (!trimmed) return
    setBusy(true)
    setError(null)
    try {
      setResponse(await api.compare(trimmed, k))
      setRan(trimmed)
      // A completed comparison unlocks the evaluation step.
      reloadStats()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause))
      setResponse(null)
    } finally {
      setBusy(false)
    }
  }

  const overlap = useMemo(() => {
    if (!response) return null
    const keyword = new Set(response.keyword.results.map((hit) => hit.chunk_id))
    const shared = response.semantic.results.filter((hit) => keyword.has(hit.chunk_id)).length
    const union = new Set([
      ...keyword,
      ...response.semantic.results.map((hit) => hit.chunk_id),
    ]).size
    return { shared, union, jaccard: union ? shared / union : 0 }
  }, [response])

  return (
    <>
      <PageHead eyebrow="Side by side" title="Compare the two methods">
        One query runs against the same indexed passages through both rankers. Each run is also recorded in history,
        so the pair becomes available to the evaluation workbench.
      </PageHead>

      <div className="searchbar">
        <div className="field searchbar__query">
          <label htmlFor="query">Your query</label>
          <input
            id="query"
            className="input input--mono"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && run()}
            placeholder="How can I protect my computer from hackers?"
          />
        </div>
        <div className="field searchbar__k">
          <label htmlFor="k">Per method</label>
          <select id="k" className="select" value={k} onChange={(event) => setK(Number(event.target.value))}>
            {[3, 5, 10, 15, 20].map((option) => (
              <option key={option} value={option}>
                top {option}
              </option>
            ))}
          </select>
        </div>
        <button className="btn btn--primary" onClick={run} disabled={busy || !query.trim()}>
          {busy ? <Spinner /> : null}
          {busy ? 'Running both…' : 'Run the matchup'}
        </button>
      </div>

      <div style={{ margin: '20px 0' }}>
        <ScoreGuide />
      </div>

      {error ? <Notice kind="error">{error}</Notice> : null}

      {response && overlap ? (
        <>
          <div className="metric-row">
            <Metric
              label="Shared passages"
              value={`${overlap.shared} / ${k}`}
              hint="returned by both methods"
            />
            <Metric
              label="Rank agreement"
              value={`${(overlap.jaccard * 100).toFixed(0)}%`}
              hint="Jaccard over the two result sets"
            />
            <Metric
              label="Keyword · end to end"
              value={`${response.keyword.timing.end_to_end_ms.toFixed(1)} ms`}
              hint={`retrieval ${response.keyword.timing.retrieval_ms.toFixed(2)} ms`}
            />
            <Metric
              label="Semantic · end to end"
              value={`${response.semantic.timing.end_to_end_ms.toFixed(1)} ms`}
              hint={`retrieval ${response.semantic.timing.retrieval_ms.toFixed(2)} ms`}
            />
          </div>

          <div className="versus">
            {(['keyword', 'semantic'] as const).map((side) => {
              const panel = response[side]
              const semantic = side === 'semantic'
              return (
                <section className="versus__col" key={side}>
                  <header className={`versus__head ${semantic ? 'versus__head--semantic' : ''}`}>
                    <h3>{semantic ? '🧲 Vector · semantic' : '🔤 BM25 · keyword'}</h3>
                    <span className="versus__timing">{panel.timing.end_to_end_ms.toFixed(2)} ms</span>
                  </header>
                  {panel.results.length ? (
                    panel.results.map((hit, position) => (
                      <ResultCard
                        key={hit.chunk_id}
                        hit={hit}
                        rank={position + 1}
                        semantic={semantic}
                        query={ran}
                      />
                    ))
                  ) : (
                    <Notice kind="warn">No matching passages for this method.</Notice>
                  )}
                </section>
              )
            })}
          </div>

          <div className="row" style={{ marginTop: 26 }}>
            <Notice kind="info">
              Overlap alone does not say which ranking is <em>better</em> — that needs relevance judgments.
            </Notice>
            <Link className="btn btn--primary" to="/app/evaluation">
              Next: grade and evaluate →
            </Link>
          </div>
        </>
      ) : null}
    </>
  )
}
