import type { Status } from '../api/types'

// Deliberately does NOT encode the transition table — see
// docs/architecture/backend.md §4. The backend sends each complaint's
// `allowed_transitions`, and this component only renders a button for each
// of those. The backend remains the sole authority: a click is still
// validated server-side, and a 409 is shown verbatim (see DashboardPage).

const ACTIONS: { target: Status; label: string; className: string }[] = [
  {
    target: 'in_progress',
    label: 'Mark in progress',
    className: 'bg-amber-500/10 text-amber-300 ring-amber-500/20 hover:bg-amber-500/20',
  },
  {
    target: 'resolved',
    label: 'Resolve',
    className: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/20 hover:bg-emerald-500/20',
  },
  {
    target: 'rejected',
    label: 'Reject',
    className: 'bg-rose-500/10 text-rose-300 ring-rose-500/20 hover:bg-rose-500/20',
  },
]

interface Props {
  allowedTransitions: Status[]
  disabled?: boolean
  onTransition: (target: Status) => void
}

export function StatusTransitionActions({ allowedTransitions, disabled, onTransition }: Props) {
  if (allowedTransitions.length === 0) {
    return <span className="text-xs text-zinc-500">No further actions</span>
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {ACTIONS.filter((a) => allowedTransitions.includes(a.target)).map((action) => (
        <button
          key={action.target}
          type="button"
          disabled={disabled}
          onClick={() => onTransition(action.target)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium ring-1 ring-inset transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${action.className}`}
        >
          {action.label}
        </button>
      ))}
    </div>
  )
}
