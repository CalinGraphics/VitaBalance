import { Component, ErrorInfo, ReactNode } from 'react'

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
      return (
        <div className="min-h-screen app-gradient-dark text-slate-100 flex items-center justify-center p-4">
          <div className="max-w-md w-full text-center">
            <h1 className="text-2xl font-bold text-red-400 mb-4">Eroare</h1>
            <p className="text-slate-300 mb-4">
              A apărut o eroare în aplicație. Te rugăm să reîncarci pagina.
            </p>
            {this.state.error && (
              <details className="text-left bg-slate-900/40 p-4 rounded-lg mb-4">
                <summary className="cursor-pointer text-slate-400 mb-2">Detalii eroare</summary>
                <pre className="text-xs text-red-400 overflow-auto">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-neonCyan text-black rounded-lg hover:bg-neonMagenta transition"
            >
              Reîncarcă pagina
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

