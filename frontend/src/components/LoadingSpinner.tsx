export function LoadingSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-2.5 py-8 text-sm text-zinc-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-700 border-t-blue-400" />
      <span>{label}</span>
    </div>
  )
}
