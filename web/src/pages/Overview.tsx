/** Dashboard: counters, the guided workflow, and recent activity. */
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Empty, Metric, PageHead, ScoreGuide, useAsync } from '../components'
import { useStats } from '../stats-context'

export default function Overview() {
  const { stats } = useStats()
  const { data: history } = useAsync(() => api.history(8), [])

  const steps = [
    {
      title: 'Add documents',
      detail: 'Build your searchable library.',
      to: '/app/upload',
      done: Boolean(stats?.documents),
    },
    {
      title: 'Run a search',
      detail: 'Try a natural-language or exact-term query.',
      to: '/app/semantic',
      done: Boolean(stats?.has_search),
    },
    {
      title: 'Compare methods',
      detail: 'Run one query through both rankers.',
      to: '/app/compare',
      done: Boolean(stats?.has_comparison),
    },
    {
      title: 'Evaluate results',
      detail: 'Grade passages and read the quality metrics.',
      to: '/app/evaluation',
      done: Boolean(stats?.has_experiment),
    },
  ]

  return (
    <>
      <PageHead eyebrow="Document search workspace" title="Search your documents.">
        Bring your files together, find passages by keyword or by meaning, then compare what each method returns.
      </PageHead>

      <div className="metric-row">
        <Metric label="Documents" value={stats?.documents ?? '—'} hint="indexed and searchable" />
        <Metric label="Passages" value={stats?.chunks ?? '—'} hint="word-window chunks" />
        <Metric label="Searches" value={stats?.searches ?? '—'} hint="recorded in history" />
      </div>

      <h2 style={{ fontSize: 22, marginBottom: 16 }}>Your workflow</h2>
      <div className="sticker-grid" style={{ marginBottom: 30 }}>
        {steps.map((step, index) => {
          // A step opens once the previous one is complete.
          const unlocked = index === 0 || steps[index - 1].done
          return (
            <div
              className="sticker"
              key={step.title}
              style={{ '--rot': `${index % 2 ? 1.2 : -1.2}deg` } as React.CSSProperties}
            >
              <div
                className="sticker__seal"
                style={{ background: step.done ? 'var(--turquoise)' : unlocked ? 'var(--gold)' : '#d8d3c8' }}
                aria-hidden
              >
                {step.done ? '✓' : index + 1}
              </div>
              <h3>{step.title}</h3>
              <p>{step.detail}</p>
              <div style={{ marginTop: 14 }}>
                {step.done ? (
                  <Link className="btn btn--sm" to={step.to}>
                    Revisit
                  </Link>
                ) : unlocked ? (
                  <Link className="btn btn--sm btn--primary" to={step.to}>
                    Continue →
                  </Link>
                ) : (
                  <span className="chip chip--ghost">After step {index}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div style={{ marginBottom: 30 }}>
        <ScoreGuide />
      </div>

      <h2 style={{ fontSize: 22, marginBottom: 16 }}>Recent activity</h2>
      {history && history.length ? (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Time</th>
                <th>Query</th>
                <th>Method</th>
                <th>Measured</th>
                <th>Scope</th>
                <th>Results</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty art="🗂️" title="No searches yet">
          <p className="muted tiny" style={{ maxWidth: '44ch', margin: 0 }}>
            Add a document to begin. The sample file in <code>samples/</code> is a good first test.
          </p>
          <Link className="btn btn--primary" to="/app/upload">
            Add documents →
          </Link>
        </Empty>
      )}
    </>
  )
}
