import type { Priority } from '../api/types'

const STYLES: Record<Priority, string> = {
  high: 'bg-red-100 text-red-800',
  normal: 'bg-slate-100 text-slate-700',
  low: 'bg-slate-100 text-slate-500',
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STYLES[priority]}`}
    >
      {priority}
    </span>
  )
}
