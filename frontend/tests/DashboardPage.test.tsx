import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { DashboardPage } from '../src/pages/DashboardPage'
import type { ComplaintResponse } from '../src/api/types'

function complaint(overrides: Partial<ComplaintResponse> = {}): ComplaintResponse {
  return {
    id: '11111111-1111-1111-1111-111111111111',
    text: 'Streetlight has been out for a week.',
    location: '5 Oak Avenue',
    reporter_contact: null,
    category: 'streetlights',
    priority: 'normal',
    status: 'open',
    allowed_transitions: ['in_progress', 'rejected'],
    ai_summary: 'Broken streetlight.',
    triaged_by: 'rules',
    triage_latency_ms: 5,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('refetches with the selected filter and resets to page 1', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ items: [complaint()], total: 1, page: 1, page_size: 20 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const user = userEvent.setup()
    render(<DashboardPage />)

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))

    await user.selectOptions(screen.getByLabelText(/filter by status/i), 'open')

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    const secondCallUrl = fetchMock.mock.calls[1][0] as string
    expect(secondCallUrl).toContain('status=open')
    expect(secondCallUrl).toContain('page=1')
  })

  it('requests the next page when Next is clicked', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ items: [complaint()], total: 50, page: 1, page_size: 20 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const user = userEvent.setup()
    render(<DashboardPage />)

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    await user.click(await screen.findByRole('button', { name: /next/i }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    const secondCallUrl = fetchMock.mock.calls[1][0] as string
    expect(secondCallUrl).toContain('page=2')
  })

  it('only offers the actions the backend lists in allowed_transitions', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({
          items: [complaint({ status: 'open', allowed_transitions: ['in_progress', 'rejected'] })],
          total: 1,
          page: 1,
          page_size: 20,
        }),
      ),
    )

    render(<DashboardPage />)

    expect(await screen.findByRole('button', { name: /mark in progress/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /resolve/i })).not.toBeInTheDocument()
  })

  it('renders the backend 409 message verbatim on an illegal transition', async () => {
    const user = userEvent.setup()
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        // Stale row: another operator already changed it, so the server rejects the click.
        jsonResponse({
          items: [complaint({ status: 'open', allowed_transitions: ['resolved'] })],
          total: 1,
          page: 1,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          { detail: 'Invalid status transition: open -> resolved' },
          { status: 409 },
        ),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<DashboardPage />)
    await screen.findByRole('button', { name: /resolve/i })

    await user.click(screen.getByRole('button', { name: /resolve/i }))

    expect(
      await screen.findByText('Invalid status transition: open -> resolved'),
    ).toBeInTheDocument()
  })
})
