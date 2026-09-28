import React, { useState, useEffect } from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  KeyRound,
  Clock,
  AlertTriangle,
  RotateCw,
  CheckCircle2,
  Lock,
  X,
  Sparkles,
} from 'lucide-react'
import { premiumApi } from '../../services/api'

export default function PremiumVerificationModal({
  isOpen,
  onClose,
  transaction,
  onVerificationSuccess,
}) {
  const [otpCode, setOtpCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [expiresIn, setExpiresIn] = useState(300) // 5 minutes
  const [resendCooldown, setResendCooldown] = useState(30)
  const [resending, setResending] = useState(false)
  const [demoCode, setDemoCode] = useState(transaction?.verification_challenge?.demo_otp || '')

  useEffect(() => {
    if (!isOpen || !transaction) return
    setOtpCode('')
    setError(null)
    setSuccessMsg(null)
    setExpiresIn(300)
    setResendCooldown(30)
    if (transaction?.verification_challenge?.demo_otp) {
      setDemoCode(transaction.verification_challenge.demo_otp)
    }
  }, [isOpen, transaction])

  // Countdown timer for expiration & cooldown
  useEffect(() => {
    if (!isOpen) return
    const timer = setInterval(() => {
      setExpiresIn((prev) => (prev > 0 ? prev - 1 : 0))
      setResendCooldown((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [isOpen])

  if (!isOpen || !transaction) return null

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const handleVerify = async (e) => {
    e?.preventDefault()
    if (!otpCode || otpCode.length < 6 || loading) return
    setLoading(true)
    setError(null)
    try {
      const res = await premiumApi.verifyOtp({
        transaction_id: transaction.transaction_id,
        otp_code: otpCode.trim(),
      })
      if (res.success) {
        setSuccessMsg(res.message || 'Verification authorized! Settlement complete.')
        setTimeout(() => {
          onVerificationSuccess && onVerificationSuccess(res)
          onClose()
        }, 1200)
      }
    } catch (err) {
      setError(err.message || 'Passcode verification failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0 || resending) return
    setResending(true)
    setError(null)
    try {
      const res = await premiumApi.requestOtp({
        transaction_id: transaction.transaction_id,
        amount: transaction.amount,
      })
      setExpiresIn(300)
      setResendCooldown(30)
      if (res.demo_otp) {
        setDemoCode(res.demo_otp)
      }
      setSuccessMsg('New security challenge code dispatched.')
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (err) {
      setError(err.message || 'Failed to request new code.')
    } finally {
      setResending(false)
    }
  }

  const handleAutoFill = () => {
    if (demoCode) {
      setOtpCode(demoCode)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg rounded-3xl bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 border-2 border-indigo-500/60 shadow-[0_0_50px_rgba(99,102,241,0.4)] p-6 sm:p-7 overflow-hidden text-slate-100">
        {/* Top Glow Accent */}
        <div className="absolute top-0 left-1/4 right-1/4 h-[2px] bg-gradient-to-r from-transparent via-indigo-400 to-transparent" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Badge */}
        <div className="flex items-center gap-3 mb-5">
          <div className="p-3 rounded-2xl bg-indigo-950/90 border border-indigo-500/60 text-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.5)]">
            <KeyRound className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-black tracking-tight text-white font-mono">
                STEP-UP CHALLENGE
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-600/70 font-bold">
                {transaction.risk_level} RISK
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Server-side cryptographic verification required to authorize transaction.
            </p>
          </div>
        </div>

        {/* Transaction Summary Card */}
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 mb-4 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono">Transaction ID</span>
            <span className="font-mono font-bold text-cyan-400">{transaction.transaction_id}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono">Amount</span>
            <span className="font-mono font-black text-white text-base">
              ₹{Number(transaction.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono">Recipient</span>
            <span className="font-mono text-indigo-300 font-semibold">{transaction.recipient}</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/60">
            <span className="text-slate-400 font-mono">Adaptive Risk Score</span>
            <span className="font-mono font-bold text-amber-400">
              {transaction.risk_score} / 100
            </span>
          </div>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-600 text-rose-200 text-xs flex items-center gap-2 mb-4 animate-shake">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-600 text-emerald-200 text-xs flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span className="font-medium">{successMsg}</span>
          </div>
        )}

        {/* OTP Input Form */}
        <form onSubmit={handleVerify} className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300 font-mono">
                ENTER 6-DIGIT PASSCODE
              </label>
              <div className="flex items-center gap-1.5 text-xs text-amber-400 font-mono">
                <Clock className="w-3.5 h-3.5" />
                <span>Expires in: {formatTime(expiresIn)}</span>
              </div>
            </div>

            <div className="relative">
              <input
                type="text"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                placeholder="• • • • • •"
                autoFocus
                className="w-full text-center tracking-[0.6em] font-mono text-2xl font-black py-3 px-4 rounded-2xl bg-slate-900 border-2 border-slate-700 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 text-white placeholder:text-slate-600 outline-none transition"
              />
            </div>
          </div>

          {/* Quick 1-Click Auto-Fill Helper for Demo Scenarios */}
          {demoCode && (
            <div className="p-2.5 rounded-xl bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span className="text-slate-300 font-mono">
                  Sandbox Security Code: <strong className="text-indigo-300 font-bold">{demoCode}</strong>
                </span>
              </div>
              <button
                type="button"
                onClick={handleAutoFill}
                className="px-2.5 py-1 rounded-lg bg-indigo-900/90 hover:bg-indigo-800 text-indigo-200 border border-indigo-500/60 font-mono text-[11px] font-bold transition"
              >
                Auto-Fill
              </button>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={handleResend}
              disabled={resendCooldown > 0 || resending}
              className="flex-1 py-2.5 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 disabled:opacity-40 text-slate-300 hover:text-white text-xs font-mono font-semibold flex items-center justify-center gap-2 transition"
            >
              <RotateCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
              <span>
                {resendCooldown > 0 ? `Resend (${resendCooldown}s)` : 'Resend Code'}
              </span>
            </button>

            <button
              type="submit"
              disabled={otpCode.length < 6 || loading || expiresIn === 0}
              className="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-40 text-white text-xs font-mono font-bold uppercase tracking-wider shadow-[0_0_25px_rgba(99,102,241,0.5)] flex items-center justify-center gap-2 transition"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Authorize Transfer</span>
                </>
              )}
            </button>
          </div>
        </form>

        <div className="mt-4 text-center text-[10px] text-slate-500 font-mono">
          Strict Cryptographic Salted SHA-256 Validation • Max 3 Attempts • Hardware Session Locked
        </div>
      </div>
    </div>
  )
}
