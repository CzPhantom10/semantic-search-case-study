/** Read-only view of the active configuration and where data lives. */
import { api } from '../api'
import { Notice, PageHead, Spinner, useAsync } from '../components'

export default function SettingsPage() {
  const { data, loading, error } = useAsync(() => api.settings(), [])

  const groups = data
    ? [
        {
          title: 'Embedding model',
          icon: '🧠',
          color: 'var(--violet)',
          rows: [
            ['Model', data.embedding_model],
            ['Dimensions', data.embedding_dimensions ?? 'determined on load'],
            ['Device', data.device],
            ['Status', data.model_loaded ? 'loaded in memory' : 'loads on first semantic search'],
          ] as const,
        },
        {
          title: 'Chunking and retrieval',
          icon: '✂️',
          color: 'var(--turquoise)',
          rows: [
            ['Chunk size', `${data.chunk_size_words} words`],
            ['Chunk overlap', `${data.chunk_overlap_words} words`],
            ['Default top K', data.default_top_k],
            ['Distance metric', data.distance_metric],
            ['Timing runs', data.latency_runs],
            ['Max upload', `${data.max_upload_mb} MB`],
          ] as const,
        },
        {
          title: 'Local storage',
          icon: '💾',
          color: 'var(--gold)',
          rows: [
            ['Vector collection', data.chroma_path],
            ['SQLite database', data.sqlite_path],
          ] as const,
        },
      ]
    : []

  return (
    <>
      <PageHead eyebrow="Configuration" title="Settings">
        These values come from <code>config.py</code> and your <code>.env</code>. They are read-only here — change
        the environment variables and restart the API to apply new settings.
      </PageHead>

      {loading ? <Spinner /> : null}
      {error ? <Notice kind="error">{error}</Notice> : null}

      <div className="sticker-grid">
        {groups.map((group, index) => (
          <div
            className="sticker"
            key={group.title}
            style={{ '--rot': `${index % 2 ? 1 : -1}deg` } as React.CSSProperties}
          >
            <div className="sticker__seal" style={{ background: group.color }} aria-hidden>
              {group.icon}
            </div>
            <h3>{group.title}</h3>
            <div className="stack" style={{ gap: 9, marginTop: 13 }}>
              {group.rows.map(([label, value]) => (
                <div key={label}>
                  <div className="metric__label">{label}</div>
                  <div
                    className="mono"
                    style={{ fontSize: 12.5, color: 'var(--body)', marginTop: 2, overflowWrap: 'anywhere' }}
                  >
                    {String(value)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 24, maxWidth: '76ch' }}>
        <Notice kind="info">
          Override with <code>SEMSEARCH_MODEL</code>, <code>SEMSEARCH_CHUNK_SIZE</code>,{' '}
          <code>SEMSEARCH_CHUNK_OVERLAP</code>, <code>SEMSEARCH_TOP_K</code>, <code>SEMSEARCH_LATENCY_RUNS</code> or{' '}
          <code>SEMSEARCH_DEVICE</code>. Changing the model or the chunk settings requires deleting and re-indexing
          your documents, because the stored vectors must match the chosen model's dimensions.
        </Notice>
      </div>
    </>
  )
}
