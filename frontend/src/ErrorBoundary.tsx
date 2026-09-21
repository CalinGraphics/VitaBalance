import { Component, ErrorInfo, ReactNode } from 'react'
import i18n from './shared/i18n'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      // Clasa nu poate folosi hook-uri; citim traducerile direct din instanța i18n.
      const t = i18n.t.bind(i18n)
      return (
        <div className="app-bg flex min-h-screen items-center justify-center p-4 text-zinc-100">
          <div className="w-full max-w-md text-center">
            <h1 className="mb-3 text-2xl font-semibold text-red-400">{t('app.boundary.title')}</h1>
            <p className="mb-4 text-zinc-300">{t('app.boundary.message')}</p>
            {this.state.error && (
              <details className="mb-4 rounded-lg border border-line bg-surface p-4 text-left">
                <summary className="mb-2 cursor-pointer text-zinc-400">{t('app.boundary.details')}</summary>
                <pre className="overflow-auto text-xs text-red-400">{this.state.error.toString()}</pre>
              </details>
            )}
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="min-h-[44px] cursor-pointer rounded-lg bg-accent px-5 text-sm font-semibold text-accent-fg transition-colors hover:bg-accent-hover"
            >
              {t('app.boundary.reload')}
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
