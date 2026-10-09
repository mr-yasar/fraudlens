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
  Bell,
  X,
  Sliders,
  DollarSign,
  Fingerprint,
} from 'lucide-react'
import { dashboardApi } from '../services/api'
import MobileSecurityApprovalModal from './MobileSecurityApprovalModal'
import { sound } from './login/soundEffects'
import GlobalCenterModal from './common/GlobalCenterModal'
import ContextualModuleHelp from './common/ContextualModuleHelp'

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

  // Real-Time Notification Banner State
  const [notification, setNotification] = useState(null)

  // Security OTP Step-Up Modal State
  const [activeApproval, setActiveApproval] = useState(null)

  // Global Centered Modal State for all clickable widgets
  const [activeModal, setActiveModal] = useState(null) // null | { type: string, title: string, subtitle: string, data?: any }

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
    // Rapid 4-second poll interval ensures fast real-time synchronization
    const interval = setInterval(fetchCustomerData, 4000)
    return () => clearInterval(interval)
  }, [customerId])

  // Real-Time Server-Sent Events (SSE) Stream Subscription
  useEffect(() => {
    let evtSource = null
    try {
      evtSource = new EventSource('/api/v1/events/stream')
      evtSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          if (
            payload.event_type?.includes('approval') ||
            payload.event_type?.includes('payment') ||
            payload.event_type === 'notification'
          ) {
            fetchCustomerData()
            if (payload.event_type === 'notification' && (!payload.data?.customer_id || payload.data.customer_id === customerId)) {
              setNotification({
                type: payload.data.type || 'SUCCESS',
                title: payload.data.title || 'Security Notification',
                message: payload.data.message || '',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
              })
              sound?.playVerified && sound.playVerified()
            }
          }
        } catch {
          // Ignore JSON parse errors on ping events
        }
      }
    } catch {
      // Fallback gracefully to rapid polling
    }
    return () => {
      if (evtSource) evtSource.close()
    }
  }, [customerId])

  // Auto-dismiss real-time notification after 7 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null)
      }, 7000)
      return () => clearTimeout(timer)
    }
  }, [notification])

  // Real-Time Approval Authorization Handler
  const handleApproveChallenge = async (approvalId, otpCode) => {
    try {
      const token = localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')
      const targetApproval = (data?.pending_approvals || []).find((a) => a.approval_id === approvalId) || activeApproval
      const res = await fetch(`/api/v1/approvals/${approvalId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          challenge_response: otpCode,
          channel: 'CUSTOMER_PORTAL_OTP',
          notes: 'Customer verified and authorized via SMS OTP in Customer Portal',
        }),
      })

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || 'Approval authorization failed on server')
      }

      // Close the modal immediately so the modal banner and screen clears smoothly
      setActiveApproval(null)

      // Play verified audio chime
      sound?.playVerified && sound.playVerified()

      // Real-Time Notification Banner
      const amt = targetApproval?.amount || 14500
      const merchant = targetApproval?.merchant_category || 'CircuitBay Electronics'
      setNotification({
        type: 'SUCCESS',
        title: 'Payment Authorized Successfully!',
        message: `SMS OTP verified. Payment of ₹${Number(amt).toLocaleString('en-IN')} to ${merchant} has been authorized and completed in real-time.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      })

      // IMMEDIATELY update local state to remove this pending approval and adjust balance
      setData((prev) => {
        if (!prev) return prev
        const remaining = (prev.pending_approvals || []).filter((a) => a.approval_id !== approvalId)
        return {
          ...prev,
          pending_approvals: remaining,
          pending_approvals_count: remaining.length,
          account_balance: Math.max(0, (prev.account_balance || 547855) - amt),
          security_summary: {
            ...(prev.security_summary || {}),
            pending_reviews_count: remaining.length,
          },
        }
      })

      // Fetch fresh verified data in the background
      setTimeout(() => {
        fetchCustomerData()
      }, 500)
    } catch (err) {
      console.error('Error approving challenge:', err)
      throw err
    }
  }

  // Real-Time Reject Handler
  const handleRejectChallenge = async (approvalId, reason) => {
    try {
      const token = localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')
      await fetch(`/api/v1/approvals/${approvalId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          reason: reason || 'Customer flagged as unrecognized',
          notes: 'Customer rejected verification in portal',
        }),
      })

      sound?.playError && sound.playError()

      // Real-Time Notification Banner
      setNotification({
        type: 'WARNING',
        title: 'Suspicious Transaction Cancelled',
        message: `Verification challenge declined. Transaction cancelled and flagged for fraud investigation review.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      })

      // Instantly remove from pending
      setData((prev) => {
        if (!prev) return prev
        const remaining = (prev.pending_approvals || []).filter((a) => a.approval_id !== approvalId)
        return {
          ...prev,
          pending_approvals: remaining,
          pending_approvals_count: remaining.length,
          security_summary: {
            ...(prev.security_summary || {}),
            pending_reviews_count: remaining.length,
          },
        }
      })

      setTimeout(() => {
        fetchCustomerData()
      }, 800)
    } catch (err) {
      console.error('Error rejecting challenge:', err)
      throw err
    }
  }

  // Determine Persona Color Theme (Case-insensitive)
  const isMonisha = (customerId || '').toUpperCase().includes('MONISHA') || (data?.customer_id || '').toUpperCase().includes('MONISHA')
  const isMohana = (customerId || '').toUpperCase().includes('MOHANA') || (data?.customer_id || '').toUpperCase().includes('MOHANA')
  const isSowmiya = (customerId || '').toUpperCase().includes('SOWMIYA') || (data?.customer_id || '').toUpperCase().includes('SOWMIYA')

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

  const pendingApprovals = isMonisha ? [] : (data?.pending_approvals || [])
  const recentTxs = data?.recent_transactions || []
  const categoryBreakdown = data?.category_breakdown || []
  const security = data?.security_summary || {}

  return (
    <div className="space-y-6">
      {/* Real-Time Security Notification Banner (Triggered upon OTP verification or action) */}
      {notification && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/95 via-slate-950 to-teal-950/95 border-2 border-emerald-500 shadow-[0_0_35px_rgba(16,185,129,0.35)] flex items-center justify-between gap-4 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex items-center gap-3.5">
            <div className="p-2.5 rounded-xl bg-emerald-500 text-slate-950 font-bold shadow-lg shadow-emerald-500/40 shrink-0">
              <ShieldCheck className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] font-black uppercase text-emerald-400 tracking-wider flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  REAL-TIME NOTIFICATION
                </span>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                  {notification.timestamp}
                </span>
              </div>
              <h4 className="text-sm font-bold text-white mt-0.5">{notification.title}</h4>
              <p className="text-xs text-emerald-200/90 mt-0.5">{notification.message}</p>
            </div>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition"
            aria-label="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

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
                <ContextualModuleHelp moduleKey="dashboard" />
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

        {/* Pending Security Reviews Alert Banner (for all customers with pending challenges) */}
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

      {/* 2. Four Master Financial & AI Defense Metrics (Click to inspect centered modals) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Available Account Balance */}
        <div
          onClick={() => setActiveModal({
            type: 'BALANCE',
            title: 'Account Liquidity & Active Reserves',
            subtitle: `Verified Account: ${customerId} • Primary Currency: INR (₹)`,
            badge: 'LIQUID ASSETS',
            badgeType: 'success',
            icon: DollarSign,
          })}
          className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 transition cursor-pointer shadow-lg relative overflow-hidden group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px] group-hover:text-cyan-300 transition">Available Balance</span>
            <div className="flex items-center gap-1">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowBalance(!showBalance)
                }}
                className="p-1 text-slate-400 hover:text-white transition"
                title={showBalance ? 'Hide Balance' : 'Show Balance'}
              >
                {showBalance ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              </button>
              <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition" />
            </div>
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
              Verified Account
            </span>
          </div>
        </div>

        {/* Metric 2: Lifetime Transaction Spending */}
        <div
          onClick={() => setActiveModal({
            type: 'VOLUME',
            title: 'Lifetime Spending Velocity & Volume',
            subtitle: `Cumulative Volume Across ${data?.total_transactions_count?.toLocaleString() || 0} Transactions`,
            badge: 'FINANCIAL VELOCITY',
            badgeType: 'info',
            icon: TrendingUp,
          })}
          className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 transition cursor-pointer shadow-lg relative overflow-hidden group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px] group-hover:text-cyan-300 transition">Total Volume</span>
            <TrendingUp className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-black text-cyan-300 font-mono mt-2 tracking-tight">
            {formatInr(data?.total_spent_amount)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono flex items-center justify-between">
            <span>{data?.total_transactions_count?.toLocaleString()} Lifetime Txs</span>
            <span className="text-cyan-400 text-[10px] group-hover:underline">Inspect &rarr;</span>
          </div>
        </div>

        {/* Metric 3: AI Fraud Defense Ratio */}
        <div
          onClick={() => setActiveModal({
            type: 'FRAUD_RATIO',
            title: 'AI Defense Ratio & Threat Isolation',
            subtitle: `Real-time calibration against ML baseline and 29 commercial merchants`,
            badge: `${data?.fraud_rate_percentage?.toFixed(1)}% INCIDENCE`,
            badgeType: isMonisha ? 'success' : isMohana ? 'warning' : 'danger',
            icon: Activity,
          })}
          className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 transition cursor-pointer shadow-lg relative overflow-hidden group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px] group-hover:text-cyan-300 transition">Fraud Defense Ratio</span>
            <Activity className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
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
        <div
          onClick={() => setActiveModal({
            type: 'SHIELD',
            title: 'Account Security Posture & Shield Telemetry',
            subtitle: `Active multi-factor protection, registered hardware, and TreeSHAP explainability`,
            badge: security.security_posture || 'SECURE',
            badgeType: security.security_posture === 'SECURE' ? 'success' : 'warning',
            icon: ShieldCheck,
          })}
          className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/60 transition cursor-pointer shadow-lg relative overflow-hidden group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-[11px] group-hover:text-cyan-300 transition">Shield State</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
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
          <div className="text-[11px] text-slate-400 mt-1 font-mono flex items-center justify-between">
            <span>{security.trusted_devices_count || 1} Devices Registered</span>
            <span className="text-cyan-400 text-[10px] group-hover:underline">Inspect &rarr;</span>
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
            onClick={() => setActiveModal({
              type: 'CARD_CONTROLS',
              title: 'Virtual Debit Card Controls & Limits',
              subtitle: `Card Number: •••• •••• •••• ${data?.card_last4 || '4092'} • FraudLens Private Bank`,
              badge: isCardFrozen ? 'FROZEN' : 'ACTIVE',
              badgeType: isCardFrozen ? 'danger' : 'success',
              icon: CreditCard,
            })}
            className={`w-full aspect-[1.586/1] rounded-3xl p-5 sm:p-6 bg-gradient-to-tr ${theme.cardBg} border-2 ${theme.cardBorder} shadow-2xl relative flex flex-col justify-between overflow-hidden transition-transform duration-500 hover:scale-[1.02] cursor-pointer`}
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
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowCvv(!showCvv)
                    }}
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
            <button
              onClick={() => setActiveModal({
                type: 'CATEGORY',
                title: 'Spending Velocity by Merchant Category',
                subtitle: `Aggregated analysis across ${data?.total_transactions_count} completed purchases`,
                badge: `${categoryBreakdown.length} CATEGORIES`,
                badgeType: 'info',
                icon: ShoppingBag,
              })}
              className="text-[10px] font-mono text-cyan-400 hover:underline flex items-center gap-1"
            >
              <span>View Full Breakdown</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div
            onClick={() => setActiveModal({
              type: 'CATEGORY',
              title: 'Spending Velocity by Merchant Category',
              subtitle: `Aggregated analysis across ${data?.total_transactions_count} completed purchases`,
              badge: `${categoryBreakdown.length} CATEGORIES`,
              badgeType: 'info',
              icon: ShoppingBag,
            })}
            className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition cursor-pointer shadow-xl space-y-4"
          >
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
                      <tr
                        key={tx.id || tx.transaction_id}
                        onClick={() => setActiveModal({
                          type: 'TX_INSPECT_MODAL',
                          title: `Transaction ${tx.transaction_id}`,
                          subtitle: `Merchant: ${tx.merchant_name || tx.merchant_category} • Amount: ${formatInr(tx.amount)}`,
                          badge: isApproved ? 'APPROVED' : isMed ? 'CHALLENGE REQUIRED' : 'BLOCKED',
                          badgeType: isApproved ? 'success' : isMed ? 'warning' : 'danger',
                          icon: CreditCard,
                          data: tx,
                        })}
                        className="hover:bg-slate-800/40 transition cursor-pointer"
                      >
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
                        <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
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
          approvalId={activeApproval.approval_id}
          onApprove={handleApproveChallenge}
          onReject={handleRejectChallenge}
          customerName={data?.name || customerPersona.customerName || customerPersona.name}
          customerPhone={customerPersona?.phone}
          maskedCustomerPhone={customerPersona?.maskedPhone}
          customerPersona={customerPersona}
          transaction={{
            transaction_id: activeApproval.transaction_id,
            amount: activeApproval.amount,
            merchant_name: activeApproval.merchant_category,
            risk_level: activeApproval.risk_level,
            risk_score: activeApproval.risk_score,
            otp_code: activeApproval.otp_code,
            location: data?.primary_location || 'Salem, IN',
            device_type: data?.primary_device || 'Android Mobile',
          }}
        />
      )}

      {/* GLOBAL VIEWPORT-EXACT CENTERED MODAL SYSTEM */}
      {activeModal && (
        <GlobalCenterModal
          isOpen={Boolean(activeModal)}
          onClose={() => setActiveModal(null)}
          title={activeModal.title}
          subtitle={activeModal.subtitle}
          badge={activeModal.badge}
          badgeType={activeModal.badgeType}
          icon={activeModal.icon}
          maxWidth={activeModal.type === 'TX_INSPECT_MODAL' ? 'max-w-2xl' : 'max-w-3xl'}
        >
          {activeModal.type === 'BALANCE' && (
            <div className="space-y-4">
              <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/80 via-slate-900 to-teal-950/80 border border-emerald-500/60 shadow-xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-emerald-400 uppercase font-mono font-bold block">
                    Available Balance
                  </span>
                  <span className="text-3xl font-black text-emerald-300 font-mono">
                    {formatInr(data?.account_balance)}
                  </span>
                  <div className="text-xs text-slate-400 mt-1">
                    Primary Checking Account • Currency: INR (₹ Indian Rupee)
                  </div>
                </div>
                <DollarSign className="w-10 h-10 text-emerald-400 opacity-50" />
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-2">
                <h4 className="font-bold text-white uppercase text-[11px] font-mono flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Pre-Auth Protection Active
                </h4>
                <p className="text-slate-400 leading-relaxed text-[11px]">
                  Every transaction is pre-scored by the FraudLens AI engine before settlement, preventing unauthorized debits and chargeback disputes.
                </p>
              </div>
            </div>
          )}

          {activeModal.type === 'VOLUME' && (
            <div className="space-y-4">
              <div className="p-5 rounded-2xl bg-gradient-to-r from-cyan-950/80 via-slate-900 to-indigo-950/80 border border-cyan-500/60 shadow-xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-cyan-400 uppercase font-mono font-bold block">
                    Cumulative Spent Volume
                  </span>
                  <span className="text-3xl font-black text-cyan-300 font-mono">
                    {formatInr(data?.total_spent_amount)}
                  </span>
                  <div className="text-xs text-slate-400 mt-1">
                    Calculated across {data?.total_transactions_count?.toLocaleString()} completed transactions
                  </div>
                </div>
                <TrendingUp className="w-10 h-10 text-cyan-400 opacity-60" />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 text-[10px] uppercase block">Total Purchases</span>
                  <strong className="text-white text-sm">{data?.total_transactions_count?.toLocaleString()}</strong>
                </div>
                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 text-[10px] uppercase block">Average Ticket</span>
                  <strong className="text-cyan-300 text-sm">
                    {formatInr((data?.total_spent_amount || 0) / Math.max(1, data?.total_transactions_count || 1))}
                  </strong>
                </div>
                <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 text-[10px] uppercase block">Profile Baseline</span>
                  <strong className="text-purple-300 text-sm">{theme.tag}</strong>
                </div>
              </div>
            </div>
          )}

          {activeModal.type === 'FRAUD_RATIO' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center font-mono">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">AI Fraud Incidence</div>
                  <div className="text-2xl font-bold text-white mt-1">{data?.fraud_rate_percentage?.toFixed(1)}%</div>
                </div>
                <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/80">
                  <div className="text-[10px] text-emerald-400 uppercase">Clean Transactions</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">{security.clean_transactions_count || 0}</div>
                </div>
                <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/80">
                  <div className="text-[10px] text-rose-400 uppercase">Isolated / Blocked</div>
                  <div className="text-2xl font-bold text-rose-400 mt-1">{security.blocked_transactions_count || 0}</div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-2">
                <h4 className="font-bold text-white uppercase text-[11px] font-mono flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-purple-400" />
                  XGBoost &amp; TreeSHAP Real-Time Defense
                </h4>
                <p className="text-slate-400 leading-relaxed text-[11px]">
                  All pre-authorization requests are evaluated against behavioral velocity baselines and TreeSHAP mathematical explanations. Clean habitual payments proceed instantaneously, while high-risk anomalies are isolated or step-up challenged.
                </p>
              </div>
            </div>
          )}

          {activeModal.type === 'SHIELD' && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-slate-950 border border-cyan-500/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-bold text-white text-sm">Security Health State: {security.security_posture || 'SECURE'}</h4>
                    <p className="text-xs text-slate-400">Multi-factor AI protection &amp; biometric attestation active</p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-700 text-xs font-mono font-bold">
                  ACTIVE 24/7
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase block">Trusted Hardware Devices</span>
                  <span className="font-bold text-white text-sm">{security.trusted_devices_count || 1} Device(s)</span>
                </div>
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase block">Account Tenure</span>
                  <span className="font-bold text-cyan-300 text-sm">{data?.account_age_days || 30} Days</span>
                </div>
              </div>
            </div>
          )}

          {activeModal.type === 'CARD_CONTROLS' && (
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300 flex items-center gap-2">
                    {isCardFrozen ? <Lock className="w-4 h-4 text-rose-400" /> : <Unlock className="w-4 h-4 text-emerald-400" />}
                    <strong>Card Lock Status: {isCardFrozen ? 'FROZEN' : 'ACTIVE'}</strong>
                  </span>
                  <button
                    onClick={() => setIsCardFrozen(!isCardFrozen)}
                    className={`px-3 py-1.5 rounded-xl font-bold font-mono transition ${
                      isCardFrozen
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-slate-800 text-slate-300 hover:text-white border border-slate-700'
                    }`}
                  >
                    {isCardFrozen ? 'Unfreeze Card' : 'Freeze Card'}
                  </button>
                </div>

                <div className="flex items-center justify-between border-t border-slate-800 pt-3">
                  <span className="text-slate-300 flex items-center gap-2">
                    <GlobeIcon className="w-4 h-4 text-cyan-400" />
                    <strong>International Transactions: {intlEnabled ? 'ALLOWED' : 'BLOCKED'}</strong>
                  </span>
                  <button
                    onClick={() => setIntlEnabled(!intlEnabled)}
                    className={`px-3 py-1.5 rounded-xl font-bold font-mono transition ${
                      intlEnabled
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    {intlEnabled ? 'ACTIVE' : 'BLOCKED'}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase block">Daily Transaction Limit</span>
                  <span className="font-bold text-white text-sm">₹5,00,000.00</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase block">Online POS Mode</span>
                  <span className="font-bold text-emerald-400 text-sm">3D-Secure 2.2</span>
                </div>
              </div>
            </div>
          )}

          {activeModal.type === 'CATEGORY' && (
            <div className="space-y-4 text-xs">
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {categoryBreakdown.map((cat, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-cyan-400" />
                        {cat.category}
                      </span>
                      <div className="flex items-center gap-3 font-mono">
                        <span className="text-slate-400">{cat.count} txs</span>
                        <span className="font-bold text-cyan-300">{formatInr(cat.total_spent)}</span>
                        <span className="text-slate-500 font-bold">{cat.percentage}%</span>
                      </div>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-600 transition-all duration-700"
                        style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeModal.type === 'TX_INSPECT_MODAL' && activeModal.data && (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-mono block">Transaction ID</span>
                  <span className="font-mono font-bold text-cyan-400">{activeModal.data.transaction_id}</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-mono block">Beneficiary / Merchant</span>
                  <span className="font-bold text-white">{activeModal.data.merchant_name || activeModal.data.merchant_category}</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-mono block">Amount</span>
                  <span className="font-mono font-bold text-white">{formatInr(activeModal.data.amount)}</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-mono block">Category</span>
                  <span className="capitalize text-slate-300">{activeModal.data.merchant_category}</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-mono block">AI Risk Score</span>
                  <span className="font-mono font-bold text-cyan-400">
                    {Math.round(activeModal.data.risk_score || (activeModal.data.fraud_probability * 100) || 0)} / 100
                  </span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-mono block">Decision</span>
                  <span className="font-bold text-emerald-400">{activeModal.data.decision || 'APPROVED'}</span>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  onClick={() => {
                    const txId = activeModal.data.transaction_id
                    setActiveModal(null)
                    onSelectTransaction && onSelectTransaction(txId)
                  }}
                  className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-1.5 transition active:scale-95"
                >
                  <Sparkles className="w-3.5 h-3.5" /> Inspect Full TreeSHAP Explanation &rarr;
                </button>
              </div>
            </div>
          )}
        </GlobalCenterModal>
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
