/** Drag-and-drop ingestion with a per-file outcome report. */
import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { Settings, UploadOutcome } from '../api'
import { Notice, PageHead, Spinner, useAsync } from '../components'
import { useStats } from '../stats-context'

const ACCEPTED = ['.pdf', '.docx', '.txt']

export default function Upload() {
  const { reloadStats } = useStats()
  const { data: settings } = useAsync<Settings>(() => api.settings(), [])
  const [queued, setQueued] = useState<File[]>([])
  const [outcomes, setOutcomes] = useState<UploadOutcome[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [over, setOver] = useState(false)
  const picker = useRef<HTMLInputElement>(null)

  const accept = (incoming: FileList | null) => {
    if (!incoming) return
    const files = Array.from(incoming).filter((file) =>
      ACCEPTED.some((extension) => file.name.toLowerCase().endsWith(extension)),
    )
    setQueued((current) => [...current, ...files])
    setOutcomes(null)
  }

  const index = async () => {
    if (!queued.length) return
    setBusy(true)
    setError(null)
    try {
      const response = await api.upload(queued)
      setOutcomes(response.results)
      setQueued([])
      reloadStats()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setBusy(false)
    }
  }

  const indexedCount = outcomes?.filter((outcome) => outcome.status === 'indexed').length ?? 0

  return (
    <>
      <PageHead eyebrow="Library" title="Add documents">
        Upload files to create or expand your searchable library. Each file is extracted, split into sentence-aware
        word windows, embedded locally, and written to the persistent vector collection.
      </PageHead>

      <div
        className="dropzone"
        data-over={over}
        onClick={() => picker.current?.click()}
        onDragOver={(event) => {
          event.preventDefault()
          setOver(true)
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(event) => {
          event.preventDefault()
          setOver(false)
          accept(event.dataTransfer.files)
        }}
      >
        <div style={{ fontSize: 40 }} aria-hidden>
          📥
        </div>
        <h3>Drop files here</h3>
        <p className="tiny muted" style={{ margin: 0, maxWidth: '50ch', lineHeight: 1.6 }}>
          PDF, DOCX and TXT · up to {settings?.max_upload_mb ?? 50} MB per file. Scanned, image-only PDFs need OCR,
          which this version does not include.
        </p>
        <span className="btn btn--sm">Browse files</span>
        <input
          ref={picker}
          type="file"
          multiple
          accept={ACCEPTED.join(',')}
          style={{ display: 'none' }}
          onChange={(event) => accept(event.target.files)}
        />
      </div>

      {queued.length ? (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="row">
            <strong style={{ fontFamily: 'var(--font-comic)' }}>
              {queued.length} file{queued.length === 1 ? '' : 's'} ready
            </strong>
            <div className="spacer" />
            <button className="btn btn--sm" onClick={() => setQueued([])} disabled={busy}>
              Clear
            </button>
            <button className="btn btn--sm btn--primary" onClick={index} disabled={busy}>
              {busy ? <Spinner /> : null}
              {busy ? 'Indexing…' : 'Index selected files'}
            </button>
          </div>
          <div className="row" style={{ marginTop: 13, gap: 7 }}>
            {queued.map((file, position) => (
              <span className="chip" key={`${file.name}-${position}`}>
                {file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {busy ? (
        <div style={{ marginTop: 18 }}>
          <Notice kind="info">
            Embedding passages locally. The first run downloads the model, which can take a minute.
          </Notice>
        </div>
      ) : null}

      {error ? (
        <div style={{ marginTop: 18 }}>
          <Notice kind="error">{error}</Notice>
        </div>
      ) : null}

      {outcomes ? (
        <div className="stack" style={{ marginTop: 20 }}>
          {outcomes.map((outcome, position) => (
            <Notice
              key={`${outcome.filename}-${position}`}
              kind={outcome.status === 'indexed' ? 'success' : outcome.status === 'skipped' ? 'warn' : 'error'}
            >
              <strong>{outcome.filename}</strong> — {outcome.detail}
            </Notice>
          ))}
          {indexedCount ? (
            <div className="row">
              <Link className="btn btn--primary" to="/app/compare">
                Continue to compare →
              </Link>
              <Link className="btn" to="/app/library">
                View library
              </Link>
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  )
}
