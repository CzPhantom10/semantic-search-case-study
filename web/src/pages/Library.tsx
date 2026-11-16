/** Indexed-document inventory with cascading deletion. */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Empty, Notice, PageHead, Spinner, useAsync } from '../components'
import { useStats } from '../stats-context'

export default function Library() {
  const { reloadStats } = useStats()
  const { data: documents, loading, error, reload } = useAsync(() => api.documents(), [])
  const [removing, setRemoving] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  const remove = async (id: string, filename: string) => {
    if (!confirm(`Delete "${filename}"? Its passages, vectors and relevance judgments are removed too.`)) return
    setRemoving(id)
    setFailure(null)
    try {
      await api.deleteDocument(id)
      reload()
      reloadStats()
    } catch (cause) {
      setFailure(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setRemoving(null)
    }
  }

  return (
    <>
      <PageHead eyebrow="Library" title="Document library">
        Review indexed files and remove the ones you no longer need. Deleting a document also drops its vectors and
        cascades its passages and relevance judgments.
      </PageHead>

      {error ? <Notice kind="error">{error}</Notice> : null}
      {failure ? <Notice kind="error">{failure}</Notice> : null}
      {loading ? <Spinner /> : null}

      {documents && !documents.length ? (
        <Empty art="📚" title="Nothing indexed yet">
          <p className="muted tiny" style={{ maxWidth: '44ch', margin: 0 }}>
            Upload a PDF, DOCX or TXT file to build your searchable library.
          </p>
          <Link className="btn btn--primary" to="/app/upload">
            Add documents →
          </Link>
        </Empty>
      ) : null}

      <div className="stack">
        {documents?.map((document) => (
          <div className="card" key={document.document_id}>
            <div className="row">
              <span style={{ fontSize: 22 }} aria-hidden>
                {document.file_type === 'pdf' ? '📕' : document.file_type === 'docx' ? '📘' : '📄'}
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontFamily: 'var(--font-comic)', fontWeight: 700, fontSize: 15 }}>
                  {document.filename}
                </div>
                <div className="tiny muted" style={{ marginTop: 3 }}>
                  {document.total_chunks} passages · {document.total_pages} pages with text · added{' '}
                  {document.upload_timestamp.replace('T', ' ').replace('+00:00', '')}
                </div>
              </div>
              <div className="spacer" />
              <span className={`chip ${document.processing_status === 'indexed' ? 'chip--turquoise' : 'chip--gold'}`}>
                {document.processing_status}
              </span>
              <button
                className="btn btn--sm btn--danger"
                onClick={() => remove(document.document_id, document.filename)}
                disabled={removing === document.document_id}
              >
                {removing === document.document_id ? 'Deleting…' : 'Delete'}
              </button>
            </div>
            {document.error ? (
              <div style={{ marginTop: 12 }}>
                <Notice kind="error">{document.error}</Notice>
              </div>
            ) : null}
          </div>
        ))}
      </div>

      {documents && documents.length ? (
        <p className="tiny muted" style={{ marginTop: 18, lineHeight: 1.6 }}>
          To re-index a file, delete it and upload the updated copy — identical contents are detected by SHA-256.
          Re-indexing in place is not supported.
        </p>
      ) : null}
    </>
  )
}
