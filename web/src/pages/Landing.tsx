/** Marketing-style entry page: the search-first hero plus the case-study story. */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Ticker, useAsync } from '../components'

const EXAMPLES = [
  'How do I protect my computer from hackers?',
  'firewall configuration',
  'what makes a password strong',
]

const STEPS = [
  {
    icon: '📥',
    label: 'Drop in your documents',
    detail: 'PDF, DOCX or TXT. Pages are extracted, split into sentence-aware word windows, and embedded locally.',
  },
  {
    icon: '🔎',
    label: 'Ask in your own words',
    detail: 'Semantic search matches meaning through 384-dimensional vectors. Keyword search matches terms through BM25.',
  },
  {
    icon: '⚖️',
    label: 'Race the two rankers',
    detail: 'One query, the same indexed passages, both methods side by side — with retrieval-only and end-to-end timings.',
  },
  {
    icon: '📊',
    label: 'Grade and measure',
    detail: 'Mark which passages are actually relevant, then get Precision@K, Recall@K, MRR and NDCG@K over your own judgments.',
  },
]

const STICKERS = [
  {
    seal: '🧠',
    color: 'var(--violet)',
    title: 'Runs entirely on your machine',
    body: 'all-MiniLM-L6-v2 embeddings, a persistent ChromaDB collection, and SQLite. No API key, no hosted model, no data leaving the laptop.',
    rot: '-2deg',
  },
  {
    seal: '📐',
    color: 'var(--turquoise)',
    title: 'Honest measurement',
    body: 'Timings are reported in two scopes and repeated, with mean and standard deviation. Model loading is excluded so the numbers reflect query cost.',
    rot: '1.5deg',
  },
  {
    seal: '✍️',
    color: 'var(--coral)',
    title: 'Your judgments, your metrics',
    body: 'No quality score appears until a person grades the passages. Judgment coverage is recorded alongside every result.',
    rot: '-1deg',
  },
]

export default function Landing() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const { data: stats } = useAsync(() => api.stats(), [])

  const start = () => {
    const trimmed = query.trim()
    if (!stats?.documents) {
      navigate('/app/upload')
      return
    }
    navigate(trimmed ? `/app/compare?q=${encodeURIComponent(trimmed)}` : '/app/compare')
  }

  const indexed = stats?.documents ?? 0

  return (
    <div className="landing">
      <section className="landing__hero">
        <div className="landing__hero-content">
          <p className="eyebrow">Keyword search vs. semantic search</p>
          <h1 className="landing__title">
            <span className="landing__title-line">Two ways to find</span>
            <span className="landing__title-line landing__title-line--accent">the same passage.</span>
          </h1>
          <p className="landing__lede">
            Drop your documents in, then watch BM25 keyword matching race embedding-based semantic retrieval over the
            exact same passages. Grade the results yourself and see which one actually earns its reputation.
          </p>

          <div className="landing__form">
            <input
              className="input input--mono"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && start()}
              placeholder="Ask something in plain language…"
              aria-label="Your query"
            />
            <button className="btn btn--primary" onClick={start}>
              {indexed ? 'Compare both →' : 'Add documents →'}
            </button>
          </div>

          <div className="landing__examples">
            <span>Try:</span>
            {EXAMPLES.map((example) => (
              <button key={example} className="pill" onClick={() => setQuery(example)}>
                {example}
              </button>
            ))}
          </div>
        </div>
        <div className="scroll-cue" aria-hidden>
          <span />
        </div>
      </section>

      <Ticker
        items={[
          'BM25 lexical baseline',
          'all-MiniLM-L6-v2 embeddings',
          'persistent ChromaDB',
          'cosine distance',
          'Precision@K · Recall@K · MRR · NDCG@K',
          'fully local',
        ]}
      />

      <section className="landing__section">
        <p className="eyebrow">How it works</p>
        <h2 className="section-title">Four stops from a pile of files to a defensible comparison.</h2>
        <div className="steps__stops">
          {STEPS.map((step, index) => (
            <div key={step.label} className={`step-stop step-stop--${index % 2 === 0 ? 'left' : 'right'}`}>
              <div className="step-stop__sign">
                <span className="step-stop__num">{index + 1}</span>
                <div className="step-stop__icon" aria-hidden>
                  {step.icon}
                </div>
                <h3 className="step-stop__label">{step.label}</h3>
                <p className="step-stop__detail">{step.detail}</p>
              </div>
              <span className="step-stop__post" aria-hidden />
            </div>
          ))}
        </div>
      </section>

      <section className="landing__section">
        <p className="eyebrow">The matchup</p>
        <h2 className="section-title">Same passages. Two very different ideas of “relevant”.</h2>
        <div className="compare-grid">
          <div className="compare__panel compare__panel--a">
            <h3>🔤 BM25 · keyword</h3>
            <span className="chip chip--gold">lexical</span>
            <ul>
              <li>Scores passages by the query terms they literally contain, weighted by rarity and length.</li>
              <li>Fast, transparent, and easy to explain to a reader.</li>
              <li>Misses paraphrases — “hackers” will not find “malicious intrusion”.</li>
            </ul>
          </div>
          <div className="compare__panel compare__panel--b">
            <h3>🧲 Vector · semantic</h3>
            <span className="chip chip--turquoise">embedding</span>
            <ul>
              <li>Embeds the query and ranks passages by cosine distance in a 384-dimensional space.</li>
              <li>Catches paraphrase and related wording the keyword ranker cannot see.</li>
              <li>Pays an embedding cost per query, and its scores are not human-readable.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="landing__section">
        <p className="eyebrow">Why it's trustworthy</p>
        <h2 className="section-title">Built to be reported, not just demoed.</h2>
        <div className="sticker-grid">
          {STICKERS.map((sticker) => (
            <div className="sticker" key={sticker.title} style={{ '--rot': sticker.rot } as React.CSSProperties}>
              <div className="sticker__seal" style={{ background: sticker.color }} aria-hidden>
                {sticker.seal}
              </div>
              <h3>{sticker.title}</h3>
              <p>{sticker.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing__section" style={{ paddingTop: 0 }}>
        <div className="row" style={{ gap: 26, alignItems: 'center' }}>
          <div className="speech-bubble">
            <p>
              {indexed
                ? `Your library already holds ${indexed} indexed document${indexed === 1 ? '' : 's'} and ${stats?.chunks ?? 0} passages. Pick up where you left off.`
                : 'Nothing indexed yet. Start with the sample document in samples/, or drop in a PDF of your own.'}
            </p>
          </div>
          <button className="btn btn--primary" onClick={() => navigate(indexed ? '/app' : '/app/upload')}>
            {indexed ? 'Open the workspace →' : 'Index your first file →'}
          </button>
        </div>
      </section>

      <footer className="landing__foot">
        <div className="landing__status">
          <span className={`dot ${stats ? 'dot--ok' : 'dot--warn'}`} />
          <span>{stats ? 'Local services online' : 'Connecting to the local API…'}</span>
          <span className="landing__status-sep">·</span>
          <span>{stats?.chunks ?? 0} passages indexed</span>
          <span className="landing__status-sep">·</span>
          <span>{stats?.searches ?? 0} searches run</span>
        </div>
      </footer>
    </div>
  )
}
