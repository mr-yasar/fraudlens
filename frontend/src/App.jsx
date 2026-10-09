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
  Lightbulb,
  BrainCircuit,
  Radio,
  CheckCircle2,
  Sparkles,
  Sun,
  Moon,
} from 'lucide-react'

import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import ErrorBoundary from './components/ErrorBoundary'
import DashboardView from './components/DashboardView'
import PaymentView from './components/PaymentView'
import TransactionRiskAnalyzerView from './components/TransactionRiskAnalyzerView'
import LiveMonitorAndInvestigationHub from './components/LiveMonitorAndInvestigationHub'
import LiveTransactionMonitorView from './components/LiveTransactionMonitorView'
import MerchantIntelligenceView from './components/MerchantIntelligenceView'
import TransactionsView from './components/TransactionsView'
import ExplainableAiView from './components/ExplainableAiView'
import InvestigationsView from './components/InvestigationsView'
import ModelLabView from './components/ModelLabView'
import DatasetHealthView from './components/DatasetHealthView'
import AuditLogsView from './components/AuditLogsView'
import SettingsView from './components/SettingsView'
import LoginScene from './components/login/LoginScene'
import SecurityUnlockTransition from './components/SecurityUnlockTransition'
import HowItWorksModal from './components/HowItWorksModal'
import AiAssistantPanel from './components/AiAssistantPanel'
import AiInvestigationCommandCenter from './components/ai/AiInvestigationCommandCenter'
import PremiumSecurityDashboard from './components/premium/PremiumSecurityDashboard'
import PremiumTransactionCenter from './components/premium/PremiumTransactionCenter'
import PremiumSecurityCenter from './components/premium/PremiumSecurityCenter'
import PremiumDeviceSecurity from './components/premium/PremiumDeviceSecurity'
import PremiumAlertCenter from './components/premium/PremiumAlertCenter'
import PremiumAuditTrail from './components/premium/PremiumAuditTrail'
import FleetSecurityView from './components/FleetSecurityView'
import PersonalizedWelcomeOverlay from './components/common/PersonalizedWelcomeOverlay'
import LogoutConfirmModal from './components/common/LogoutConfirmModal'
import SecurityLogoutDoor from './components/common/SecurityLogoutDoor'
import ModuleInfoExplainer from './components/common/ModuleInfoExplainer'
import { systemApi } from './services/api'
import { getCustomerPersona } from './utils/customerHelper'

function CommandCenterApp() {
  const { user, isAuthenticated, isAdmin, login, register, logout, loading: authLoading, error: authError } = useAuth()
  const isCustomer = user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user'
  const customerPersona = getCustomerPersona(user) || {}
  const isPremium = user?.account_tier === 'PREMIUM' || customerPersona?.isPremium

  // Navigation State
  const [activeView, setActiveView] = useState('dashboard')
  const [selectedPersona, setSelectedPersona] = useState(null)
  const [navHistory, setNavHistory] = useState([]) // history stack for back navigation
  const [mobileOpen, setMobileOpen] = useState(false)
  const [showHowItWorks, setShowHowItWorks] = useState(false)

  // Clear selected persona override whenever authenticated user changes
  useEffect(() => {
    setSelectedPersona(null)
  }, [user?.id, user?.email])

  // Global Theme State: 'dark' | 'light'
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('fraudlens_theme')
    return saved === 'light' ? 'light' : 'dark'
  })

  useEffect(() => {
    localStorage.setItem('fraudlens_theme', theme)
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme')
      document.documentElement.classList.remove('dark')
      document.documentElement.setAttribute('data-theme', 'light')
    } else {
      document.documentElement.classList.remove('light-theme')
      document.documentElement.classList.add('dark')
      document.documentElement.setAttribute('data-theme', 'dark')
    }
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }, [])

  // Floating AI Assistant & Expand/Minimize Synchronization
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false)
  const [previousViewBeforeCopilot, setPreviousViewBeforeCopilot] = useState('dashboard')

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

  const handleExpandToCommandCenter = useCallback(() => {
    setPreviousViewBeforeCopilot((prev) => (activeView !== 'ai-copilot' ? activeView : 'dashboard'))
    setAiAssistantOpen(false)
    navigateTo('ai-copilot')
  }, [activeView, navigateTo])

  const handleMinimizeCommandCenter = useCallback(() => {
    const returnView =
      previousViewBeforeCopilot && previousViewBeforeCopilot !== 'ai-copilot'
        ? previousViewBeforeCopilot
        : (navHistory.length > 0 && navHistory[navHistory.length - 1] !== 'ai-copilot'
            ? navHistory[navHistory.length - 1]
            : 'dashboard')
    navigateTo(returnView)
    setAiAssistantOpen(true)
  }, [previousViewBeforeCopilot, navHistory, navigateTo])

  // Guard payment gateway & analyzer: Admin never accesses Payment Gateway or Customer Analyzer
  useEffect(() => {
    if (isAdmin && (activeView === 'payment' || activeView === 'analyzer')) {
      setActiveView('dashboard')
    }
  }, [isAdmin, activeView])

  const handleSelectPersona = useCallback((personaId) => {
    if (isAdmin) return
    setSelectedPersona(personaId)
    setActiveView('payment')
    setMobileOpen(false)
  }, [isAdmin])

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

  // Refresh & Feedback State
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshToast, setRefreshToast] = useState(false)
  const [showWelcome, setShowWelcome] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [explainerOpen, setExplainerOpen] = useState(false)

  const isConnected = !healthLoading && !healthError && healthData?.status === 'healthy'
  const [isTransitioning, setIsTransitioning] = useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await checkHealth()
    } catch {
      // ignore errors
    } finally {
      setIsRefreshing(false)
      setRefreshToast(true)
      setTimeout(() => setRefreshToast(false), 2200)
    }
  }

  const handleTriggerLogout = useCallback(() => {
    if (isLoggingOut) return
    setShowLogoutConfirm(true)
  }, [isLoggingOut])

  const handleConfirmLogout = useCallback(() => {
    setShowLogoutConfirm(false)
    setIsLoggingOut(true)
  }, [])

  const handleFinalizeLogout = useCallback(async () => {
    try {
      await logout()
    } catch {
      // ignore errors
    } finally {
      setIsLoggingOut(false)
      setShowWelcome(false)
      setActiveView('dashboard')
      setNavHistory([])
    }
  }, [logout])

  // If user is not authenticated and not in unlock transition and not in logout exit, display login scene
  if (!isAuthenticated && !isTransitioning && !isLoggingOut) {
    return (
      <ErrorBoundary onReset={() => window.location.reload()}>
        <LoginScene
          onLoginSuccess={() => {
            setIsTransitioning(false)
            setShowWelcome(true)
            setActiveView('dashboard')
          }}
          login={login}
          register={register}
          authLoading={authLoading}
          authError={authError}
          isConnected={isConnected}
          latency={latency}
        />
      </ErrorBoundary>
    )
  }

  // AUTHENTICATED COMMAND CENTER APPLICATION SHELL
  return (
    <div className={`min-h-screen flex flex-col relative overflow-hidden transition-colors duration-200 ${
      theme === 'light'
        ? 'light-theme bg-slate-50 text-slate-900 selection:bg-cyan-500/20 selection:text-cyan-900'
        : 'dark bg-slate-950 text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200'
    }`}>
      {/* Personalized Welcome Overlay (2.3s Tailored Experience) */}
      {showWelcome && (
        <PersonalizedWelcomeOverlay
          user={user}
          onComplete={() => setShowWelcome(false)}
        />
      )}

      {/* Cinematic Security Access Unlock Transition */}
      {isTransitioning && (
        <SecurityUnlockTransition
          onComplete={() => setIsTransitioning(false)}
        />
      )}

      {/* Security Logout Door Lockdown Animation (2.8s) */}
      {isLoggingOut && (
        <SecurityLogoutDoor
          userName={customerPersona?.name || user?.name || user?.email?.split('@')[0] || 'Operator'}
          onComplete={handleFinalizeLogout}
        />
      )}

      {/* Logout Confirmation Dialog */}
      <LogoutConfirmModal
        isOpen={showLogoutConfirm}
        onClose={() => setShowLogoutConfirm(false)}
        onConfirm={handleConfirmLogout}
        userName={customerPersona?.name || user?.name || user?.email?.split('@')[0] || 'Operator'}
      />

      {/* Refresh Toast Feedback */}
      {refreshToast && (
        <div
          role="status"
          aria-live="polite"
          className="fixed top-20 right-6 z-50 flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/95 border border-cyan-500/60 text-cyan-200 text-xs font-mono shadow-[0_10px_30px_rgba(0,0,0,0.8),0_0_20px_rgba(6,182,212,0.25)] animate-fade-in pointer-events-none"
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="font-semibold text-slate-200">Dashboard refreshed</span>
        </div>
      )}

      <div
        className={`flex flex-1 overflow-hidden transition-all duration-700 ease-out ${
          isTransitioning || isLoggingOut ? 'opacity-75 scale-[0.99] filter blur-[0.5px]' : 'opacity-100 scale-100 filter-none'
        }`}
      >
        {/* Responsive Sidebar Navigation */}
        {activeView !== 'ai-copilot' && (
          <ErrorBoundary onReset={() => setActiveView('dashboard')}>
            <Sidebar
              activeView={activeView}
              setActiveView={navigateTo}
              isAdmin={isAdmin}
              user={user}
              logout={handleTriggerLogout}
              mobileOpen={mobileOpen}
              setMobileOpen={setMobileOpen}
              onOpenHowItWorks={() => setShowHowItWorks(true)}
              onOpenManual={() => setShowHowItWorks(true)}
              onOpenVoiceHelp={() => setShowHowItWorks(true)}
              onSelectPersona={handleSelectPersona}
            />
          </ErrorBoundary>
        )}

        {/* Main Content Layout */}
        <div
          className={`flex-1 flex flex-col min-w-0 ${
            activeView === 'ai-copilot' ? 'overflow-hidden h-screen' : 'overflow-y-auto'
          } transition-transform duration-500 ${
            isTransitioning ? 'translate-y-0.5' : 'translate-y-0'
          }`}
        >
          {/* Top Operational Navigation Bar (Clean, Minimal, Enterprise-Grade) */}
          {activeView !== 'ai-copilot' && (
            <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl sticky top-0 z-30 px-4 sm:px-6 h-16 flex items-center justify-between">
            {/* LEFT: Branding, Mobile Menu & Active View Context */}
            <div className="flex items-center gap-3 min-w-0">
              {/* Mobile sidebar toggle */}
              <button
                onClick={() => setMobileOpen(true)}
                className="lg:hidden p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition"
                aria-label="Open navigation menu"
              >
                <Menu className="w-5 h-5" />
              </button>

              {/* Back Button */}
              {navHistory.length > 0 && (
                <button
                  onClick={navigateBack}
                  title="Go back (Alt+←)"
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-cyan-300 text-xs font-semibold transition group cursor-pointer"
                  aria-label="Navigate back"
                >
                  <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform text-cyan-400" />
                  <span className="hidden sm:inline">Back</span>
                </button>
              )}

              {/* FraudLens AI Brand & Page Title */}
              <div className="flex items-center gap-2.5 truncate">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-500 via-indigo-600 to-purple-600 p-1 flex items-center justify-center shadow-[0_0_12px_rgba(6,182,212,0.35)] shrink-0">
                    <ShieldCheck className="w-4 h-4 text-white" />
                  </div>
                  <span className="font-extrabold text-sm tracking-tight text-white hidden md:inline">
                    FraudLens <span className="text-cyan-400">AI</span>
                  </span>
                </div>

                <span className="text-slate-600 hidden md:inline">/</span>

                <span className="text-xs font-semibold text-slate-300 truncate tracking-wide">
                  {activeView.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              </div>
            </div>

            {/* CENTER: Minimal & Spacious */}
            <div className="hidden md:flex flex-1" />

            {/* RIGHT: Operational Actions & Profile */}
            <div className="flex items-center gap-2.5">
              {/* Light / Dark Mode Toggle Button */}
              <button
                onClick={toggleTheme}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border transition-all text-xs font-semibold cursor-pointer ${
                  theme === 'light'
                    ? 'bg-white hover:bg-slate-100 text-slate-800 border-slate-300 shadow-sm'
                    : 'bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-amber-300 border-slate-800'
                }`}
                title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
                aria-label="Toggle Light/Dark Theme"
              >
                {theme === 'light' ? (
                  <>
                    <Moon className="w-4 h-4 text-indigo-600" />
                    <span className="hidden sm:inline">Dark</span>
                  </>
                ) : (
                  <>
                    <Sun className="w-4 h-4 text-amber-400" />
                    <span className="hidden sm:inline">Light</span>
                  </>
                )}
              </button>

              {/* Refresh Action */}
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 hover:border-slate-700 transition relative cursor-pointer"
                title="Refresh Dashboard"
                aria-label="Refresh Dashboard"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
              </button>

              {/* High-Graphics Interactive Module Guide Button */}
              <button
                onClick={() => setExplainerOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-slate-900 to-cyan-950/70 hover:from-cyan-950/90 hover:to-indigo-950/90 text-cyan-300 hover:text-white border border-cyan-500/40 hover:border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)] hover:shadow-[0_0_25px_rgba(6,182,212,0.5)] text-xs font-bold transition-all duration-300 group cursor-pointer active:scale-95"
                title="View interactive high-graphics 3D module guide"
                aria-label="View Module Guide"
              >
                <Sparkles className="w-3.5 h-3.5 text-cyan-400 group-hover:rotate-12 transition-transform" />
                <span className="hidden sm:inline">Module Guide</span>
              </button>

              {/* User Profile Pill */}
              <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-indigo-600 text-white flex items-center justify-center font-bold text-[10px] shrink-0 uppercase shadow-inner">
                  {isAdmin ? (user?.name ? user.name.charAt(0) : 'A') : (customerPersona?.name ? customerPersona.name.charAt(0) : (user?.name ? user.name.charAt(0) : 'U'))}
                </div>
                <div className="hidden sm:flex flex-col text-left leading-tight">
                  <span className="font-bold text-slate-200 text-xs truncate max-w-[120px]">
                    {isAdmin ? (user?.name || 'Administrator') : (customerPersona?.name || user?.name || user?.email?.split('@')[0] || 'User')}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {isAdmin ? 'System Admin' : (customerPersona?.name === 'Ajay' ? 'Enterprise' : 'User')}
                  </span>
                </div>
              </div>

              {/* Logout Action */}
              <button
                onClick={handleTriggerLogout}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-rose-950/40 text-slate-300 hover:text-rose-300 border border-slate-800 hover:border-rose-700/60 text-xs font-semibold transition group cursor-pointer"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5 text-slate-400 group-hover:text-rose-400 group-hover:translate-x-0.5 transition" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </header>
        )}

          {/* Dynamic Page Views */}
          <main className={activeView === 'ai-copilot' ? 'flex-1 overflow-hidden' : 'p-4 sm:p-6 lg:p-8 flex-1'}>
            <ErrorBoundary onReset={() => setActiveView('dashboard')}>
              {activeView === 'dashboard' && (
                isPremium ? (
                  <PremiumSecurityDashboard
                    user={user}
                    onNavigate={navigateTo}
                  />
                ) : (
                  <DashboardView
                    user={user}
                    isAdmin={isAdmin}
                    onSelectTransaction={handleSelectTransaction}
                    onOpenCase={() => navigateTo('investigations')}
                    onOpenPayment={isAdmin ? null : handleSelectPersona}
                  />
                )
              )}

              {(activeView === 'executive-transactions' || activeView === 'premium-transactions') && (
                <PremiumTransactionCenter
                  user={user}
                />
              )}

              {(activeView === 'security-center' || activeView === 'premium-security-center') && (
                <PremiumSecurityCenter
                  user={user}
                />
              )}

              {(activeView === 'fleet-security' || activeView === 'premium-devices' || activeView === 'premium-sessions') && (
                <FleetSecurityView
                  user={user}
                  isAdmin={isAdmin}
                />
              )}

              {(activeView === 'security-alerts' || activeView === 'premium-alerts') && (
                <PremiumAlertCenter
                  user={user}
                />
              )}

              {(activeView === 'audit-trail' || activeView === 'premium-audit') && (
                <PremiumAuditTrail
                  user={user}
                />
              )}

              {activeView === 'ai-copilot' && (
                <AiInvestigationCommandCenter
                  user={user}
                  isAdmin={isAdmin}
                  onNavigate={navigateTo}
                  onMinimize={handleMinimizeCommandCenter}
                />
              )}

              {activeView === 'payment' && !isAdmin && (
                <PaymentView
                  user={user}
                  isAdmin={isAdmin}
                  selectedPersona={selectedPersona}
                  onViewExplanation={handleViewExplanation}
                  onNavigateToInvestigations={() => navigateTo('live-monitor')}
                  onSelectTransaction={handleSelectTransaction}
                />
              )}

              {activeView === 'analyzer' && !isAdmin && (
                <TransactionRiskAnalyzerView
                  user={user}
                  isAdmin={isAdmin}
                  onViewExplanation={handleViewExplanation}
                  onNavigateToInvestigations={() => navigateTo('live-monitor')}
                  onSelectTransaction={handleSelectTransaction}
                />
              )}

              {(activeView === 'live-monitor' || activeView === 'investigations') && (
                <LiveMonitorAndInvestigationHub
                  user={user}
                  isAdmin={isAdmin}
                  initialTab={activeView === 'investigations' ? 'investigations' : 'monitor'}
                  initialTxId={targetTxId}
                  onViewExplanation={handleViewExplanation}
                />
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

              {activeView === 'explainable-ai' && (
                <ExplainableAiView
                  user={user}
                  isAdmin={isAdmin}
                  initialTransactionId={targetTxId}
                />
              )}

              {(activeView === 'model-lab' || activeView === 'admin-models') && (
                <ModelLabView user={user} isAdmin={isAdmin} />
              )}

              {(activeView === 'dataset-health' || activeView === 'admin-dataset') && (
                <DatasetHealthView user={user} isAdmin={isAdmin} />
              )}

              {activeView === 'audit-logs' && (
                <AuditLogsView />
              )}

              {activeView === 'settings' && (
                <SettingsView />
              )}
            </ErrorBoundary>
          </main>

          {/* Footer (hidden in full-screen AI copilot workspace) */}
          {activeView !== 'ai-copilot' && (
            <footer className="border-t border-slate-800/80 py-3 px-6 bg-slate-950/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
              <div>FraudLens AI — Financial Fraud Detection &amp; Explainability Platform</div>
              <div className="font-mono text-[11px]">29 Merchant Master Architecture • Real-Time AI</div>
            </footer>
          )}
        </div>
      </div>

      {/* Floating AI Assistant Panel — Gemini + Grok Chat */}
      <AiAssistantPanel
        user={user}
        isAdmin={isAdmin}
        currentView={activeView}
        currentTransactionId={''}
        isOpenExternal={aiAssistantOpen}
        onOpenChange={setAiAssistantOpen}
        onExpandToCommandCenter={handleExpandToCommandCenter}
        theme={theme}
      />

      {/* Interactive Unified How It Works (System Guide, Architecture & AI Voice Help) */}
      <HowItWorksModal
        isOpen={showHowItWorks}
        onClose={() => setShowHowItWorks(false)}
        user={user}
        isAdmin={isAdmin}
      />

      {/* High-Graphics 60 FPS HTML5 Canvas Module Explainer */}
      <ModuleInfoExplainer
        activeView={activeView}
        isOpenExternal={explainerOpen}
        onOpenChange={setExplainerOpen}
        showFloatingButton={true}
      />
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <CommandCenterApp />
      </AuthProvider>
    </ErrorBoundary>
  )
}
