import React from 'react'
import {
  LayoutDashboard,
  CreditCard,
  Users,
  BrainCircuit,
  Sparkles,
  ShieldAlert,
  BarChart3,
  FileSpreadsheet,
  Cpu,
  History,
  Settings,
  LogOut,
  ShieldCheck,
  Network,
  Share2,
  Sliders,
  X,
} from 'lucide-react'

export default function Sidebar({
  activeView,
  setActiveView,
  isAdmin,
  user,
  logout,
  mobileOpen,
  setMobileOpen,
}) {
  const primaryNav = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'payment', label: 'Risk Simulator', icon: CreditCard },
    { id: 'transactions', label: 'Transactions', icon: History },
    { id: 'customers', label: 'Customers', icon: Users },
    { id: 'predictions', label: 'AI Predictions', icon: BrainCircuit },
    { id: 'explainable-ai', label: 'Explainable AI', icon: Sparkles },
    { id: 'fraud-intelligence', label: 'Fraud Intelligence', icon: Share2 },
    { id: 'adaptive-intelligence', label: 'Adaptive Intelligence', icon: Sliders },
    { id: 'investigations', label: 'Investigations', icon: ShieldAlert },
    { id: 'reports', label: 'Reports & Analytics', icon: BarChart3 },
  ]

  const adminNav = [
    { id: 'admin-dataset', label: 'Training Dataset', icon: FileSpreadsheet },
    { id: 'admin-models', label: 'Model Management', icon: Cpu },
  ]

  const systemNav = [
    { id: 'audit-logs', label: 'Audit Logs', icon: History },
    { id: 'settings', label: 'System Settings', icon: Settings },
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
                <div className="text-[10px] text-slate-400 font-mono tracking-tight">Security Command Center</div>
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
          <nav className="p-3 space-y-6 overflow-y-auto max-h-[calc(100vh-140px)]">
            {/* Core Operation Section */}
            <div>
              <div className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-slate-400">
                Operations
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

            {/* Admin Section (Strict RBAC Boundary) */}
            {isAdmin && (
              <div>
                <div className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-purple-400 flex items-center justify-between">
                  <span>Administration</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-950 border border-purple-800/80 font-bold">
                    ADMIN
                  </span>
                </div>
                <ul className="space-y-1">
                  {adminNav.map((item) => {
                    const Icon = item.icon
                    const isActive = activeView === item.id
                    return (
                      <li key={item.id}>
                        <button
                          onClick={() => handleSelect(item.id)}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition duration-150 ${
                            isActive
                              ? 'bg-gradient-to-r from-purple-950/80 to-slate-900 text-purple-300 border border-purple-800/60 shadow-md font-semibold'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                          }`}
                        >
                          <Icon className={`w-4 h-4 ${isActive ? 'text-purple-400' : 'text-slate-400'}`} />
                          <span>{item.label}</span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}

            {/* System Section */}
            <div>
              <div className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-slate-400">
                System &amp; Compliance
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
          </nav>
        </div>

        {/* User Profile & Logout */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/60">
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="truncate pr-2">
              <div className="text-xs font-bold text-white truncate">{user?.name || 'Operator'}</div>
              <div className="text-[10px] font-mono text-cyan-400 truncate">{user?.role || 'FRAUD_INVESTIGATOR'}</div>
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
