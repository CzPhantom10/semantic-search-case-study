/** Single-method retrieval view, shared by the semantic and keyword routes. */
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import type { SearchResponse } from '../api'
import { Empty, Notice, PageHead, ResultCard, ScoreGuide, Spinner, TimingLine } from '../components'

const COPY = {
  Semantic: {
    eyebrow: 'Semantic retrieval',
    title: 'Search by meaning',
    blurb:
      'Your query is embedded into the same 384-dimensional space as the passages, then ranked by cosine distance. Related wording matches even when no term is shared.',
    placeholder: 'How can I protect my computer from hackers?',
  },
  Keyword: {
    eyebrow: 'Lexical retrieval',
    title: 'Search by keywords',
    blurb:
      'BM25 scores each passage by the query terms it literally contains, weighted by term rarity and passage length. Exact wording wins; paraphrases are invisible.',
    placeholder: 'firewall configuration',
  },
}

export default function Search({ method }: { method: 'Semantic' | 'Keyword' }) {
  const copy = COPY[method]
  const [params] = useSearchParams()
  const [query, setQuery] = useState(params.get('q') ?? '')
  const [k, setK] = useState(5)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [ran, setRan] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    const trimmed = query.trim()
    if (!trimmed) return
    setBusy(true)
    setError(null)
    try {
      setResponse(await api.search(trimmed, method, k))
      setRan(trimmed)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause))
      setResponse(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHead eyebrow={copy.eyebrow} title={copy.title}>
        {copy.blurb}
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
            placeholder={copy.placeholder}
          />
        </div>
        <div className="field searchbar__k">
          <label htmlFor="k">Results</label>
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
          {busy ? 'Searching…' : 'Search'}
        </button>
      </div>

      <div style={{ margin: '20px 0' }}>
        <ScoreGuide />
      </div>

      {error ? <Notice kind="error">{error}</Notice> : null}

      {response ? (
        <>
          <div className="row" style={{ marginBottom: 14 }}>
            <span className={`chip ${method === 'Semantic' ? 'chip--violet' : 'chip--gold'}`}>
              {method === 'Semantic' ? '🧲 Vector · semantic' : '🔤 BM25 · keyword'}
            </span>
            <span className="chip chip--ghost">
              {response.results.length} of top {k}
            </span>
            <div className="spacer" />
            <TimingLine timing={response.timing} />
          </div>

          {response.results.length ? (
            <>
              <div className="results">
                {response.results.map((hit, position) => (
                  <ResultCard
                    key={hit.chunk_id}
                    hit={hit}
                    rank={position + 1}
                    semantic={method === 'Semantic'}
                    query={ran}
                  />
                ))}
              </div>
              <div className="row" style={{ marginTop: 24 }}>
                <Link className="btn btn--primary" to={`/app/compare?q=${encodeURIComponent(ran)}`}>
                  Next: compare both methods →
                </Link>
              </div>
            </>
          ) : (
            <Empty art="🤷" title="No matching passages">
              <p className="muted tiny" style={{ margin: 0, maxWidth: '44ch' }}>
                {method === 'Keyword'
                  ? 'BM25 found none of your terms. Try different wording, or switch to semantic search.'
                  : 'Nothing was close enough in the vector space. Try a longer, more descriptive query.'}
              </p>
            </Empty>
          )}
        </>
      ) : null}
    </>
  )
}
