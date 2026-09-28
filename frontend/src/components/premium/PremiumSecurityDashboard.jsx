import React, { useState, useEffect, useCallback } from 'react'
import {
  ShieldCheck,
  ShieldAlert,
  Shield,
  Activity,
  Cpu,
  Laptop,
  Smartphone,
  Globe,
  Radio,
  Clock,
  ArrowRight,
  Sparkles,
  Lock,
  Unlock,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
  Zap,
} from 'lucide-react'
import { premiumApi } from '../../services/api'
import ContextualModuleHelp from '../common/ContextualModuleHelp'

export default function PremiumSecurityDashboard({
  user,
  onNavigate,
}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  const loadDashboard = useCallback(async () => {
    try {
      setRefreshing(true)
      const res = await premiumApi.getDashboard()
      setData(res)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load premium dashboard.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
    const interval = setInterval(loadDashboard, 20000)
    return () => clearInterval(interval)
  }, [loadDashboard])

  const getHealthColor = (score) => {
    if (score >= 85) return 'text-emerald-400 border-emerald-500/60 bg-emerald-950/40'
    if (score >= 65) return 'text-cyan-400 border-cyan-500/60 bg-cyan-950/40'
    if (score >= 40) return 'text-amber-400 border-amber-500/60 bg-amber-950/40'
    return 'text-rose-400 border-rose-500/60 bg-rose-950/40'
  }

  const getRiskBadge = (level) => {
    switch (level) {
      case 'LOW':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-600/60'
      case 'MEDIUM':
        return 'bg-amber-950/80 text-amber-300 border-amber-600/60'
      case 'HIGH':
        return 'bg-rose-950/80 text-rose-300 border-rose-600/60'
      case 'CRITICAL':
        return 'bg-purple-950/90 text-purple-200 border-purple-500/70 shadow-[0_0_15px_rgba(168,85,247,0.4)]'
      default:
        return 'bg-slate-900 text-slate-300 border-slate-700'
    }
  }

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-indigo-950/80 border border-indigo-500/50 flex items-center justify-center animate-spin">
          <ShieldCheck className="w-6 h-6 text-indigo-400" />
        </div>
        <div className="font-mono text-xs text-indigo-300 tracking-wider uppercase animate-pulse">
          Establishing Hardware Enclave & Loading Defense State...
        </div>
      </div>
    )
  }

  const health = data?.security_health || { score: 98, status: 'Excellent', factors: [] }
  const profile = data?.behavioral_profile || {}
  const transactions = data?.recent_transactions || []
  const alerts = data?.recent_alerts || []
  const devices = data?.devices || []
  const sessions = data?.active_sessions || []

  return (
    <div className="space-y-6 animate-fade-in text-slate-100">
      {/* Premium Hero Banner */}
      <div className="relative rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border-2 border-indigo-500/40 p-6 sm:p-8 shadow-[0_0_40px_rgba(99,102,241,0.25)] overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="px-3 py-1 rounded-xl bg-indigo-900/90 text-indigo-200 border border-indigo-400/60 text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-[0_0_15px_rgba(99,102,241,0.35)]">
                <Sparkles className="w-3.5 h-3.5 text-indigo-300 animate-pulse" />
                ENTERPRISE SECURITY TIER
              </span>
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5 bg-emerald-950/60 px-2.5 py-1 rounded-xl border border-emerald-800">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Hardware Shield Active
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                Welcome, <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-purple-200 to-cyan-300">{data?.name || 'Ajay'}</span>
              </h1>
              <ContextualModuleHelp moduleKey="dashboard" />
            </div>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Real-time multi-signal adaptive protection powered by Scikit-Learn ML ensemble models, biometric keystroke baseline, and cryptographically isolated hardware enclave.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate && onNavigate('transactions')}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 hover:from-indigo-500 hover:to-purple-500 text-white font-mono text-xs font-bold uppercase tracking-wider shadow-[0_0_20px_rgba(99,102,241,0.45)] flex items-center gap-2 transition"
            >
              <Zap className="w-4 h-4" />
              <span>Transact / Run Scenarios</span>
            </button>

            <button
              onClick={loadDashboard}
              disabled={refreshing}
              className="p-2.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white transition"
              title="Refresh Defense Posture"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-indigo-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Defense Overview Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Security Health Score */}
        <div className={`p-5 rounded-3xl border ${getHealthColor(health.score)} backdrop-blur-md shadow-lg relative overflow-hidden`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-400">
              Security Health
            </span>
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black font-mono text-white">{health.score}</span>
            <span className="text-xs font-mono text-slate-400">/ 100</span>
          </div>
          <div className="mt-2 text-xs font-mono font-bold text-emerald-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            {health.status} Status
          </div>
        </div>

        {/* 2. Wallet Balance */}
        <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-400">
              Simulated Liquidity
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-bold">
              INR
            </span>
          </div>
          <div className="text-2xl sm:text-3xl font-black font-mono text-white truncate">
            ₹{Number(data?.wallet_balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="mt-2 text-xs font-mono text-slate-400">
            Account ID: <strong className="text-cyan-400">{data?.customer_id}</strong>
          </div>
        </div>

        {/* 3. Trusted Hardware Devices */}
        <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-400">
              Hardware Vault
            </span>
            <Cpu className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white">
            {health.trusted_devices_count} <span className="text-sm font-normal text-slate-400 font-sans">Enclaves</span>
          </div>
          <div className="mt-2 text-xs font-mono text-indigo-300 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
            MacBook Pro M3 + iPhone 15 Pro
          </div>
        </div>

        {/* 4. Active Sessions */}
        <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-400">
              Active Fleet Sessions
            </span>
            <Radio className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
          <div className="text-3xl font-black font-mono text-white">
            {health.active_sessions_count} <span className="text-sm font-normal text-slate-400 font-sans">Active</span>
          </div>
          <div className="mt-2 text-xs font-mono text-cyan-300 flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5 text-cyan-400" />
            Mumbai & Bangalore Tech Hubs
          </div>
        </div>
      </div>

      {/* Main Grid: Live Threat Alerts & Behavioral Invariants */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Transactions & Risk Evaluations */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  REAL-TIME TRANSACTION MONITOR
                </h3>
                <p className="text-xs text-slate-400">
                  Adaptive AI evaluation history with explainable risk breakdown.
                </p>
              </div>

              <button
                onClick={() => onNavigate && onNavigate('transactions')}
                className="text-xs font-mono text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
              >
                <span>View All</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {transactions.length === 0 ? (
              <div className="p-8 rounded-2xl bg-slate-950/60 border border-slate-800/60 text-center text-xs text-slate-400 font-mono">
                No recent transactions recorded. Use the "Transact / Run Scenarios" tool above to evaluate transactions.
              </div>
            ) : (
              <div className="space-y-2.5">
                {transactions.slice(0, 5).map((tx) => (
                  <div
                    key={tx.id || tx.transaction_id}
                    className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800/80 hover:border-indigo-500/50 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-white">
                          {tx.recipient || 'Cloud Provider'}
                        </span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${getRiskBadge(tx.risk_level)}`}>
                          {tx.risk_level} • {tx.risk_score}/100
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">
                          {tx.created_at ? new Date(tx.created_at).toLocaleTimeString() : 'Just now'}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                        <span>ID: {tx.transaction_id}</span>
                        <span>•</span>
                        <span>{tx.location || 'Mumbai Hub'}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-4">
                      <div className="text-right">
                        <div className="font-mono font-bold text-sm text-white">
                          ₹{Number(tx.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] font-mono uppercase text-indigo-300 font-semibold">
                          {tx.status}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Behavioral Baseline Snapshot */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
                  <Shield className="w-4 h-4 text-cyan-400" />
                  BEHAVIORAL PROFILE BASELINE
                </h3>
                <p className="text-xs text-slate-400">
                  Learned behavioral norms against which incoming activity is continuously scored.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800/80">
                <div className="text-[10px] font-mono text-slate-400 uppercase">Standard Transfer Amount</div>
                <div className="text-sm font-mono font-bold text-white mt-0.5">{profile.normal_transaction_range || '₹5,000 - ₹150,000'}</div>
                <div className="text-[10px] font-mono text-slate-500 mt-1">Historical Avg: ₹{Number(profile.average_transaction_amount || 45000).toLocaleString('en-IN')}</div>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800/80">
                <div className="text-[10px] font-mono text-slate-400 uppercase">Active Operational Hours</div>
                <div className="text-sm font-mono font-bold text-emerald-400 mt-0.5">{profile.common_transaction_times || '08:00 - 22:00 IST'}</div>
                <div className="text-[10px] font-mono text-slate-500 mt-1">Off-hours trigger step-up challenge</div>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800/80">
                <div className="text-[10px] font-mono text-slate-400 uppercase">Primary Geographies</div>
                <div className="text-sm font-mono font-bold text-white mt-0.5">{profile.common_locations || 'Mumbai, Bangalore, Singapore'}</div>
                <div className="text-[10px] font-mono text-slate-500 mt-1">Cross-border foreign IPs flagged</div>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800/80">
                <div className="text-[10px] font-mono text-slate-400 uppercase">Trusted Device Fleet</div>
                <div className="text-sm font-mono font-bold text-indigo-300 mt-0.5">{profile.trusted_devices || 'MacBook Pro M3 Max, iPhone 15 Pro Max'}</div>
                <div className="text-[10px] font-mono text-slate-500 mt-1">Hardware enclave cryptographic tokens</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Security Health Explanation & Live Alerts */}
        <div className="space-y-6">
          {/* Security Health Score Explainability */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              HEALTH EXPLAINABILITY
            </h3>

            <div className="space-y-2">
              {health.factors && health.factors.length > 0 ? (
                health.factors.map((factor, idx) => (
                  <div key={idx} className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800/80 text-xs font-mono text-slate-300 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{factor}</span>
                  </div>
                ))
              ) : (
                <div className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800/80 text-xs font-mono text-slate-300">
                  All baseline security invariants optimal. No active threat vectors.
                </div>
              )}
            </div>
          </div>

          {/* In-App Security Alerts */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                SECURITY ALERTS
              </h3>
              <button
                onClick={() => onNavigate && onNavigate('alerts')}
                className="text-xs font-mono text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
              >
                <span>Manage</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {alerts.length === 0 ? (
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/60 text-center text-xs text-slate-400 font-mono">
                No active security alerts. Platform running in optimal state.
              </div>
            ) : (
              <div className="space-y-2.5">
                {alerts.slice(0, 4).map((alert) => (
                  <div
                    key={alert.id || alert.alert_id}
                    className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-white font-mono">{alert.title}</span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700 font-bold">
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2">
                      {alert.message}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
