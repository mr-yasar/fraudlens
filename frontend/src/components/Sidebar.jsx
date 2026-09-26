import React from 'react'
import {
  LayoutDashboard,
  BrainCircuit,
  Radio,
  Store,
  History,
  Users,
  Smartphone,
  ShieldAlert,
  Sparkles,
  Cpu,
  Database,
  BarChart3,
  FileSpreadsheet,
  Settings,
  LogOut,
  ShieldCheck,
  BookOpen,
  X,
  CreditCard,
  Zap,
  UserCheck,
  Bot,
  Volume2,
  Lightbulb,
} from 'lucide-react'
import { getCustomerPersona } from '../utils/customerHelper'

export default function Sidebar({
  activeView,
  setActiveView,
  isAdmin,
  user,
  logout,
  mobileOpen,
  setMobileOpen,
  onOpenHowItWorks,
  onOpenManual,
  onOpenVoiceHelp,
  onSelectPersona,
}) {
  const isCustomer = user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user'
  const customerPersona = getCustomerPersona(user)

  // All modules open for both customer and admin, with contextual labeling
  const primaryNav = [
    { id: 'dashboard', label: isCustomer ? 'Security Dashboard' : 'Command Dashboard', icon: LayoutDashboard },
    { id: 'payment', label: 'Payment Gateway (Pre-Auth)', icon: CreditCard },
    { id: 'analyzer', label: 'Transaction Risk Analyzer', icon: BrainCircuit },
    { id: 'live-monitor', label: isCustomer ? 'Account Live Radar' : 'Live Fraud Monitor', icon: Radio },
    { id: 'merchants', label: 'Merchant Intelligence', icon: Store },
    { id: 'transactions', label: isCustomer ? 'My Transactions' : 'All Transactions', icon: History },
    { id: 'customers', label: isCustomer ? 'My Customer Profile' : 'Customer Intelligence', icon: Users },
    { id: 'explainable-ai', label: 'Explainable AI & SHAP', icon: Sparkles },
    { id: 'investigations', label: isCustomer ? 'Security Cases & Alerts' : 'Fraud Investigations', icon: ShieldAlert },
    { id: 'model-lab', label: 'Model Lab & Registry', icon: Cpu },
    { id: 'dataset-health', label: 'Dataset Health & Audit', icon: Database },
    { id: 'reports', label: isCustomer ? 'Account Security Reports' : 'Reports & Analytics', icon: BarChart3 },
  ]

  const systemNav = [
    { id: 'audit-logs', label: 'Audit Trail & Compliance', icon: FileSpreadsheet },
    { id: 'settings', label: 'Platform Settings', icon: Settings },
  ]

  const handleSelect = (id) => {
    setActiveView(id)
    if (setMobileOpen) setMobileOpen(false)
  }

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-950/95 backdrop-blur-xl border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div>
          <div className="h-16 border-b border-slate-800/80 px-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-sm font-extrabold tracking-wider text-white uppercase flex items-center gap-1.5">
                  FraudLens <span className="text-cyan-400">AI</span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono tracking-tight">
                  {isCustomer ? 'Customer Portal' : 'Security Command Center'}
                </div>
              </div>
            </div>

            {/* Mobile close button */}
            <button
              onClick={() => setMobileOpen(false)}
              className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-900"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-5 overflow-y-auto max-h-[calc(100vh-140px)]">
            {/* Real-Time Personas Quick Launch Panel (Admin audits all 3; Customer watches only their own) */}
            {isCustomer ? (
              <div className="p-3 rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-950/90 to-emerald-950/30 border border-emerald-800/50 shadow-lg">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-300 font-extrabold flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Verified Customer
                  </span>
                  <span className="text-[9px] font-mono bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800 font-bold">
                    Logged In
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                  <div className="text-xs font-bold text-white flex items-center justify-between">
                    <span>{customerPersona.name}</span>
                    <span className="text-[10px] font-mono text-emerald-400 font-semibold">{customerPersona.fraudRate}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    ID: <strong className="text-cyan-400">{customerPersona.customerId}</strong>
                  </div>
                  <div className="text-[10px] text-emerald-400/90 font-mono">
                    {customerPersona.baselineType}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleSelect('payment')}
                  className="w-full mt-2.5 py-1.5 px-2 rounded-lg bg-emerald-950/70 hover:bg-emerald-900/80 border border-emerald-800/80 text-emerald-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  <CreditCard className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Open My Gateway</span>
                </button>
              </div>
            ) : (
              <div className="p-3 rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-950/90 to-cyan-950/30 border border-cyan-800/50 shadow-lg shadow-cyan-950/30">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-300 font-extrabold flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                    Personas (Admin Audit)
                  </span>
                  <span className="text-[9px] font-mono bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800 font-bold">
                    All 3
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 leading-tight mb-2">
                  Admin authority: audit all 3 student customer baselines:
                </p>
                <div className="space-y-1">
                  <button
                    type="button"
                    onClick={() => {
                      if (onSelectPersona) onSelectPersona('scenario_monisha_safe')
                      else handleSelect('payment')
                    }}
                    className="w-full text-left px-2 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/70 border border-emerald-800/70 text-emerald-300 text-xs font-semibold flex items-center justify-between transition group"
                  >
                    <span className="truncate">🟢 Monisha</span>
                    <span className="text-[10px] font-mono font-bold bg-emerald-900/90 px-1.5 py-0.5 rounded text-emerald-200">
                      3% SAFE
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (onSelectPersona) onSelectPersona('scenario_mohana_review')
                      else handleSelect('payment')
                    }}
                    className="w-full text-left px-2 py-1.5 rounded-lg bg-amber-950/60 hover:bg-amber-900/70 border border-amber-800/70 text-amber-300 text-xs font-semibold flex items-center justify-between transition group"
                  >
                    <span className="truncate">🟡 Mohana</span>
                    <span className="text-[10px] font-mono font-bold bg-amber-900/90 px-1.5 py-0.5 rounded text-amber-200">
                      12% OTP
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (onSelectPersona) onSelectPersona('scenario_sowmiya_block')
                      else handleSelect('payment')
                    }}
                    className="w-full text-left px-2 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900/70 border border-rose-800/70 text-rose-300 text-xs font-semibold flex items-center justify-between transition group"
                  >
                    <span className="truncate">🔴 Sowmiya</span>
                    <span className="text-[10px] font-mono font-bold bg-rose-900/90 px-1.5 py-0.5 rounded text-rose-200">
                      26% BLOCK
                    </span>
                  </button>
                </div>
              </div>
            )}

            {/* Core Operation Section */}
            <div>
              <div className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-slate-400">
                {isCustomer ? 'User Operations' : 'Fraud Operations'}
              </div>
              <ul className="space-y-1">
                {primaryNav.map((item) => {
                  const Icon = item.icon
                  const isActive = activeView === item.id
                  return (
                    <li key={item.id}>
                      <button
                        onClick={() => handleSelect(item.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition duration-150 ${
                          isActive
                            ? 'bg-gradient-to-r from-cyan-950/80 to-slate-900 text-cyan-300 border border-cyan-800/60 shadow-md shadow-cyan-950/40 font-semibold'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                        }`}
                      >
                        <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                        <span>{item.label}</span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>

            {/* System Section (for Investigators / Admins) */}
            {!isCustomer && (
              <div>
                <div className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-slate-400">
                  Governance &amp; Logs
                </div>
                <ul className="space-y-1">
                  {systemNav.map((item) => {
                    const Icon = item.icon
                    const isActive = activeView === item.id
                    return (
                      <li key={item.id}>
                        <button
                          onClick={() => handleSelect(item.id)}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition duration-150 ${
                            isActive
                              ? 'bg-gradient-to-r from-slate-900 to-slate-800 text-cyan-300 border border-slate-700 font-semibold'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                          }`}
                        >
                          <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                          <span>{item.label}</span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}

            {/* Quick Action: Unified How It Works (System Guide & AI Voice Help) */}
            <div className="pt-2">
              <button
                type="button"
                onClick={() => {
                  if (onOpenHowItWorks) onOpenHowItWorks()
                  else if (onOpenManual) onOpenManual()
                  if (setMobileOpen) setMobileOpen(false)
                }}
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-cyan-950/80 via-indigo-950/80 to-slate-900 border border-cyan-500/60 text-cyan-200 shadow-lg shadow-cyan-950/50 hover:border-cyan-400 hover:text-white transition group"
                title="Open How It Works: Interactive Guide, Architecture, Personas & AI Voice Explainer"
              >
                <div className="flex items-center gap-2.5">
                  <Lightbulb className="w-4 h-4 text-cyan-300 group-hover:scale-110 transition-transform animate-pulse" />
                  <span>How It Works</span>
                </div>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-900/90 text-cyan-200 font-bold flex items-center gap-1 border border-cyan-700">
                  <Volume2 className="w-2.5 h-2.5 text-cyan-300" />
                  Guide + Voice
                </span>
              </button>
            </div>
          </nav>
        </div>

        {/* User Profile & Logout */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/60">
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="truncate pr-2">
              <div className="text-xs font-bold text-white truncate">{user?.name || 'Operator'}</div>
              <div className="text-[10px] font-mono text-cyan-400 truncate uppercase">
                {user?.role || 'FRAUD_INVESTIGATOR'}
              </div>
            </div>
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 border border-slate-700/60 transition"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
