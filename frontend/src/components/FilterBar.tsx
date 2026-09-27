import { CATEGORIES, PRIORITIES, STATUSES } from '../api/types'
import type { Category, Priority, Status } from '../api/types'

export interface Filters {
  category?: Category
  priority?: Priority
  status?: Status
}

interface Props {
  filters: Filters
  onChange: (filters: Filters) => void
}

export function FilterBar({ filters, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-4">
      <label className="flex flex-col text-sm text-slate-600">
        Category
        <select
          aria-label="Filter by category"
          className="mt-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={filters.category ?? ''}
          onChange={(e) =>
            onChange({ ...filters, category: (e.target.value || undefined) as Category | undefined })
          }
        >
          <option value="">All</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-sm text-slate-600">
        Priority
        <select
          aria-label="Filter by priority"
          className="mt-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={filters.priority ?? ''}
          onChange={(e) =>
            onChange({ ...filters, priority: (e.target.value || undefined) as Priority | undefined })
          }
        >
          <option value="">All</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-sm text-slate-600">
        Status
        <select
          aria-label="Filter by status"
          className="mt-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          value={filters.status ?? ''}
          onChange={(e) =>
            onChange({ ...filters, status: (e.target.value || undefined) as Status | undefined })
          }
        >
          <option value="">All</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>

      {(filters.category || filters.priority || filters.status) && (
        <button
          type="button"
          onClick={() => onChange({})}
          className="text-sm font-medium text-slate-500 hover:text-slate-800"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
