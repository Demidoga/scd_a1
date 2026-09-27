import { NavLink, Route, Routes } from 'react-router-dom'
import { SubmitPage } from './pages/SubmitPage'
import { DashboardPage } from './pages/DashboardPage'
import { StatsPage } from './pages/StatsPage'
import { ErrorBoundary } from './components/ErrorBoundary'

const NAV_ITEMS = [
  { to: '/', label: 'Complain', end: true },
  { to: '/dashboard', label: 'Dashboard', end: false },
  { to: '/stats', label: 'Statistics', end: false },
]

function navClass({ isActive }: { isActive: boolean }) {
  return `rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors duration-150 ${
    isActive
      ? 'bg-zinc-800 text-white'
      : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-50'
  }`
}

export default function App() {
  return (
    <div className="min-h-screen bg-zinc-950">
      <header className="sticky top-0 z-10 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center gap-4 overflow-x-auto px-4 py-4 sm:gap-8 sm:px-6">
          <div className="flex shrink-0 items-center gap-2.5">
            
            <span className="text-[15px] font-extrabold tracking-tight text-zinc-50 sm:text-[24px]">
              CIVIC-PULSE
            </span>
          </div>
          <nav className="flex items-end shrink-0 gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
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
