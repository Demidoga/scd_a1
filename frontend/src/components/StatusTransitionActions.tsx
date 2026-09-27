import type { Status } from '../api/types'

// Deliberately does NOT encode the transition table (open -> in_progress ->
// resolved/rejected, etc) — see docs/architecture/backend.md §4. The only
// UI-level knowledge here is "terminal statuses have no further actions",
// which is a property of the complaint's own current status, not a copy of
// the legality table. Every button click still goes through the backend,
// which is the sole authority on whether a transition is legal; an illegal
// click surfaces the backend's 409 message verbatim (see DashboardPage).
const TERMINAL: Status[] = ['resolved', 'rejected']

const ACTIONS: { target: Status; label: string; className: string }[] = [
  { target: 'in_progress', label: 'Mark in progress', className: 'bg-amber-600 hover:bg-amber-500' },
  { target: 'resolved', label: 'Resolve', className: 'bg-green-600 hover:bg-green-500' },
  { target: 'rejected', label: 'Reject', className: 'bg-red-600 hover:bg-red-500' },
]

interface Props {
  status: Status
  disabled?: boolean
  onTransition: (target: Status) => void
}

export function StatusTransitionActions({ status, disabled, onTransition }: Props) {
  if (TERMINAL.includes(status)) {
    return <span className="text-xs text-slate-400">No further actions</span>
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {ACTIONS.filter((a) => a.target !== status).map((action) => (
        <button
          key={action.target}
          type="button"
          disabled={disabled}
          onClick={() => onTransition(action.target)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 ${action.className}`}
        >
          {action.label}
        </button>
      ))}
    </div>
  )
}
