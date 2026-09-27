import type { Priority } from '../api/types'

const STYLES: Record<Priority, string> = {
  high: 'bg-rose-500/10 text-rose-300 ring-rose-500/25',
  normal: 'bg-zinc-500/10 text-zinc-300 ring-zinc-500/20',
  low: 'bg-zinc-500/5 text-zinc-500 ring-zinc-500/10',
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize ring-1 ring-inset ${STYLES[priority]}`}
    >
      {priority}
    </span>
  )
}
