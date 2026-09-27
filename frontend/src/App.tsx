import { NavLink, Route, Routes } from 'react-router-dom'
import { SubmitPage } from './pages/SubmitPage'
import { DashboardPage } from './pages/DashboardPage'
import { StatsPage } from './pages/StatsPage'
import { ErrorBoundary } from './components/ErrorBoundary'

const NAV_ITEMS = [
  { to: '/', label: 'Submit', end: true },
  { to: '/dashboard', label: 'Dashboard', end: false },
  { to: '/stats', label: 'Statistics', end: false },
]

function navClass({ isActive }: { isActive: boolean }) {
  return `rounded-md px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
  }`
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
          <span className="text-lg font-semibold text-slate-900">CivicPulse</span>
          <nav className="flex gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<SubmitPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/stats" element={<StatsPage />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  )
}
