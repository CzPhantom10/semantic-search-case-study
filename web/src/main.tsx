import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { MoodToggle, useMood } from './components'
import Shell from './Shell'
import Landing from './pages/Landing'
import Overview from './pages/Overview'
import Upload from './pages/Upload'
import Library from './pages/Library'
import Search from './pages/Search'
import Compare from './pages/Compare'
import Evaluation from './pages/Evaluation'
import History from './pages/History'
import SettingsPage from './pages/Settings'
import './styles.css'

// Paint the mood before React mounts so the first frame is already themed.
document.documentElement.dataset.mood = localStorage.getItem('studio-mood') ?? 'day'

/**
 * Owns the day/night mood for the whole app. The landing page lives outside
 * the workspace shell, so the toggle and the `data-mood` attribute have to sit
 * above both of them — otherwise every design token is undefined on `/`.
 */
function Root() {
  const { mood, toggle } = useMood()
  return (
    <>
      <Outlet />
      <MoodToggle mood={mood} onToggle={toggle} />
    </>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Root />}>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<Shell />}>
            <Route index element={<Overview />} />
            <Route path="upload" element={<Upload />} />
            <Route path="library" element={<Library />} />
            <Route path="semantic" element={<Search method="Semantic" />} />
            <Route path="keyword" element={<Search method="Keyword" />} />
            <Route path="compare" element={<Compare />} />
            <Route path="evaluation" element={<Evaluation />} />
            <Route path="history" element={<History />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
