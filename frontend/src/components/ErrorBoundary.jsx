import React from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    if (this.props.onReset) {
      this.props.onReset()
    } else {
      window.location.reload()
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md w-full p-6 rounded-2xl bg-slate-900/90 border border-rose-900/60 shadow-2xl backdrop-blur-xl text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-xl bg-rose-950/60 border border-rose-800 text-rose-400 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h3 className="text-lg font-bold text-white">System Component Interrupted</h3>
              <p className="text-xs text-slate-400">
                An unexpected interface anomaly was caught by the FraudLens safety boundary.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-left font-mono text-[11px] text-rose-300">
              {this.state.error?.message || 'Component runtime exception'}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={this.handleReset}
                className="flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-950 transition"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry Component
              </button>
              <button
                onClick={() => (window.location.href = '/')}
                className="flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
              >
                <Home className="w-3.5 h-3.5" />
                Dashboard
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
