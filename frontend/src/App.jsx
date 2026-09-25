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
  BookOpen,
  Zap,
  CreditCard,
  Bot,
  Volume2,
} from 'lucide-react'

import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import ErrorBoundary from './components/ErrorBoundary'
import DashboardView from './components/DashboardView'
import PaymentView from './components/PaymentView'
import TransactionRiskAnalyzerView from './components/TransactionRiskAnalyzerView'
import LiveTransactionMonitorView from './components/LiveTransactionMonitorView'
import MerchantIntelligenceView from './components/MerchantIntelligenceView'
import TransactionsView from './components/TransactionsView'
import CustomersView from './components/CustomersView'
import ExplainableAiView from './components/ExplainableAiView'
import InvestigationsView from './components/InvestigationsView'
import ModelLabView from './components/ModelLabView'
import DatasetHealthView from './components/DatasetHealthView'
import ReportsView from './components/ReportsView'
import AuditLogsView from './components/AuditLogsView'
import SettingsView from './components/SettingsView'
import LoginScene from './components/login/LoginScene'
import SecurityUnlockTransition from './components/SecurityUnlockTransition'
import UserManualModal from './components/UserManualModal'
import AiVoiceHelpModal from './components/AiVoiceHelpModal'
import AiAssistantPanel from './components/AiAssistantPanel'
import { systemApi } from './services/api'
import { getCustomerPersona } from './utils/customerHelper'

function CommandCenterApp() {
  const { user, isAuthenticated, isAdmin, login, register, logout, loading: authLoading, error: authError } = useAuth()
  const isCustomer = user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user'
  const customerPersona = getCustomerPersona(user)

  // Navigation State
  const [activeView, setActiveView] = useState('dashboard')
  const [selectedPersona, setSelectedPersona] = useState('scenario_monisha_safe')
  const [navHistory, setNavHistory] = useState([]) // history stack for back navigation
  const [mobileOpen, setMobileOpen] = useState(false)
  const [showManual, setShowManual] = useState(false)
  const [showVoiceHelp, setShowVoiceHelp] = useState(false)

  // Navigate to a new view — push current view into history
  const navigateTo = useCallback((view) => {
    setActiveView((prev) => {
      if (prev !== view) {
        setNavHistory((h) => [...h, prev])
      }
      return view
    })
    setMobileOpen(false)
  }, [])

  const handleSelectPersona = useCallback((personaId) => {
    setSelectedPersona(personaId)
    setActiveView('payment')
    setMobileOpen(false)
  }, [])

  // Go back to the previous view
  const navigateBack = useCallback(() => {
    setNavHistory((prev) => {
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

  // Cross-view context passing
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

  const handleOpenInvestigation = (txId) => {
    setTargetTxId(txId)
    navigateTo('investigations')
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
        register={register}
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
      {/* Cinematic Security Access Unlock Transition */}
      {isTransitioning && (
        <SecurityUnlockTransition
          onComplete={() => setIsTransitioning(false)}
        />
      )}

      <div
        className={`flex flex-1 overflow-hidden transition-all duration-700 ease-out ${
          isTransitioning ? 'opacity-75 scale-[0.99] filter blur-[0.5px]' : 'opacity-100 scale-100 filter-none'
        }`}
      >
        {/* Responsive Sidebar Navigation */}
        <ErrorBoundary onReset={() => setActiveView('dashboard')}>
          <Sidebar
            activeView={activeView}
            setActiveView={navigateTo}
            isAdmin={isAdmin}
            user={user}
            logout={logout}
            mobileOpen={mobileOpen}
            setMobileOpen={setMobileOpen}
            onOpenManual={() => setShowManual(true)}
            onOpenVoiceHelp={() => setShowVoiceHelp(true)}
            onSelectPersona={handleSelectPersona}
          />
        </ErrorBoundary>

        {/* Main Content Layout */}
        <div
          className={`flex-1 flex flex-col min-w-0 overflow-y-auto transition-transform duration-500 ${
            isTransitioning ? 'translate-y-0.5' : 'translate-y-0'
          }`}
        >
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

              {/* Back Button */}
              {navHistory.length > 0 && (
                <button
                  onClick={navigateBack}
                  title="Go back (Alt+←)"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-700 text-slate-300 hover:text-cyan-300 text-xs font-semibold transition-all group"
                >
                  <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                  <span className="hidden sm:inline">
                    {navHistory[navHistory.length - 1].replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </span>
                  <span className="sm:hidden">Back</span>
                </button>
              )}

              <div className="font-mono text-xs text-slate-400">
                Active Module:{' '}
                <strong className="text-cyan-400 uppercase tracking-wide">
                  {activeView.replace(/-/g, ' ')}
                </strong>
              </div>

              {/* Real-Time Personas Header Switcher Bar (Admin sees all 3; Customer watches only their own) */}
              {isCustomer ? (
                <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-xl bg-slate-950/80 border border-emerald-800/80 shadow-inner">
                  <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    Verified Customer:
                  </span>
                  <span className="text-[11px] font-mono font-bold text-white">
                    {customerPersona.name} ({customerPersona.customerId})
                  </span>
                  <span className="text-[10px] font-mono font-bold bg-emerald-950 px-1.5 py-0.5 rounded text-emerald-300 border border-emerald-800">
                    {customerPersona.fraudRate} Baseline
                  </span>
                </div>
              ) : (
                <div className="hidden xl:flex items-center gap-1.5 px-2 py-1 rounded-xl bg-slate-950/80 border border-slate-800/80 shadow-inner">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold flex items-center gap-1 mr-1">
                    <Zap className="w-3 h-3 text-cyan-400 animate-pulse" />
                    Personas:
                  </span>
                  <button
                    onClick={() => handleSelectPersona('scenario_monisha_safe')}
                    className={`px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold transition flex items-center gap-1 border ${
                      activeView === 'payment' && selectedPersona === 'scenario_monisha_safe'
                        ? 'bg-emerald-900 border-emerald-500 text-white shadow-sm'
                        : 'bg-emerald-950/70 hover:bg-emerald-900/80 border-emerald-800/60 text-emerald-300'
                    }`}
                    title="Monisha (3% Fraud Rate) - Clean Habitual Baseline -> ALLOW"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    Monisha (3%)
                  </button>
                  <button
                    onClick={() => handleSelectPersona('scenario_mohana_review')}
                    className={`px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold transition flex items-center gap-1 border ${
                      activeView === 'payment' && selectedPersona === 'scenario_mohana_review'
                        ? 'bg-amber-900 border-amber-500 text-white shadow-sm'
                        : 'bg-amber-950/70 hover:bg-amber-900/80 border-amber-800/60 text-amber-300'
                    }`}
                    title="Mohana (12% Fraud Rate) - Unfamiliar Device/Region -> REVIEW (OTP)"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    Mohana (12%)
                  </button>
                  <button
                    onClick={() => handleSelectPersona('scenario_sowmiya_block')}
                    className={`px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold transition flex items-center gap-1 border ${
                      activeView === 'payment' && selectedPersona === 'scenario_sowmiya_block'
                        ? 'bg-rose-900 border-rose-500 text-white shadow-sm'
                        : 'bg-rose-950/70 hover:bg-rose-900/80 border-rose-800/60 text-rose-300'
                    }`}
                    title="Sowmiya (26% Fraud Rate) - Botnet ATO Attack -> BLOCK"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                    Sowmiya (26%)
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2.5">
              {/* Direct Payment Gateway Shortcut */}
              <button
                onClick={() => navigateTo('payment')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition border ${
                  activeView === 'payment'
                    ? 'bg-cyan-600 text-white border-cyan-400 shadow-md shadow-cyan-900/50'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border-slate-700'
                }`}
                title="Open Pre-Auth Payment Gateway"
              >
                <CreditCard className="w-3.5 h-3.5 text-cyan-400" />
                <span className="hidden sm:inline">Payment Gateway</span>
              </button>

              {/* AI Voice Help: What is Fraud? Shortcut */}
              <button
                onClick={() => setShowVoiceHelp(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-purple-950/40 transition border border-purple-400/50 group"
                title="Launch AI Voice Help & What is Fraud? (Siri & Google Voice)"
              >
                <Bot className="w-3.5 h-3.5 group-hover:scale-110 transition-transform animate-pulse" />
                <span className="hidden lg:inline">AI Voice Help</span>
                <span className="lg:hidden">Voice AI</span>
                <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-purple-950/90 text-purple-200 border border-purple-700/80">
                  Siri
                </span>
              </button>

              {/* User Manual & Guide Button */}
              <button
                onClick={() => setShowManual(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-950/40 transition"
                title="Open Easy User Manual"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span className="hidden md:inline">User Manual</span>
                <span className="md:hidden">Guide</span>
              </button>

              {/* Backend Connectivity Status */}
              <div className="hidden sm:flex items-center space-x-2 bg-slate-900/80 px-3 py-1.5 rounded-full border border-slate-800 text-xs">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
                  }`}
                />
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
                    isAdmin
                      ? 'bg-purple-950 text-purple-300 border border-purple-800'
                      : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
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
                  user={user}
                  isAdmin={isAdmin}
                  onSelectTransaction={handleSelectTransaction}
                  onOpenCase={() => navigateTo('investigations')}
                  onOpenPayment={handleSelectPersona}
                />
              )}

              {activeView === 'payment' && (
                <PaymentView
                  user={user}
                  isAdmin={isAdmin}
                  initialPreset={selectedPersona}
                  onViewExplanation={handleViewExplanation}
                  onNavigateToInvestigations={() => navigateTo('investigations')}
                  onSelectTransaction={handleSelectTransaction}
                />
              )}

              {activeView === 'analyzer' && (
                <TransactionRiskAnalyzerView user={user} isAdmin={isAdmin} />
              )}

              {activeView === 'live-monitor' && (
                <LiveTransactionMonitorView user={user} isAdmin={isAdmin} onInvestigate={handleOpenInvestigation} />
              )}

              {activeView === 'merchants' && (
                <MerchantIntelligenceView user={user} isAdmin={isAdmin} />
              )}

              {activeView === 'transactions' && (
                <TransactionsView
                  user={user}
                  isAdmin={isAdmin}
                  onViewExplanation={handleViewExplanation}
                />
              )}

              {activeView === 'customers' && (
                <CustomersView
                  user={user}
                  isAdmin={isAdmin}
                  onSelectTransaction={handleSelectTransaction}
                />
              )}

              {activeView === 'explainable-ai' && (
                <ExplainableAiView
                  user={user}
                  isAdmin={isAdmin}
                  initialTransactionId={targetTxId}
                />
              )}

              {activeView === 'investigations' && (
                <InvestigationsView
                  user={user}
                  isAdmin={isAdmin}
                  onInspectExplanation={handleViewExplanation}
                />
              )}

              {(activeView === 'model-lab' || activeView === 'admin-models') && (
                <ModelLabView user={user} isAdmin={isAdmin} />
              )}

              {(activeView === 'dataset-health' || activeView === 'admin-dataset') && (
                <DatasetHealthView user={user} isAdmin={isAdmin} />
              )}

              {activeView === 'reports' && (
                <ReportsView user={user} isAdmin={isAdmin} />
              )}

              {activeView === 'audit-logs' && (
                <AuditLogsView />
              )}

              {activeView === 'settings' && (
                <SettingsView />
              )}
            </ErrorBoundary>
          </main>

          {/* Footer */}
          <footer className="border-t border-slate-800/80 py-3 px-6 bg-slate-950/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
            <div>FraudLens AI — Financial Fraud Detection &amp; Explainability Platform</div>
            <div className="font-mono text-[11px]">29 Merchant Master Architecture • Real-Time AI</div>
          </footer>
        </div>
      </div>

      {/* Floating AI Assistant Panel — Gemini + Grok Chat */}
      <AiAssistantPanel
        user={user}
        isAdmin={isAdmin}
        currentView={activeView}
        currentTransactionId={''}
      />

      {/* Interactive Easy User Manual & Guide Modal */}
      <UserManualModal
        isOpen={showManual}
        onClose={() => setShowManual(false)}
        onOpenVoiceHelp={() => setShowVoiceHelp(true)}
        user={user}
        isAdmin={isAdmin}
      />

      {/* Interactive AI Voice Help & What is Fraud Explainer Modal */}
      <AiVoiceHelpModal
        isOpen={showVoiceHelp}
        onClose={() => setShowVoiceHelp(false)}
      />
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
