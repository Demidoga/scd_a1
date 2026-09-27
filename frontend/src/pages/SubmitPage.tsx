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
      <h1 className="text-2xl font-semibold text-slate-900">Report an issue</h1>
      <p className="mt-1 text-sm text-slate-500">
        Describe the problem and where it is happening. It will be automatically triaged.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-6 space-y-5">
        <div>
          <label htmlFor="text" className="block text-sm font-medium text-slate-700">
            Complaint text
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none"
            placeholder="e.g. There is a large pothole outside 12 Main Street causing traffic to swerve."
          />
          <p className="mt-1 text-xs text-slate-400">{text.length}/{TEXT_MAX} characters</p>
          {(clientErrors.text || fieldMessage('text')) && (
            <p className="mt-1 text-sm text-red-600">{clientErrors.text ?? fieldMessage('text')}</p>
          )}
        </div>

        <div>
          <label htmlFor="location" className="block text-sm font-medium text-slate-700">
            Location
          </label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none"
            placeholder="e.g. 12 Main Street"
          />
          {(clientErrors.location || fieldMessage('location')) && (
            <p className="mt-1 text-sm text-red-600">
              {clientErrors.location ?? fieldMessage('location')}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="contact" className="block text-sm font-medium text-slate-700">
            Contact (optional)
          </label>
          <input
            id="contact"
            type="text"
            value={reporterContact}
            onChange={(e) => setReporterContact(e.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none"
            placeholder="Email or phone number"
          />
        </div>

        {submitError && <ErrorMessage message={submitError} />}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 hover:bg-slate-700"
        >
          {submitting ? 'Submitting…' : 'Submit complaint'}
        </button>
        {submitting && <LoadingSpinner label="Triaging your complaint…" />}
      </form>

      {result && (
        <div className="mt-8 rounded-lg border border-green-200 bg-green-50 p-4">
          <h2 className="text-sm font-semibold text-green-900">Complaint submitted</h2>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-green-700">Category</dt>
              <dd className="font-medium capitalize text-green-900">{result.category}</dd>
            </div>
            <div>
              <dt className="text-green-700">Priority</dt>
              <dd>
                <PriorityBadge priority={result.priority} />
              </dd>
            </div>
            <div>
              <dt className="text-green-700">Status</dt>
              <dd>
                <StatusBadge status={result.status} />
              </dd>
            </div>
            <div>
              <dt className="text-green-700">Triaged by</dt>
              <dd className="font-medium text-green-900">{result.triaged_by}</dd>
            </div>
            {result.ai_summary && (
              <div className="col-span-2">
                <dt className="text-green-700">AI summary</dt>
                <dd className="text-green-900">{result.ai_summary}</dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </div>
  )
}
