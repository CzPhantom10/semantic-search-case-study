/** Recorded searches, with the saved result payload for any one of them. */
import { useState } from 'react'
import { api } from '../api'
import { Empty, Notice, PageHead, ResultCard, Spinner, useAsync } from '../components'

export default function History() {
  const { data: rows, loading, error } = useAsync(() => api.history(500), [])
  const [open, setOpen] = useState<number | null>(null)

  const selected = rows?.find((row) => row.search_id === open) ?? null

  const exportCsv = () => {
    if (!rows?.length) return
    const header = ['timestamp', 'query_text', 'search_method', 'end_to_end_ms', 'retrieval_ms', 'timing_scope', 'result_count']
    const body = rows.map((row) =>
      [
        row.timestamp,
        `"${row.query_text.replace(/"/g, '""')}"`,
        row.search_method,
        row.end_to_end_ms ?? row.latency_ms,
        row.retrieval_ms ?? '',
        row.timing_scope,
        row.result_count,
      ].join(','),
    )
    const blob = new Blob([[header.join(','), ...body].join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'search_history.csv'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <PageHead eyebrow="Record" title="Search history">
        Every search is recorded with its measured timing and the passages it returned, so a run can be revisited
        long after the fact.
      </PageHead>

      {error ? <Notice kind="error">{error}</Notice> : null}
      {loading ? <Spinner /> : null}

      {rows && !rows.length ? (
        <Empty art="🕘" title="No searches recorded yet">
          <p className="muted tiny" style={{ margin: 0, maxWidth: '44ch' }}>
            History appears here after your first query.
          </p>
        </Empty>
      ) : null}

      {rows && rows.length ? (
        <>
          <div className="row" style={{ marginBottom: 16 }}>
            <span className="chip chip--ghost">{rows.length} recorded searches</span>
            <div className="spacer" />
            <button className="btn btn--sm" onClick={exportCsv}>
              ⬇ Export history CSV
            </button>
          </div>

          <div className="table-wrap" style={{ marginBottom: 22 }}>
            <table className="data">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Query</th>
                  <th>Method</th>
                  <th>Measured</th>
                  <th>Scope</th>
                  <th>Results</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.search_id}>
                    <td className="num tiny">{row.timestamp.replace('T', ' ').replace('+00:00', '')}</td>
                    <td>{row.query_text}</td>
                    <td>
                      <span className={`chip ${row.search_method.includes('Semantic') ? 'chip--violet' : 'chip--gold'}`}>
                        {row.search_method}
                      </span>
                    </td>
                    <td className="num">{(row.end_to_end_ms ?? row.latency_ms).toFixed(2)} ms</td>
                    <td className="tiny muted">{row.timing_scope}</td>
                    <td className="num">{row.result_count}</td>
                    <td>
                      <button
                        className="btn btn--sm"
                        onClick={() => setOpen(open === row.search_id ? null : row.search_id)}
                      >
                        {open === row.search_id ? 'Hide' : 'View'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selected ? (
            <>
              <h2 style={{ fontSize: 20, marginBottom: 6 }}>Saved results</h2>
              <p className="tiny muted" style={{ marginTop: 0, marginBottom: 16 }}>
                {selected.search_method} · “{selected.query_text}” ·{' '}
                {selected.timestamp.replace('T', ' ').replace('+00:00', '')}
              </p>
              {selected.results.length ? (
                <div className="results">
                  {selected.results.map((hit, position) => (
                    <ResultCard
                      key={`${hit.chunk_id}-${position}`}
                      hit={hit}
                      rank={position + 1}
                      semantic={selected.search_method.includes('Semantic')}
                      query={selected.query_text}
                    />
                  ))}
                </div>
              ) : (
                <Notice kind="warn">This search recorded no results.</Notice>
              )}
            </>
          ) : null}
        </>
      ) : null}
    </>
  )
}
