import { useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import type { ComplaintResponse, FieldError } from '../api/types'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { StatusBadge } from '../components/StatusBadge'
import { PriorityBadge } from '../components/PriorityBadge'

const TEXT_MIN = 10
const TEXT_MAX = 2000
const LOCATION_MIN = 3
const LOCATION_MAX = 200

interface ClientErrors {
  text?: string
  location?: string
}

function validate(text: string, location: string): ClientErrors {
  const errors: ClientErrors = {}
  if (text.trim().length < TEXT_MIN || text.length > TEXT_MAX) {
    errors.text = `Complaint text must be between ${TEXT_MIN} and ${TEXT_MAX} characters.`
  }
  if (location.trim().length < LOCATION_MIN || location.length > LOCATION_MAX) {
    errors.location = `Location must be between ${LOCATION_MIN} and ${LOCATION_MAX} characters.`
  }
  return errors
}

const inputClass =
  'mt-1.5 block w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 transition-colors placeholder:text-zinc-500 hover:border-zinc-600 focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/15'

export function SubmitPage() {
  const [text, setText] = useState('')
  const [location, setLocation] = useState('')
  const [reporterContact, setReporterContact] = useState('')
  const [clientErrors, setClientErrors] = useState<ClientErrors>({})
  const [serverErrors, setServerErrors] = useState<FieldError[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [result, setResult] = useState<ComplaintResponse | null>(null)

  const fieldMessage = (field: string) => serverErrors.find((e) => e.field === field)?.message

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const errors = validate(text, location)
    setClientErrors(errors)
    setServerErrors([])
    setSubmitError(null)
    if (Object.keys(errors).length > 0) return

    setSubmitting(true)
    setResult(null)
    try {
      const complaint = await api.createComplaint({
        text,
        location,
        reporter_contact: reporterContact.trim() ? reporterContact.trim() : null,
      })
      setResult(complaint)
      setText('')
      setLocation('')
      setReporterContact('')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 400 && err.body?.errors) {
          setServerErrors(err.body.errors)
        } else {
          setSubmitError(err.body?.detail ?? err.message)
        }
      } else {
        setSubmitError('Unexpected error submitting complaint.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">Report an issue</h1>
      <p className="mt-1.5 text-sm text-zinc-400">
        Describe the problem and where it is happening. It will be automatically triaged.
      </p>

      <form
        onSubmit={handleSubmit}
        noValidate
        className="mt-7 space-y-5 rounded-xl border border-zinc-800 bg-zinc-900 p-6 sm:p-7"
      >
        <div>
          <label htmlFor="text" className="block text-sm font-medium text-zinc-300">
            Complaint text
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            className={`${inputClass} resize-none`}
            placeholder="e.g. There is a large pothole outside 12 Main Street causing traffic to swerve."
          />
          <div className="mt-1.5 flex items-start justify-between gap-4">
            {(clientErrors.text || fieldMessage('text')) && (
              <p className="text-sm text-rose-400">{clientErrors.text ?? fieldMessage('text')}</p>
            )}
            <p className="ml-auto shrink-0 text-xs tabular-nums text-zinc-500">
              {text.length}/{TEXT_MAX}
            </p>
          </div>
        </div>

        <div>
          <label htmlFor="location" className="block text-sm font-medium text-zinc-300">
            Location
          </label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className={inputClass}
            placeholder="e.g. 12 Main Street"
          />
          {(clientErrors.location || fieldMessage('location')) && (
            <p className="mt-1.5 text-sm text-rose-400">
              {clientErrors.location ?? fieldMessage('location')}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="contact" className="block text-sm font-medium text-zinc-300">
            Contact <span className="font-normal text-zinc-500">(optional)</span>
          </label>
          <input
            id="contact"
            type="text"
            value={reporterContact}
            onChange={(e) => setReporterContact(e.target.value)}
            className={inputClass}
            placeholder="Email or phone number"
          />
        </div>

        {submitError && <ErrorMessage message={submitError} />}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-blue-500 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? 'Submitting…' : 'Submit complaint'}
        </button>
        {submitting && <LoadingSpinner label="Triaging your complaint…" />}
      </form>

      {result && (
        <div className="mt-6 rounded-xl border border-emerald-500/20 bg-emerald-500/6 p-5">
          <div className="flex items-center gap-2">
            <svg
              aria-hidden="true"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="h-4.5 w-4.5 text-emerald-400"
            >
              <path
                fillRule="evenodd"
                d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z"
                clipRule="evenodd"
              />
            </svg>
            <h2 className="text-sm font-semibold text-emerald-100">Complaint submitted</h2>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3.5 text-sm">
            <div>
              <dt className="text-xs font-medium text-emerald-400/80">Category</dt>
              <dd className="mt-0.5 font-medium capitalize text-emerald-50">{result.category}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-emerald-400/80">Priority</dt>
              <dd className="mt-1">
                <PriorityBadge priority={result.priority} />
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-emerald-400/80">Status</dt>
              <dd className="mt-1">
                <StatusBadge status={result.status} />
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-emerald-400/80">Triaged by</dt>
              <dd className="mt-0.5 font-medium text-emerald-50">{result.triaged_by}</dd>
            </div>
            {result.ai_summary && (
              <div className="col-span-2 border-t border-emerald-500/20 pt-3.5">
                <dt className="text-xs font-medium text-emerald-400/80">AI summary</dt>
                <dd className="mt-0.5 text-emerald-50">{result.ai_summary}</dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </div>
  )
}
