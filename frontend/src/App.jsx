import React, { useState, useEffect, useCallback } from 'react'
import {
  ShieldCheck,
  RefreshCw,
  Lock,
  KeyRound,
  Menu,
  XCircle,
  ArrowLeft,
  LogOut,
} from 'lucide-react'

import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import ErrorBoundary from './components/ErrorBoundary'
import DashboardView from './components/DashboardView'
import PaymentView from './components/PaymentView'
import TransactionsView from './components/TransactionsView'
import CustomersView from './components/CustomersView'
import PredictionsView from './components/PredictionsView'
import ExplainableAiView from './components/ExplainableAiView'
import InvestigationsView from './components/InvestigationsView'
import ReportsView from './components/ReportsView'
import AuditLogsView from './components/AuditLogsView'
import AdminMlView from './components/AdminMlView'
import SettingsView from './components/SettingsView'
import LoginScene from './components/login/LoginScene'
import SecurityUnlockTransition from './components/SecurityUnlockTransition'
import { systemApi } from './services/api'

function CommandCenterApp() {
  const { user, isAuthenticated, isAdmin, login, logout, loading: authLoading, error: authError } = useAuth()

  // Navigation State
  const [activeView, setActiveView] = useState('dashboard')
  const [navHistory, setNavHistory] = useState([])  // history stack for back navigation
  const [mobileOpen, setMobileOpen] = useState(false)

  // Navigate to a new view — push current view into history
  const navigateTo = useCallback((view) => {
    setActiveView(prev => {
      if (prev !== view) {
        setNavHistory(h => [...h, prev])
      }
      return view
    })
    setMobileOpen(false)
  }, [])

  // Go back to the previous view
  const navigateBack = useCallback(() => {
    setNavHistory(prev => {
      if (prev.length === 0) return prev
      const history = [...prev]
      const previous = history.pop()
      setActiveView(previous)
      return history
    })
  }, [])

  // Keyboard shortcut: Alt+← goes back
  useEffect(() => {
    const onKey = (e) => {
      if (e.altKey && e.key === 'ArrowLeft' && navHistory.length > 0) {
        e.preventDefault()
        navigateBack()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [navHistory, navigateBack])

  // Cross-view context passing (e.g. inspecting specific transaction in XAI view)
  const [targetTxId, setTargetTxId] = useState(null)

  // Health API telemetry
  const [healthData, setHealthData] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [healthError, setHealthError] = useState(null)
  const [latency, setLatency] = useState(null)

  const checkHealth = useCallback(async () => {
    setHealthLoading(true)
    setHealthError(null)
    const startTime = performance.now()
    try {
      const data = await systemApi.getHealth()
      const endTime = performance.now()
      setLatency(Math.round(endTime - startTime))
      setHealthData(data)
    } catch (err) {
      setHealthError(err instanceof Error ? err.message : 'Failed to connect')
      setHealthData(null)
    } finally {
      setHealthLoading(false)
    }
  }, [])

  useEffect(() => {
    checkHealth()
    const timer = setInterval(checkHealth, 25000)
    return () => clearInterval(timer)
  }, [checkHealth])

  // Cross-view navigation handlers
  const handleViewExplanation = (txId) => {
    setTargetTxId(txId)
    navigateTo('explainable-ai')
  }

  const handleSelectTransaction = (txId) => {
    setTargetTxId(txId)
    navigateTo('transactions')
  }

  const isConnected = !healthLoading && !healthError && healthData?.status === 'healthy'
  const [isTransitioning, setIsTransitioning] = useState(false)

  // If user is not authenticated and not in unlock transition, display login scene
  if (!isAuthenticated && !isTransitioning) {
    return (
      <LoginScene
        onLoginSuccess={() => {
          setIsTransitioning(true)
          setActiveView('dashboard')
        }}
        login={login}
        authLoading={authLoading}
        authError={authError}
        isConnected={isConnected}
        latency={latency}
      />
    )
  }

  // AUTHENTICATED COMMAND CENTER APPLICATION SHELL
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200 relative overflow-hidden">
      {/* 5-Phase Cinematic Security Access & AI Core Unlock Transition Overlay */}
      {isTransitioning && (
        <SecurityUnlockTransition
          onComplete={() => setIsTransitioning(false)}
        />
      )}

      <div className={`flex flex-1 overflow-hidden transition-all duration-700 ease-out ${
        isTransitioning ? 'opacity-75 scale-[0.99] filter blur-[0.5px]' : 'opacity-100 scale-100 filter-none'
      }`}>
        {/* Responsive Sidebar Navigation */}
        <Sidebar
          activeView={activeView}
          setActiveView={navigateTo}
          isAdmin={isAdmin}
          user={user}
          logout={logout}
          mobileOpen={mobileOpen}
          setMobileOpen={setMobileOpen}
        />

        {/* Main Content Layout */}
        <div className={`flex-1 flex flex-col min-w-0 overflow-y-auto transition-transform duration-500 ${
          isTransitioning ? 'translate-y-0.5' : 'translate-y-0'
        }`}>
          {/* Top Operational Header */}
          <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30 px-4 sm:px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMobileOpen(true)}
                className="lg:hidden p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white"
                aria-label="Open sidebar navigation"
              >
                <Menu className="w-5 h-5" />
              </button>

              {/* Back Button — appears when history exists */}
              {navHistory.length > 0 && (
                <button
                  onClick={navigateBack}
                  title="Go back (Alt+←)"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-700 text-slate-300 hover:text-cyan-300 text-xs font-semibold transition-all group"
                >
                  <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                  <span className="hidden sm:inline">
                    {navHistory[navHistory.length - 1].replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                  <span className="sm:hidden">Back</span>
                </button>
              )}

              <div className="font-mono text-xs text-slate-400">
                Active View: <strong className="text-cyan-400 uppercase">{activeView.replace(/-/g, ' ')}</strong>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {/* Backend Connectivity Status */}
              <div className="hidden sm:flex items-center space-x-2 bg-slate-900/80 px-3 py-1.5 rounded-full border border-slate-800 text-xs">
                <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
                <span className="font-medium text-slate-300">
                  {isConnected ? `Backend Connected (${latency}ms)` : 'Offline'}
                </span>
              </div>

              {/* User Profile Badge */}
              <div className="flex items-center space-x-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-full text-xs">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                <span className="font-semibold text-slate-200 hidden md:inline">{user?.email}</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold font-mono ${
                    isAdmin ? 'bg-purple-950 text-purple-300 border border-purple-800' : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                  }`}
                >
                  {user?.role}
                </span>
              </div>

              <button
                onClick={checkHealth}
                disabled={healthLoading}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
                title="Refresh Status"
              >
                <RefreshCw className={`w-4 h-4 ${healthLoading ? 'animate-spin' : ''}`} />
              </button>

              <button
                onClick={logout}
                className="p-2 rounded-xl bg-slate-800 hover:bg-rose-950/50 text-slate-300 hover:text-rose-400 border border-slate-700 hover:border-rose-700/60 transition"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </header>

          {/* Dynamic Page Views */}
          <main className="p-4 sm:p-6 lg:p-8 flex-1">
            <ErrorBoundary onReset={() => setActiveView('dashboard')}>
              {activeView === 'dashboard' && (
                <DashboardView
                  onSelectTransaction={handleSelectTransaction}
                  onOpenCase={() => navigateTo('investigations')}
                />
              )}

              {activeView === 'payment' && (
                <PaymentView
                  onViewExplanation={handleViewExplanation}
                />
              )}

              {activeView === 'transactions' && (
                <TransactionsView
                  onViewExplanation={handleViewExplanation}
                />
              )}

              {activeView === 'customers' && (
                <CustomersView
                  onSelectTransaction={handleSelectTransaction}
                />
              )}

              {activeView === 'predictions' && (
                <PredictionsView
                  onOpenExplanation={handleViewExplanation}
                />
              )}

              {activeView === 'explainable-ai' && (
                <ExplainableAiView
                  initialTransactionId={targetTxId}
                />
              )}

              {activeView === 'investigations' && (
                <InvestigationsView
                  onInspectExplanation={handleViewExplanation}
                />
              )}

              {activeView === 'reports' && (
                <ReportsView />
              )}

              {activeView === 'audit-logs' && (
                <AuditLogsView />
              )}

              {activeView === 'settings' && (
                <SettingsView />
              )}

              {/* Admin-Only Views */}
              {activeView === 'admin-dataset' && isAdmin && (
                <AdminMlView initialTab="dataset" />
              )}

              {activeView === 'admin-models' && isAdmin && (
                <AdminMlView initialTab="models" />
              )}
            </ErrorBoundary>
          </main>

          {/* Footer */}
          <footer className="border-t border-slate-800/80 py-3 px-6 bg-slate-950/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
            <div>Explainable AI-Based Financial Fraud and Risk Detection System</div>
            <div className="font-mono text-[11px]">Phases 1–16 Production Architecture</div>
          </footer>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <CommandCenterApp />
    </AuthProvider>
  )
}
