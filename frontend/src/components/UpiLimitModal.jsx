import React from 'react'
import {
  ShieldAlert,
  CreditCard,
  X,
  Clock,
  ArrowRight,
  AlertTriangle,
  Info,
  CheckCircle2,
  Lock,
} from 'lucide-react'
import GlobalCenterModal from './common/GlobalCenterModal'
import { formatINR } from '../utils/formatters'

/**
 * Premium UPI Daily Limit Reached Modal & Card-Only Fallback
 * 
 * Enforces project-configured business rules:
 * - Overall UPI daily limit: ₹5,00,000 per user/account.
 * - UPI merchant daily limit: ₹1,49,000 per user/account.
 * - Displays exact prompt titles, messages, stats, reset time, and Card Fallback action.
 */
export default function UpiLimitModal({
  isOpen,
  onClose,
  violation,
  onPayByCard,
}) {
  if (!isOpen || !violation) return null

  const isMerchant = violation.limit_type === 'MERCHANT'
  const limitTitle = isMerchant ? 'Merchant UPI Limit Reached' : 'Daily UPI Limit Reached'
  const applicableLimit = violation.applicable_limit || (isMerchant ? 149000 : 500000)
  const amountUsed = violation.amount_used || 0
  const remainingAmount = Math.max(0, violation.remaining_amount || (applicableLimit - amountUsed))
  const requestedAmount = violation.requested_amount || 0
  const resetTimeStr = violation.reset_time_human || violation.reset_time || 'Next 24h rolling cycle'

  const usedPercentage = Math.min(100, Math.round((amountUsed / applicableLimit) * 100))

  return (
    <GlobalCenterModal
      isOpen={isOpen}
      onClose={onClose}
      title={limitTitle}
      subtitle="Application Daily UPI Limit Protection"
      icon={AlertTriangle}
      badge={isMerchant ? 'MERCHANT UPI LIMIT: ₹1,49,000' : 'OVERALL UPI LIMIT: ₹5,00,000'}
      badgeType="danger"
      maxWidth="max-w-xl"
      footer={
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 w-full">
          <button
            type="button"
            onClick={onClose}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-bold transition font-mono"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onPayByCard}
            className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-xs font-bold shadow-lg shadow-indigo-950/60 transition flex items-center justify-center gap-2 uppercase tracking-wider"
          >
            <CreditCard className="w-4 h-4" />
            <span>Pay by Card &rarr;</span>
          </button>
        </div>
      }
    >
      <div className="space-y-4 text-slate-200">
        {/* Exact Required Prompt Message Banner */}
        <div className="p-4 rounded-xl bg-rose-950/70 border border-rose-700/70 shadow-lg space-y-2">
          <div className="flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="space-y-1.5">
              <h4 className="text-sm font-bold text-white">
                {limitTitle}
              </h4>
              {isMerchant ? (
                <p className="text-xs text-rose-200 leading-relaxed">
                  Your daily merchant UPI limit of <strong>₹1,49,000</strong> has been reached.
                  <br />
                  <span className="text-slate-300">
                    Please use Card Payment to continue with this merchant transaction.
                  </span>
                </p>
              ) : (
                <p className="text-xs text-rose-200 leading-relaxed">
                  You have reached your daily UPI payment limit of <strong>₹5,00,000</strong>.
                  <br />
                  <span className="text-slate-300">
                    UPI payments are unavailable for the remainder of the applicable limit period. To continue with this transaction, please select Card Payment.
                  </span>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Limit Breakdown Stats Grid */}
        <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 space-y-3">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
            <span>Daily Accounting Usage Breakdown (Rolling 24 Hours)</span>
            <span className="text-rose-400 font-bold">{usedPercentage}% Used</span>
          </div>

          <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                usedPercentage >= 100
                  ? 'bg-rose-500'
                  : usedPercentage >= 80
                  ? 'bg-amber-500'
                  : 'bg-cyan-500'
              }`}
              style={{ width: `${Math.max(5, usedPercentage)}%` }}
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-mono">Applicable Limit</div>
              <div className="text-xs font-bold text-white font-mono mt-0.5">
                {formatINR(applicableLimit)}
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-mono">Amount Used</div>
              <div className="text-xs font-bold text-rose-400 font-mono mt-0.5">
                {formatINR(amountUsed)}
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-mono">Remaining Limit</div>
              <div className="text-xs font-bold text-emerald-400 font-mono mt-0.5">
                {formatINR(remainingAmount)}
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-mono">Requested</div>
              <div className="text-xs font-bold text-cyan-300 font-mono mt-0.5">
                {formatINR(requestedAmount)}
              </div>
            </div>
          </div>

          {/* Reset Time Indicator */}
          <div className="flex items-center justify-between text-xs font-mono pt-1 text-slate-400 border-t border-slate-900">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span>Limit Reset Time:</span>
            </div>
            <span className="text-white font-bold">{resetTimeStr}</span>
          </div>
        </div>

        {/* Card Payment Fallback Recommendation */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-indigo-950/60 border border-indigo-700/50 flex items-start gap-3 shadow-inner">
          <div className="w-9 h-9 rounded-lg bg-indigo-900/60 border border-indigo-500/40 flex items-center justify-center shrink-0 text-indigo-300 shadow">
            <CreditCard className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h5 className="text-xs font-bold text-indigo-200 uppercase tracking-wider">
                Card Payment Fallback Ready
              </h5>
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-indigo-900 text-indigo-300 border border-indigo-700">
                RECOMMENDED
              </span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Click <strong>Pay by Card</strong> to switch to card checkout. Your transfer amount of{' '}
              <strong className="text-cyan-300 font-mono">{formatINR(requestedAmount)}</strong> and recipient information will be preserved without creating duplicate transactions.
            </p>
          </div>
        </div>
      </div>
    </GlobalCenterModal>
  )
}
