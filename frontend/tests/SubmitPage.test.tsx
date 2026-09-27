import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { SubmitPage } from '../src/pages/SubmitPage'

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

describe('SubmitPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows client-side validation errors for text that is too short', async () => {
    const user = userEvent.setup()
    render(<SubmitPage />)

    await user.type(screen.getByLabelText(/complaint text/i), 'too short')
    await user.type(screen.getByLabelText(/location/i), 'ok location')
    await user.click(screen.getByRole('button', { name: /submit complaint/i }))

    expect(
      await screen.findByText(/complaint text must be between 10 and 2000 characters/i),
    ).toBeInTheDocument()
  })

  it('shows an honest loading state while the request is in flight', async () => {
    let resolveFetch!: (value: Response) => void
    const pending = new Promise<Response>((resolve) => {
      resolveFetch = resolve
    })
    vi.stubGlobal(
      'fetch',
      vi.fn(() => pending),
    )

    const user = userEvent.setup()
    render(<SubmitPage />)

    await user.type(screen.getByLabelText(/complaint text/i), 'There is a large pothole here.')
    await user.type(screen.getByLabelText(/location/i), '12 Main Street')
    await user.click(screen.getByRole('button', { name: /submit complaint/i }))

    expect(screen.getByText(/triaging your complaint/i)).toBeInTheDocument()

    resolveFetch(
      jsonResponse(
        {
          id: '11111111-1111-1111-1111-111111111111',
          text: 'There is a large pothole here.',
          location: '12 Main Street',
          reporter_contact: null,
          category: 'roads',
          priority: 'high',
          status: 'open',
          ai_summary: 'Pothole reported on Main Street.',
          triaged_by: 'llm:groq',
          triage_latency_ms: 120,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        { status: 201 },
      ),
    )

    await waitFor(() =>
      expect(screen.queryByText(/triaging your complaint/i)).not.toBeInTheDocument(),
    )
  })

  it('renders the triage result (category, priority, summary, provider) on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            id: '11111111-1111-1111-1111-111111111111',
            text: 'There is a large pothole here.',
            location: '12 Main Street',
            reporter_contact: null,
            category: 'roads',
            priority: 'high',
            status: 'open',
            ai_summary: 'Pothole reported on Main Street.',
            triaged_by: 'llm:groq',
            triage_latency_ms: 120,
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
          { status: 201 },
        ),
      ),
    )

    const user = userEvent.setup()
    render(<SubmitPage />)

    await user.type(screen.getByLabelText(/complaint text/i), 'There is a large pothole here.')
    await user.type(screen.getByLabelText(/location/i), '12 Main Street')
    await user.click(screen.getByRole('button', { name: /submit complaint/i }))

    expect(await screen.findByText(/complaint submitted/i)).toBeInTheDocument()
    expect(screen.getByText('roads')).toBeInTheDocument()
    expect(screen.getByText('high')).toBeInTheDocument()
    expect(screen.getByText('llm:groq')).toBeInTheDocument()
    expect(screen.getByText('Pothole reported on Main Street.')).toBeInTheDocument()
  })
})
