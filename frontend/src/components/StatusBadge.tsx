import type { Status } from '../api/types'

const STYLES: Record<Status, string> = {
  open: 'bg-sky-500/10 text-sky-300 ring-sky-500/25',
  in_progress: 'bg-amber-500/10 text-amber-300 ring-amber-500/25',
  resolved: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/25',
  rejected: 'bg-rose-500/10 text-rose-300 ring-rose-500/25',
}

const DOT: Record<Status, string> = {
  open: 'bg-sky-400',
  in_progress: 'bg-amber-400',
  resolved: 'bg-emerald-400',
  rejected: 'bg-rose-400',
}

const LABELS: Record<Status, string> = {
  open: 'Open',
  in_progress: 'In progress',
  resolved: 'Resolved',
  rejected: 'Rejected',
}

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${STYLES[status]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${DOT[status]}`} />
      {LABELS[status]}
    </span>
  )
}
