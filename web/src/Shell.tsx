/**
 * Workspace frame: brand, workflow-aware navigation, and the routed outlet.
 *
 * Navigation mirrors the guided workflow — search is unavailable until a
 * document is indexed, comparison until a search has run, evaluation until a
 * paired comparison exists. Locked steps stay visible so the path is legible.
 */
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from './api'
import type { Stats } from './api'
import { useAsync } from './components'
import { StatsContext } from './stats-context'

interface NavItem {
  to: string
  icon: string
  label: string
  /** Which workflow flag must be true before this view opens. */
  requires?: keyof Stats
  hint?: string
}

const ITEMS: NavItem[] = [
  { to: '/app', icon: '◈', label: 'Overview' },
  { to: '/app/upload', icon: '📥', label: 'Add documents' },
  { to: '/app/library', icon: '📚', label: 'Library' },
  { to: '/app/semantic', icon: '🧲', label: 'Semantic search', requires: 'documents', hint: 'Index a document first' },
  { to: '/app/keyword', icon: '🔤', label: 'Keyword search', requires: 'documents', hint: 'Index a document first' },
  { to: '/app/compare', icon: '⚖️', label: 'Compare', requires: 'documents', hint: 'Index a document first' },
  { to: '/app/evaluation', icon: '📊', label: 'Evaluation', requires: 'has_comparison', hint: 'Run a comparison first' },
  { to: '/app/history', icon: '🕘', label: 'History' },
  { to: '/app/settings', icon: '⚙️', label: 'Settings' },
]

export default function Shell() {
  const location = useLocation()
  // Re-read the workflow flags on every navigation so locks open promptly.
  const { data: stats, reload } = useAsync(() => api.stats(), [location.pathname])

  const unlocked = (item: NavItem) => {
    if (!item.requires) return true
    if (!stats) return false
    return Boolean(stats[item.requires])
  }

  return (
    <StatsContext.Provider value={{ stats, reloadStats: reload }}>
      <div className="shell">
        <aside className="shell__sidebar">
          <div className="shell__sidebar-inner">
            <NavLink to="/" className="brand">
              <span className="brand__mark" aria-hidden>
                🔎
              </span>
              <span>
                <span className="brand__name">
                  Semantic
                  <br />
                  Search Studio
                </span>
                <span className="brand__caption">Local workspace</span>
              </span>
            </NavLink>

            <nav className="nav">
              {ITEMS.map((item) => {
                const open = unlocked(item)
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/app'}
                    title={open ? item.label : item.hint}
                    className={({ isActive }) =>
                      ['nav__link', isActive && open ? 'nav__link--active' : '', open ? '' : 'nav__link--locked']
                        .filter(Boolean)
                        .join(' ')
                    }
                    aria-disabled={!open}
                  >
                    <span className="nav__icon" aria-hidden>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                    {open ? null : (
                      <span className="nav__lock" aria-hidden>
                        🔒
                      </span>
                    )}
                  </NavLink>
                )
              })}
            </nav>

            <div className="spacer" />

            <div className="card card--tint card--flat" style={{ padding: '12px 14px' }}>
              <div className="tiny muted" style={{ lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--text-strong)' }}>{stats?.documents ?? 0}</strong> documents ·{' '}
                <strong style={{ color: 'var(--text-strong)' }}>{stats?.chunks ?? 0}</strong> passages
                <br />
                All data stays on this machine.
              </div>
            </div>
          </div>
        </aside>

        <main className="shell__main">
          <Outlet />
        </main>
      </div>
    </StatsContext.Provider>
  )
}
