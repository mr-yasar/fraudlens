import React, { useState, useEffect } from 'react'
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CreditCard,
  TrendingUp,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowUpRight,
  RefreshCw,
  Sparkles,
  Smartphone,
  Laptop,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Radio,
  MapPin,
  ExternalLink,
  ChevronRight,
  ArrowDownLeft,
  ShoppingBag,
  Zap,
} from 'lucide-react'
import { dashboardApi } from '../services/api'
import MobileSecurityApprovalModal from './MobileSecurityApprovalModal'

export default function CustomerDashboardView({
  user,
  customerPersona,
  onSelectTransaction,
  onOpenPayment,
}) {
  const customerId = customerPersona.customerId
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Card Interactive States
  const [showBalance, setShowBalance] = useState(true)
  const [showCvv, setShowCvv] = useState(false)
  const [isCardFrozen, setIsCardFrozen] = useState(false)
  const [intlEnabled, setIntlEnabled] = useState(true)

  // Security OTP Step-Up Modal State
  const [activeApproval, setActiveApproval] = useState(null)

  const fetchCustomerData = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await dashboardApi.getCustomerDashboard(customerId)
      setData(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve personal customer dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCustomerData()
    const interval = setInterval(fetchCustomerData, 15000)
    return () => clearInterval(interval)
  }, [customerId])

  // Determine Persona Color Theme
  const isMonisha = customerId.includes('MONISHA')
  const isMohana = customerId.includes('MOHANA')
  const isSowmiya = customerId.includes('SOWMIYA')

  const theme = isMonisha
    ? {
        border: 'border-emerald-500/50',
        glow: 'shadow-[0_0_30px_rgba(16,185,129,0.25)]',
        cardBg: 'from-emerald-900 via-slate-900 to-teal-950',
        cardBorder: 'border-emerald-500/60',
        badge: 'bg-emerald-950/80 text-emerald-300 border-emerald-700',
        accentText: 'text-emerald-400',
        tag: 'Safe Habitual Consumer',
        riskTier: 'Low Risk (3.0% Fraud Rate)',
      }
    : isMohana
    ? {
        border: 'border-amber-500/50',
        glow: 'shadow-[0_0_30px_rgba(245,158,11,0.25)]',
        cardBg: 'from-amber-900 via-slate-900 to-orange-950',
        cardBorder: 'border-amber-500/60',
        badge: 'bg-amber-950/80 text-amber-300 border-amber-700',
        accentText: 'text-amber-400',
        tag: 'Elevated Velocity Profile',
        riskTier: 'Medium Risk (12.0% Fraud Rate)',
      }
    : {
        border: 'border-rose-500/50',
        glow: 'shadow-[0_0_30px_rgba(244,63,94,0.25)]',
        cardBg: 'from-rose-950 via-slate-900 to-red-950',
        cardBorder: 'border-rose-500/60',
        badge: 'bg-rose-950/80 text-rose-300 border-rose-700',
        accentText: 'text-rose-400',
        tag: 'High Risk ATO / Botnet Attack',
        riskTier: 'High Risk (26.0% Fraud Rate)',
      }

  const formatInr = (amt) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(amt || 0)
  }

  if (loading && !data) {
    return (
      <div className="space-y-6 animate-pulse p-4 sm:p-6">
        <div className="h-44 bg-slate-900/60 rounded-3xl border border-slate-800" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-900/60 rounded-2xl border border-slate-800" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-80 bg-slate-900/60 rounded-3xl border border-slate-800 lg:col-span-1" />
          <div className="h-80 bg-slate-900/60 rounded-3xl border border-slate-800 lg:col-span-2" />
        </div>
      </div>
    )
  }

  const pendingApprovals = data?.pending_approvals || []
  const recentTxs = data?.recent_transactions || []
  const categoryBreakdown = data?.category_breakdown || []
  const security = data?.security_summary || {}

  return (
    <div className="space-y-6">
      {/* 1. Header: Customer Identity & Real-Time Security Posture */}
      <div
        className={`p-5 sm:p-6 rounded-3xl bg-slate-950/90 border-2 ${theme.border} ${theme.glow} backdrop-blur-xl relative overflow-hidden`}
      >
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-cyan-500/10 via-purple-500/5 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="flex items-center gap-4">
            <div
              className={`w-14 h-14 rounded-2xl bg-gradient-to-tr ${theme.cardBg} border-2 ${theme.cardBorder} flex items-center justify-center text-white shadow-xl shadow-cyan-950/50 relative`}
            >
              <ShieldCheck className="w-8 h-8 text-cyan-300 animate-pulse" />
              <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-slate-950" />
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                  Welcome back, {data?.name || customerPersona.customerName}
                </h1>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${theme.badge}`}>
                  {theme.tag}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
                  {customerId}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  {data?.primary_location || 'Tamil Nadu'}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1 font-mono">
                  <Smartphone className="w-3.5 h-3.5 text-purple-400" />
                  {data?.primary_device || 'mobile_device'}
                </span>
                <span>•</span>
                <span className="text-emerald-400 font-semibold font-mono">
                  {data?.account_age_days || 30} Days Account Tenure
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchCustomerData}
              className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 transition"
              title="Refresh Balance & Telemetry"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>

            <button
              onClick={() => onOpenPayment && onOpenPayment(customerPersona.defaultPresetId)}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-cyan-950/50 flex items-center gap-2 transition active:scale-95"
            >
              <Zap className="w-4 h-4 text-amber-300" />
              <span>Make New Payment</span>
            </button>
          </div>
        </div>

        {/* Pending Security Reviews Alert Banner (for Mohana or elevated cases) */}
        {pendingApprovals.length > 0 && (
          <div className="mt-4 p-3.5 rounded-2xl bg-amber-950/60 border border-amber-600 text-amber-200 text-xs flex flex-wrap items-center justify-between gap-3 shadow-lg animate-pulse">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
              <div>
                <strong>Action Required: {pendingApprovals.length} Step-Up Security Challenge(s) Pending</strong>
                <p className="text-[11px] text-amber-300/80">
                  Suspicious high-value activity detected. Review and authorize with your SMS One-Time Passcode (OTP).
                </p>
              </div>
            </div>
            <button
              onClick={() => setActiveApproval(pendingApprovals[0])}
              className="px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow transition active:scale-95 shrink-0"
            >
              Review &amp; Enter OTP &rarr;
            </button>
          </div>
        )}
      </div>

      {/* 2. Four Master Financial & AI Defense Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Available Account Balance */}
        <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition shadow-lg relative overflow-hidden group">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Available Balance</span>
            <button
              onClick={() => setShowBalance(!showBalance)}
              className="p-1 text-slate-400 hover:text-white transition"
              title={showBalance ? 'Hide Balance' : 'Show Balance'}
            >
              {showBalance ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            </button>
          </div>
          <div className="text-2xl font-black text-white font-mono mt-2 tracking-tight">
            {showBalance ? formatInr(data?.account_balance) : '••••••••'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between font-mono">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>Checking • INR</span>
            </span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 font-bold border border-emerald-700">
              +₹15L Active
            </span>
          </div>
        </div>

        {/* Metric 2: Lifetime Transaction Spending */}
        <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition shadow-lg relative overflow-hidden group">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Total Volume</span>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-cyan-300 font-mono mt-2 tracking-tight">
            {formatInr(data?.total_spent_amount)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            {data?.total_transactions_count?.toLocaleString()} Lifetime Transactions
          </div>
        </div>

        {/* Metric 3: AI Fraud Defense Ratio */}
        <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition shadow-lg relative overflow-hidden group">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Fraud Defense Ratio</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono mt-2 tracking-tight flex items-baseline gap-2">
            <span>{data?.fraud_rate_percentage?.toFixed(1)}%</span>
            <span className="text-xs text-slate-400 font-normal">Incidence</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono flex items-center justify-between">
            <span className="text-emerald-400 font-bold">
              {security.clean_transactions_count || 0} Clean
            </span>
            <span className="text-rose-400 font-bold">
              {security.blocked_transactions_count || 0} Isolated
            </span>
          </div>
        </div>

        {/* Metric 4: Security Health State */}
        <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition shadow-lg relative overflow-hidden group">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Shield State</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-black mt-2 tracking-tight flex items-center gap-2">
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase ${
                security.security_posture === 'SECURE'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                  : security.security_posture === 'ELEVATED_RISK'
                  ? 'bg-amber-950 text-amber-300 border border-amber-700'
                  : 'bg-rose-950 text-rose-300 border border-rose-700'
              }`}
            >
              {security.security_posture || 'SECURE'}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            {security.trusted_devices_count || 1} Registered Devices • TreeSHAP Active
          </div>
        </div>
      </div>

      {/* 3. Center Section: 3D Holographic Card + Category Spending Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Virtual Cyber Card & Controls */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-cyan-400" />
              <span>Digital Security Card</span>
            </h3>
            <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
              Virtual Debit
            </span>
          </div>

          {/* Interactive Virtual Card */}
          <div
            className={`w-full aspect-[1.586/1] rounded-3xl p-5 sm:p-6 bg-gradient-to-tr ${theme.cardBg} border-2 ${theme.cardBorder} shadow-2xl relative flex flex-col justify-between overflow-hidden transition-transform duration-500 hover:scale-[1.02]`}
          >
            {/* Card Holographic Sheen Overlay */}
            <div className="absolute inset-0 bg-gradient-to-tr from-white/10 via-transparent to-black/40 pointer-events-none" />
            <div className="absolute -right-12 -top-12 w-40 h-40 rounded-full bg-cyan-400/20 blur-2xl pointer-events-none" />

            {/* Top Row: Bank Brand & NFC Chip */}
            <div className="flex items-center justify-between relative z-10">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-cyan-400/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 font-black text-xs font-mono">
                  FL
                </div>
                <span className="font-extrabold text-white text-xs tracking-wider uppercase font-mono">
                  FraudLens Private Bank
                </span>
              </div>
              <Radio className="w-5 h-5 text-white/70 rotate-90" />
            </div>

            {/* Chip & Status */}
            <div className="relative z-10 flex items-center justify-between">
              <div className="w-10 h-7 rounded-md bg-gradient-to-br from-amber-200 to-amber-500 border border-amber-600/60 shadow-inner" />
              {isCardFrozen && (
                <span className="px-2 py-0.5 rounded bg-rose-950/90 text-rose-300 text-[10px] font-mono font-bold border border-rose-700 flex items-center gap-1">
                  <Lock className="w-3 h-3" /> FROZEN
                </span>
              )}
            </div>

            {/* Middle: Masked PAN Number */}
            <div className="relative z-10 py-1">
              <div className="text-base sm:text-lg font-mono font-bold text-white tracking-widest flex items-center gap-3">
                <span>••••</span>
                <span>••••</span>
                <span>••••</span>
                <span>{data?.card_last4 || '4092'}</span>
              </div>
            </div>

            {/* Bottom: Cardholder Name, Expiry & CVV */}
            <div className="flex items-end justify-between relative z-10 text-[11px] font-mono">
              <div>
                <span className="text-[9px] text-slate-400 block uppercase">Cardholder</span>
                <span className="font-bold text-white uppercase">{data?.name || customerPersona.customerName}</span>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">Expires</span>
                  <span className="font-bold text-slate-200">{data?.card_expiry || '09/29'}</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-400 block uppercase">CVV</span>
                  <button
                    onClick={() => setShowCvv(!showCvv)}
                    className="font-bold text-cyan-300 hover:underline"
                  >
                    {showCvv ? '892' : '•••'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Card Controls */}
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 flex items-center gap-2">
                {isCardFrozen ? <Lock className="w-3.5 h-3.5 text-rose-400" /> : <Unlock className="w-3.5 h-3.5 text-emerald-400" />}
                <span>Freeze / Lock Card</span>
              </span>
              <button
                onClick={() => setIsCardFrozen(!isCardFrozen)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition font-mono ${
                  isCardFrozen
                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                    : 'bg-slate-800 text-slate-300 hover:text-white border border-slate-700'
                }`}
              >
                {isCardFrozen ? 'Unfreeze' : 'Freeze Card'}
              </button>
            </div>

            <div className="flex items-center justify-between border-t border-slate-800/60 pt-2">
              <span className="text-slate-300 flex items-center gap-2">
                <GlobeIcon className="w-3.5 h-3.5 text-cyan-400" />
                <span>International Usage</span>
              </span>
              <button
                onClick={() => setIntlEnabled(!intlEnabled)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition font-mono ${
                  intlEnabled
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                {intlEnabled ? 'ACTIVE' : 'BLOCKED'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Spending Category Analysis */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <ShoppingBag className="w-4 h-4 text-cyan-400" />
              <span>Spending Velocity by Merchant Category</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-400">
              Computed from {data?.total_transactions_count} real transactions
            </span>
          </div>

          <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
            {categoryBreakdown.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                Loading category telemetry...
              </div>
            ) : (
              categoryBreakdown.map((cat, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-cyan-400" />
                      {cat.category}
                    </span>
                    <div className="flex items-center gap-3 font-mono text-[11px]">
                      <span className="text-slate-400">{cat.count} purchases</span>
                      <span className="font-bold text-cyan-300">{formatInr(cat.total_spent)}</span>
                      <span className="text-slate-500 font-semibold">{cat.percentage}%</span>
                    </div>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-600 transition-all duration-700"
                      style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                    />
                  </div>
                </div>
              ))
            )}

            <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-[11px] text-slate-400 gap-2">
              <span>Risk profiling calibrated against 29 Master Commercial Merchants</span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Zero Data Leakage Enforced
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Recent Customer Transactions Ledger */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Personal Account Transaction Activity
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Showing latest {recentTxs.length} records
          </span>
        </div>

        <div className="rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Transaction ID</th>
                  <th className="py-3 px-4">Merchant / Beneficiary</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Risk Decision</th>
                  <th className="py-3 px-4">AI Score</th>
                  <th className="py-3 px-4 text-right">SHAP Explainability</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {recentTxs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-500 text-xs">
                      No recent transactions recorded for this account.
                    </td>
                  </tr>
                ) : (
                  recentTxs.map((tx) => {
                    const isHigh = tx.risk_level === 'HIGH' || tx.decision === 'BLOCKED'
                    const isMed = tx.risk_level === 'MEDIUM' || tx.decision === 'STEP_UP_REQUIRED'
                    const isApproved = !isHigh && !isMed

                    return (
                      <tr key={tx.id || tx.transaction_id} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-4 font-bold text-cyan-400">
                          {tx.transaction_id}
                        </td>
                        <td className="py-3 px-4 text-white font-sans font-medium">
                          {tx.merchant_name || tx.merchant_category}
                        </td>
                        <td className="py-3 px-4 text-slate-400 font-sans text-[11px]">
                          {tx.merchant_category}
                        </td>
                        <td className="py-3 px-4 font-bold text-white">
                          {formatInr(tx.amount)}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              isApproved
                                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                                : isMed
                                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                : 'bg-rose-950 text-rose-300 border border-rose-800'
                            }`}
                          >
                            {tx.decision || (isApproved ? 'APPROVED' : 'BLOCKED')}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`font-bold ${isHigh ? 'text-rose-400' : isMed ? 'text-amber-400' : 'text-emerald-400'}`}>
                            {Math.round(tx.risk_score || (tx.fraud_probability * 100) || 0)} / 100
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => onSelectTransaction && onSelectTransaction(tx.transaction_id)}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-xs font-sans font-medium transition"
                          >
                            Inspect SHAP &rarr;
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Security Approval Modal if User Clicks a Challenge */}
      {activeApproval && (
        <MobileSecurityApprovalModal
          isOpen={Boolean(activeApproval)}
          onClose={() => setActiveApproval(null)}
          onApproved={() => {
            setActiveApproval(null)
            fetchCustomerData()
          }}
          onRejected={() => {
            setActiveApproval(null)
            fetchCustomerData()
          }}
          transactionData={{
            transaction_id: activeApproval.transaction_id,
            amount: activeApproval.amount,
            merchant_name: activeApproval.merchant_category,
            risk_level: activeApproval.risk_level,
            risk_score: activeApproval.risk_score,
            customer_name: data?.name || customerPersona.customerName,
          }}
        />
      )}
    </div>
  )
}

function GlobeIcon(props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
      <path d="M2 12h20" />
    </svg>
  )
}
