/** Shared presentation pieces built on the toon design system. */
import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { Hit, Timing } from './api'

export function PageHead({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <header className="page-head">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {children ? <p>{children}</p> : null}
    </header>
  )
}

export function Metric({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="metric">
      <div className="metric__label">{label}</div>
      <div className="metric__value">{value}</div>
      {hint ? <div className="metric__hint">{hint}</div> : null}
    </div>
  )
}

export function Notice({ kind, children }: { kind: 'warn' | 'success' | 'error' | 'info'; children: ReactNode }) {
  return <div className={`notice notice--${kind}`}>{children}</div>
}

export function Empty({ art, title, children }: { art: string; title: string; children?: ReactNode }) {
  return (
    <div className="empty">
      <div className="empty__art">{art}</div>
      <h3>{title}</h3>
      {children}
    </div>
  )
}

export function Spinner() {
  return <span className="spinner" aria-hidden />
}

/** Coverage / progress meter with an ink-outlined fill. */
export function Meter({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(1, value)) * 100
  return (
    <div className="meter" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
      <div className="meter__fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

/* ------------------------------------------------------------------ search */

/** Escape a user query before it becomes part of a highlight regex. */
function escapeRegExp(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * Highlight query terms inside a passage. Terms are matched on word
 * boundaries so a short query like "ip" does not light up "description".
 */
function Highlighted({ text, query }: { text: string; query: string }) {
  const parts = useMemo(() => {
    const terms = Array.from(new Set(query.toLowerCase().match(/[\p{L}\p{N}]{3,}/gu) ?? []))
    if (!terms.length) return [{ text, hit: false }]
    const pattern = new RegExp(`\\b(${terms.map(escapeRegExp).join('|')})\\b`, 'giu')
    const out: { text: string; hit: boolean }[] = []
    let cursor = 0
    for (const match of text.matchAll(pattern)) {
      const start = match.index ?? 0
      if (start > cursor) out.push({ text: text.slice(cursor, start), hit: false })
      out.push({ text: match[0], hit: true })
      cursor = start + match[0].length
    }
    if (cursor < text.length) out.push({ text: text.slice(cursor), hit: false })
    return out
  }, [text, query])

  return (
    <>
      {parts.map((part, index) =>
        part.hit ? <mark key={index}>{part.text}</mark> : <span key={index}>{part.text}</span>,
      )}
    </>
  )
}

/**
 * One retrieved passage. Keyword hits carry a BM25 score (higher is better);
 * semantic hits carry a cosine distance (lower is closer), so the label and
 * the colour of the rank badge both change with the method.
 */
export function ResultCard({
  hit,
  rank,
  semantic,
  query,
}: {
  hit: Hit
  rank: number
  semantic: boolean
  query: string
}) {
  const filename = String(hit.metadata.filename ?? hit.metadata.document_name ?? 'Document')
  const page = hit.metadata.page_number
  const scoreLabel = semantic
    ? hit.distance == null
      ? '—'
      : `distance ${hit.distance.toFixed(4)}`
    : hit.score == null
      ? '—'
      : `BM25 ${hit.score.toFixed(3)}`

  return (
    <article
      className={`result fade-in ${semantic ? 'result--semantic' : ''}`}
      style={{ animationDelay: `${Math.min(rank, 8) * 40}ms` }}
    >
      <div className="result__head">
        <span className="result__rank">{rank}</span>
        <span className="result__title">{filename}</span>
        {page !== null && page !== undefined && page !== '' ? (
          <span className="chip chip--ghost">p. {String(page)}</span>
        ) : null}
        <span className={`chip result__score ${semantic ? 'chip--violet' : 'chip--gold'}`}>{scoreLabel}</span>
      </div>
      <p className="result__text">
        <Highlighted text={hit.text} query={query} />
      </p>
    </article>
  )
}

export function TimingLine({ timing }: { timing: Timing }) {
  return (
    <p className="tiny muted mono" style={{ margin: '4px 0 0' }}>
      end-to-end {timing.end_to_end_ms.toFixed(2)} ms · retrieval-only {timing.retrieval_ms.toFixed(2)} ms
    </p>
  )
}

/** The scoring legend; collapsed by default so it never crowds the results. */
export function ScoreGuide() {
  const [open, setOpen] = useState(false)
  return (
    <div className="card card--tint" style={{ padding: '14px 18px' }}>
      <div className="row">
        <strong style={{ fontFamily: 'var(--font-comic)', fontSize: 14 }}>How to read the scores</strong>
        <div className="spacer" />
        <button className="btn btn--sm" onClick={() => setOpen((value) => !value)}>
          {open ? 'Hide' : 'Show'}
        </button>
      </div>
      {open ? (
        <div className="stack" style={{ marginTop: 14 }}>
          <p className="tiny" style={{ margin: 0, lineHeight: 1.65 }}>
            <span className="chip chip--gold">BM25</span> Keyword relevance. Higher is a stronger lexical match. The
            value is unbounded and only comparable within one query.
          </p>
          <p className="tiny" style={{ margin: 0, lineHeight: 1.65 }}>
            <span className="chip chip--violet">distance</span> Cosine distance between the query vector and the
            passage vector. Lower means closer in meaning. It is a distance, not a calibrated probability.
          </p>
          <p className="tiny muted" style={{ margin: 0, lineHeight: 1.65 }}>
            The two scales are not directly comparable. Compare the <em>rankings</em> the methods produce, not the raw
            numbers.
          </p>
        </div>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ layout */

/** Scrolling marquee; the track is duplicated so the loop is seamless. */
export function Ticker({ items }: { items: string[] }) {
  const doubled = [...items, ...items]
  return (
    <div className="ticker">
      <div className="ticker__track">
        {doubled.map((item, index) => (
          <span className="ticker__item" key={index}>
            <span className="ticker__dot">●</span>
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

export function MoodToggle({ mood, onToggle }: { mood: 'day' | 'night'; onToggle: () => void }) {
  return (
    <button
      className="mood-toggle"
      onClick={onToggle}
      aria-label={`Switch to ${mood === 'day' ? 'night' : 'day'} mode`}
      title={`Switch to ${mood === 'day' ? 'night' : 'day'} mode`}
    >
      <span className="mood-toggle__knob">{mood === 'day' ? '☀' : '☾'}</span>
    </button>
  )
}

/* ------------------------------------------------------------------- hooks */

/** Mood persists across reloads and is written to the <html> element. */
export function useMood() {
  const [mood, setMood] = useState<'day' | 'night'>(
    () => (localStorage.getItem('studio-mood') as 'day' | 'night' | null) ?? 'day',
  )
  useEffect(() => {
    document.documentElement.dataset.mood = mood
    localStorage.setItem('studio-mood', mood)
  }, [mood])
  return { mood, toggle: () => setMood((value) => (value === 'day' ? 'night' : 'day')) }
}

/**
 * Run an async loader on mount and whenever `deps` change, tracking loading
 * and error state. `reload` re-runs it without changing deps.
 */
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [nonce, setNonce] = useState(0)
  // Keep the latest loader without making it a dependency of the effect.
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    loaderRef
      .current()
      .then((value) => {
        if (active) setData(value)
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : String(cause))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce])

  return { data, error, loading, reload: () => setNonce((value) => value + 1) }
}
