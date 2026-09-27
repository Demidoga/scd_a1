interface Props {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pageSize, total, onPageChange }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="mt-4 flex items-center justify-between gap-4">
      <p className="text-sm text-zinc-400">
        Page <span className="font-medium text-zinc-200">{page}</span> of{' '}
        <span className="font-medium text-zinc-200">{totalPages}</span>
        <span className="text-zinc-600"> · </span>
        <span className="tabular-nums">{total}</span> total
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3.5 py-1.5 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-zinc-900"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3.5 py-1.5 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-zinc-900"
        >
          Next
        </button>
      </div>
    </div>
  )
}
