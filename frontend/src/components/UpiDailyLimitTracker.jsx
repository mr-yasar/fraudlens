import React from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  CreditCard,
  Clock,
  RefreshCw,
  AlertTriangle,
  Zap,
  Info,
} from 'lucide-react'
import { formatINR } from '../utils/formatters'

/**
 * UpiDailyLimitTracker
 * 
 * Embeddable tracker widget displaying:
 * - Overall UPI daily limit: ₹5,00,000
 * - Merchant UPI daily limit: ₹1,49,000
 * - Real-time amounts used & remaining
 * - Progress indicators and limit status badges
 * - Reset time over rolling 24-hour accounting window
 * - Card Payment fallback prompt
 */
export default function UpiDailyLimitTracker({
  limits,
  loading,
  onRefresh,
  onSwitchToCard,
  currentPaymentMethod,
}) {
  if (!limits) return null

  const overallLimit = limits.overall_limit || 500000.0
  const overallUsed = limits.overall_used || 0.0
  const overallRemaining = Math.max(0, limits.overall_remaining ?? (overallLimit - overallUsed))
  const overallReached = limits.overall_limit_reached || overallUsed >= overallLimit
  const overallPercent = Math.min(100, Math.round((overallUsed / overallLimit) * 100))

  const merchantLimit = limits.merchant_limit || 149000.0
  const merchantUsed = limits.merchant_used || 0.0
  const merchantRemaining = Math.max(0, limits.merchant_remaining ?? (merchantLimit - merchantUsed))
  const merchantReached = limits.merchant_limit_reached || merchantUsed >= merchantLimit
  const merchantPercent = Math.min(100, Math.round((merchantUsed / merchantLimit) * 100))

  const isUpiActive = currentPaymentMethod === 'upi'

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4.5 shadow-xl backdrop-blur-md space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>UPI Daily Limits &amp; Tracking</span>
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                24H ROLLING WINDOW
              </span>
            </h3>
            <p className="text-[10px] text-slate-400">
              Reset Time: <span className="text-slate-200 font-mono font-medium">{limits.reset_time_human || 'Rolling 24h'}</span>
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-cyan-300 border border-slate-800 transition disabled:opacity-50"
          title="Refresh limits from database"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
        </button>
      </div>

      {/* 2-Column Limits Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* Card 1: Overall UPI Limit */}
        <div className={`p-3.5 rounded-xl border transition ${
          overallReached
            ? 'bg-rose-950/40 border-rose-800/80'
            : 'bg-slate-950/70 border-slate-800'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
              <span>Overall UPI Daily Limit</span>
            </span>
            <span
              className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                overallReached
                  ? 'bg-rose-900 text-rose-200 border-rose-700 animate-pulse'
                  : 'bg-emerald-950 text-emerald-300 border-emerald-800'
              }`}
            >
              {overallReached ? 'LIMIT REACHED' : 'ACTIVE'}
            </span>
          </div>

          <div className="flex items-baseline justify-between text-xs font-mono mb-1.5">
            <span className="text-slate-400">
              Used: <strong className={overallReached ? 'text-rose-400' : 'text-cyan-300'}>{formatINR(overallUsed)}</strong>
            </span>
            <span className="text-slate-400">
              Limit: <strong className="text-white">{formatINR(overallLimit)}</strong>
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800 mb-2">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                overallReached
                  ? 'bg-rose-500'
                  : overallPercent >= 80
                  ? 'bg-amber-500'
                  : 'bg-gradient-to-r from-cyan-500 to-blue-500'
              }`}
              style={{ width: `${Math.max(4, overallPercent)}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>Remaining: <strong className="text-emerald-400 font-bold">{formatINR(overallRemaining)}</strong></span>
            <span>{overallPercent}% Used</span>
          </div>
        </div>

        {/* Card 2: Merchant UPI Limit */}
        <div className={`p-3.5 rounded-xl border transition ${
          merchantReached
            ? 'bg-rose-950/40 border-rose-800/80'
            : 'bg-slate-950/70 border-slate-800'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
              <span>Merchant UPI Daily Limit</span>
            </span>
            <span
              className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                merchantReached
                  ? 'bg-rose-900 text-rose-200 border-rose-700 animate-pulse'
                  : 'bg-emerald-950 text-emerald-300 border-emerald-800'
              }`}
            >
              {merchantReached ? 'LIMIT REACHED' : 'ACTIVE'}
            </span>
          </div>

          <div className="flex items-baseline justify-between text-xs font-mono mb-1.5">
            <span className="text-slate-400">
              Used: <strong className={merchantReached ? 'text-rose-400' : 'text-cyan-300'}>{formatINR(merchantUsed)}</strong>
            </span>
            <span className="text-slate-400">
              Limit: <strong className="text-white">{formatINR(merchantLimit)}</strong>
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800 mb-2">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                merchantReached
                  ? 'bg-rose-500'
                  : merchantPercent >= 80
                  ? 'bg-amber-500'
                  : 'bg-gradient-to-r from-cyan-500 to-indigo-500'
              }`}
              style={{ width: `${Math.max(4, merchantPercent)}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>Remaining: <strong className="text-emerald-400 font-bold">{formatINR(merchantRemaining)}</strong></span>
            <span>{merchantPercent}% Used</span>
          </div>
        </div>
      </div>

      {/* Card Fallback Alert & Quick Action */}
      {(overallReached || merchantReached || !isUpiActive) && (
        <div className="p-3 rounded-xl bg-indigo-950/50 border border-indigo-700/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-indigo-400 shrink-0" />
            <div className="text-xs text-indigo-200">
              <span className="font-bold">Card Payment Available:</span>{' '}
              {overallReached || merchantReached
                ? 'UPI limit reached. Seamlessly switch to Card Payment.'
                : 'Card transactions are exempt from UPI daily limits.'}
            </div>
          </div>
          {isUpiActive && (
            <button
              type="button"
              onClick={onSwitchToCard}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition flex items-center justify-center gap-1.5 shrink-0 shadow cursor-pointer"
            >
              <span>Pay by Card</span>
              <span>&rarr;</span>
            </button>
          )}
        </div>
      )}
    </div>
  )
}
