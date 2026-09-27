import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error', error, info)
  }

  private reset = () => this.setState({ error: null })

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-lg py-16 text-center">
          <h2 className="text-lg font-semibold text-slate-900">Something went wrong</h2>
          <p className="mt-2 text-sm text-slate-600">
            An unexpected error occurred while rendering this page.
          </p>
          <button
            type="button"
            onClick={this.reset}
            className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
