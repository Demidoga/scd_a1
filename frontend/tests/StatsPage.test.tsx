import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { StatsPage } from '../src/pages/StatsPage'

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

describe('StatsPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('displays the aggregate totals and the X-Cache header state', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            total: 42,
            by_status: { open: 10, resolved: 32 },
            by_category: { roads: 20, water: 22 },
            by_priority: { high: 5, normal: 30, low: 7 },
          },
          { headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT' } },
        ),
      ),
    )

    render(<StatsPage />)

    expect(await screen.findByText('42')).toBeInTheDocument()
    expect(await screen.findByTestId('cache-status')).toHaveTextContent('X-Cache: HIT')
  })

  it('shows MISS when the backend reports a cache miss', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            total: 1,
            by_status: { open: 1 },
            by_category: { roads: 1 },
            by_priority: { normal: 1 },
          },
          { headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS' } },
        ),
      ),
    )

    render(<StatsPage />)

    expect(await screen.findByTestId('cache-status')).toHaveTextContent('X-Cache: MISS')
  })
})
