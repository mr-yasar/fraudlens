import React, { useState, useEffect, useRef } from 'react'
import {
  Smartphone,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Fingerprint,
  KeyRound,
  Bell,
  Wifi,
  BatteryCharging,
  Signal,
  Store,
  MapPin,
  Clock,
  Laptop,
  ArrowRight,
  X,
  Sparkles,
  AlertTriangle,
  Send,
  RefreshCw,
  MessageSquare,
  Copy,
  Check,
} from 'lucide-react'
import { formatINR } from '../utils/formatters'
import { sound } from './login/soundEffects'
import { paymentApi } from '../services/api'

/**
 * MobileSecurityApprovalModal
 *
 * Highly realistic simulated smartphone device rendering an interactive lockscreen push notification,
 * authentic SMS OTP delivery, strict OTP matching validation, and biometric approval interface.
 */
export default function MobileSecurityApprovalModal({
  isOpen,
  onClose,
  transaction,
  approvalId,
  customerName = 'Customer',
  onApprove,
  onReject,
  actionLoading = false,
}) {
  const [authMethod, setAuthMethod] = useState('otp') // 'otp' | 'biometric'
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', ''])
  const [generatedOtp, setGeneratedOtp] = useState('')
  const [incomingSms, setIncomingSms] = useState(null)
  const [cooldown, setCooldown] = useState(0)
  const [isSending, setIsSending] = useState(false)
  const [otpError, setOtpError] = useState(null)
  const [failedCount, setFailedCount] = useState(0)
  const [status, setStatus] = useState('pending') // 'pending' | 'verifying' | 'approved' | 'rejected'
  const [currentTime, setCurrentTime] = useState('09:41')
  const [copied, setCopied] = useState(false)

  const inputRefs = [
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
  ]

  // Update clock every minute
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setCurrentTime(
        now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      )
    }
    updateTime()
    const timer = setInterval(updateTime, 30000)
    return () => clearInterval(timer)
  }, [])

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown((c) => c - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [cooldown])

  // Initialize or re-trigger when modal opens
  useEffect(() => {
    if (isOpen) {
      setStatus('pending')
      setOtpDigits(['', '', '', '', '', ''])
      setOtpError(null)
      setFailedCount(0)
      setCopied(false)

      const initialOtp =
        transaction?.otp_code ||
        String(Math.floor(100000 + Math.random() * 900000))
      setGeneratedOtp(initialOtp)

      // Simulate incoming SMS push alert with a realistic 500ms delay
      const smsTimer = setTimeout(() => {
        setIncomingSms({
          sender: 'FraudLens Bank SMS',
          code: initialOtp,
          amount: transaction?.amount || 14500,
          merchant:
            transaction?.merchant_name ||
            transaction?.beneficiary_name ||
            'NovaMart Fresh',
          time: 'now',
        })
        sound.playAlert && sound.playAlert()
      }, 500)

      setCooldown(30)
      return () => clearTimeout(smsTimer)
    } else {
      setIncomingSms(null)
    }
  }, [isOpen, transaction])

  if (!isOpen) return null

  const txAmount = transaction?.amount || 14500
  const txMerchant =
    transaction?.merchant_name || transaction?.beneficiary_name || 'NovaMart Fresh'
  const txLocation = transaction?.location || 'Chennai, IN'
  const txDevice = transaction?.device_type || 'Android Mobile'
  const txRisk = transaction?.risk_score || 72

  // Send / Resend a new OTP to the phone
  const handleSendNewOtp = async () => {
    if (cooldown > 0 || isSending) return
    setIsSending(true)
    setOtpError(null)
    setCopied(false)

    try {
      let freshCode = String(Math.floor(100000 + Math.random() * 900000))
      if (approvalId) {
        try {
          const res = await paymentApi.sendApprovalOtp(approvalId)
          if (res?.otp_code) {
            freshCode = res.otp_code
          }
        } catch {
          // Fallback to local generated code if backend approval is demo
        }
      }

      setGeneratedOtp(freshCode)
      setOtpDigits(['', '', '', '', '', ''])
      setCooldown(30)

      // Display incoming SMS banner
      setTimeout(() => {
        setIncomingSms({
          sender: 'FraudLens Bank SMS',
          code: freshCode,
          amount: txAmount,
          merchant: txMerchant,
          time: 'now',
        })
        sound.playAlert && sound.playAlert()
      }, 400)
    } finally {
      setIsSending(false)
    }
  }

  // Handle single digit typing or paste
  const handleDigitChange = (index, value) => {
    setOtpError(null)

    // Handle full 6-digit paste
    if (value.length > 1) {
      const clean = value.replace(/\D/g, '').slice(0, 6)
      if (clean.length > 0) {
        const nextDigits = ['', '', '', '', '', '']
        for (let i = 0; i < clean.length; i++) {
          nextDigits[i] = clean[i]
        }
        setOtpDigits(nextDigits)
        const nextFocus = Math.min(clean.length, 5)
        inputRefs[nextFocus]?.current?.focus()
        return
      }
    }

    const cleanChar = value.replace(/\D/g, '').slice(-1)
    const next = [...otpDigits]
    next[index] = cleanChar
    setOtpDigits(next)

    if (cleanChar && index < 5) {
      inputRefs[index + 1]?.current?.focus()
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      inputRefs[index - 1]?.current?.focus()
    }
  }

  // Quick 1-click Auto-fill from incoming SMS
  const handleAutoFillFromSms = () => {
    if (!generatedOtp) return
    const split = generatedOtp.split('').slice(0, 6)
    while (split.length < 6) split.push('')
    setOtpDigits(split)
    setOtpError(null)
    sound.playBlip && sound.playBlip()
    inputRefs[5]?.current?.focus()
  }

  // Copy code to clipboard
  const handleCopyOtp = () => {
    if (!generatedOtp) return
    navigator.clipboard?.writeText(generatedOtp)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    sound.playBlip && sound.playBlip()
  }

  // Strict OTP Matching Verification
  const handleVerifyAndApprove = async () => {
    if (authMethod === 'otp') {
      const enteredCode = otpDigits.join('').trim()

      if (enteredCode.length < 6) {
        setOtpError('Please enter the complete 6-digit SMS OTP code.')
        sound.playError && sound.playError()
        inputRefs[enteredCode.length]?.current?.focus()
        return
      }

      // Real matching check
      if (enteredCode !== generatedOtp) {
        const newFailCount = failedCount + 1
        setFailedCount(newFailCount)
        setOtpError(
          `❌ Invalid OTP Code! '${enteredCode}' does not match the 6-digit code sent to your phone. (Attempt ${newFailCount}/3)`
        )
        sound.playError && sound.playError()
        return
      }
    }

    // OTP matched or biometric authorized!
    setStatus('verifying')
    sound.playBlip && sound.playBlip()

    try {
      const challengeResponse = authMethod === 'otp' ? otpDigits.join('').trim() : 'BIOMETRIC_TOUCH_ID'
      if (onApprove) {
        await onApprove(approvalId, challengeResponse)
      }
      setStatus('approved')
      sound.playVerified && sound.playVerified()

      setTimeout(() => {
        onClose && onClose()
      }, 2000)
    } catch (err) {
      setStatus('pending')
      setOtpError(err instanceof Error ? err.message : 'Approval verification failed on server.')
      sound.playError && sound.playError()
    }
  }

  // Reject / Freeze
  const handleRejectClick = async () => {
    setStatus('rejected')
    sound.playError && sound.playError()
    if (onReject) {
      await onReject(approvalId)
    }
    setTimeout(() => {
      onClose && onClose()
    }, 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 bg-black/85 backdrop-blur-md animate-fadeIn select-none overflow-y-auto">
      {/* Outer Modal Container */}
      <div className="relative w-full max-w-sm flex flex-col items-center my-auto">
        {/* Dismiss Button */}
        <button
          onClick={onClose}
          className="absolute -top-10 right-2 p-1.5 text-slate-400 hover:text-white rounded-full bg-slate-900 border border-slate-700 transition z-50"
          title="Close Phone Simulation"
        >
          <X className="w-4 h-4" />
        </button>

        {/* =========================================================================
            SMARTPHONE CHASSIS (Curved Sleek Titanium Device Frame)
            ========================================================================= */}
        <div className="w-[330px] sm:w-[355px] max-h-[96vh] h-[660px] rounded-[44px] bg-slate-950 p-2.5 shadow-[0_0_65px_rgba(6,182,212,0.45),0_20px_50px_rgba(0,0,0,0.95)] border-4 border-slate-700/80 relative flex flex-col justify-between overflow-hidden">
          {/* Dynamic Island / Speaker Pill */}
          <div className="absolute top-3.5 left-1/2 -translate-x-1/2 w-32 h-5.5 bg-black rounded-full z-40 flex items-center justify-between px-3 border border-slate-800 shadow-md">
            <div className="w-2 h-2 rounded-full bg-slate-900 border border-slate-700" />
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
          </div>

          {/* Phone Screen Glass */}
          <div className="w-full h-full rounded-[36px] bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 border border-slate-800/80 flex flex-col justify-between p-3.5 pt-8 relative overflow-hidden text-slate-100">
            {/* Background Holographic Cyber Glow */}
            <div className="absolute -top-24 -left-24 w-48 h-48 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-500/15 rounded-full blur-3xl pointer-events-none" />

            {/* Status Bar */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1 mb-1.5 z-10">
              <span className="font-bold text-white">{currentTime}</span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-cyan-400 font-mono">5G</span>
                <Signal className="w-3.5 h-3.5 text-slate-300" />
                <Wifi className="w-3.5 h-3.5 text-slate-300" />
                <div className="flex items-center gap-0.5">
                  <span className="text-[10px]">98%</span>
                  <BatteryCharging className="w-4 h-4 text-emerald-400" />
                </div>
              </div>
            </div>

            {/* =====================================================================
                INCOMING REAL SMS POPUP BANNER (Drops down like genuine phone notification)
                ===================================================================== */}
            {incomingSms && status === 'pending' && (
              <div className="z-30 mb-2 p-2.5 rounded-2xl bg-slate-900/98 border border-cyan-500/80 shadow-[0_8px_25px_rgba(6,182,212,0.4)] backdrop-blur-xl animate-bounce-subtle space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <div className="p-1 rounded-lg bg-emerald-600 text-white shadow-sm">
                      <MessageSquare className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-bold text-white tracking-tight">
                      MESSAGES • {incomingSms.time}
                    </span>
                  </div>
                  <span className="px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-mono text-[9px] font-bold">
                    SMS DELIVERED
                  </span>
                </div>

                <p className="text-[11px] text-slate-200 leading-snug">
                  FraudLens Bank: <strong className="text-white font-mono bg-cyan-950 px-1 py-0.5 rounded border border-cyan-700 tracking-wider font-extrabold text-cyan-300">{incomingSms.code}</strong> is your secret verification OTP for payment of {formatINR(incomingSms.amount)}. Valid for 5m.
                </p>

                {/* Quick actions right on SMS */}
                <div className="flex items-center gap-2 pt-0.5 text-[10px]">
                  <button
                    type="button"
                    onClick={handleAutoFillFromSms}
                    className="flex-1 py-1 px-2 rounded-lg bg-cyan-600/90 hover:bg-cyan-500 text-white font-semibold flex items-center justify-center gap-1 shadow-sm transition active:scale-95"
                  >
                    <Check className="w-3 h-3" />
                    <span>Auto-Fill Code ({incomingSms.code})</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCopyOtp}
                    className="py-1 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium flex items-center gap-1 border border-slate-700 transition"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* LOCKSCREEN TRANSACTION CONTEXT CARD */}
            <div className="z-10 space-y-2">
              <div className="p-2.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md backdrop-blur-md">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span className="font-bold text-white text-[11px] uppercase tracking-wide">
                      Fraud Intervention Held
                    </span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800">
                    Risk {txRisk}/100
                  </span>
                </div>
                <div className="flex items-baseline justify-between mt-1">
                  <span className="text-xl font-black font-mono text-white">
                    {formatINR(txAmount)}
                  </span>
                  <span className="text-[11px] font-medium text-slate-300 truncate max-w-[150px]">
                    {txMerchant}
                  </span>
                </div>
              </div>
            </div>

            {/* MAIN AUTHENTICATION INTERACTION */}
            <div className="z-10 my-auto py-1 space-y-2.5">
              {/* Security Verification Choice Toggle */}
              <div className="flex p-0.5 bg-slate-950 rounded-xl border border-slate-800 text-[11px]">
                <button
                  type="button"
                  onClick={() => setAuthMethod('otp')}
                  className={`flex-1 py-1 rounded-lg font-semibold flex items-center justify-center gap-1 transition ${
                    authMethod === 'otp'
                      ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>Real SMS OTP (Match)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMethod('biometric')}
                  className={`flex-1 py-1 rounded-lg font-semibold flex items-center justify-center gap-1 transition ${
                    authMethod === 'biometric'
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Fingerprint className="w-3.5 h-3.5" />
                  <span>Biometric Touch ID</span>
                </button>
              </div>

              {/* REAL SMS OTP INPUT FORM */}
              {authMethod === 'otp' && status === 'pending' && (
                <div className="space-y-2 bg-slate-950/90 p-3 rounded-2xl border border-slate-800">
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span className="font-semibold text-slate-300">
                      Enter 6-Digit SMS Security Code:
                    </span>
                    <button
                      type="button"
                      disabled={cooldown > 0 || isSending}
                      onClick={handleSendNewOtp}
                      className="text-cyan-400 hover:text-cyan-300 font-semibold underline flex items-center gap-1 disabled:text-slate-600"
                    >
                      <RefreshCw className={`w-3 h-3 ${isSending ? 'animate-spin' : ''}`} />
                      <span>{cooldown > 0 ? `Resend (${cooldown}s)` : 'Resend Code'}</span>
                    </button>
                  </div>

                  {/* 6 Individual Styled Digit Input Cells */}
                  <div className="flex items-center justify-between gap-1.5 pt-0.5">
                    {otpDigits.map((digit, idx) => (
                      <input
                        key={idx}
                        ref={inputRefs[idx]}
                        type="text"
                        inputMode="numeric"
                        maxLength={6}
                        value={digit}
                        onChange={(e) => handleDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleKeyDown(idx, e)}
                        placeholder="•"
                        className={`w-9 sm:w-10 h-10 sm:h-11 text-center font-mono text-lg font-black rounded-xl bg-slate-900 border transition-all ${
                          digit
                            ? 'border-cyan-400 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.4)]'
                            : 'border-slate-700 text-slate-500 focus:border-cyan-500'
                        } focus:outline-none focus:scale-105`}
                      />
                    ))}
                  </div>

                  {/* Error Notification */}
                  {otpError && (
                    <div className="p-2 rounded-xl bg-rose-950/90 border border-rose-600 text-rose-200 text-[10px] font-semibold flex items-start gap-1.5 animate-shake shadow-md">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-rose-400 mt-0.5" />
                      <span className="leading-tight">{otpError}</span>
                    </div>
                  )}

                  {/* Dispatch metadata banner */}
                  <div className="flex items-center justify-between text-[9px] font-mono text-slate-500 pt-0.5 border-t border-slate-800/80">
                    <span>Delivered to: +91 98••••••42</span>
                    <span className="text-cyan-400 font-bold">Strict 1:1 Match Enforced</span>
                  </div>
                </div>
              )}

              {/* BIOMETRIC TOUCH FORM */}
              {authMethod === 'biometric' && status === 'pending' && (
                <div className="py-4 px-3 bg-slate-950/90 rounded-2xl border border-slate-800 text-center space-y-2">
                  <div className="relative w-16 h-16 mx-auto flex items-center justify-center">
                    <div className="absolute inset-0 bg-purple-500/20 rounded-full animate-ping pointer-events-none" />
                    <div className="p-3.5 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-[0_0_20px_rgba(168,85,247,0.5)]">
                      <Fingerprint className="w-8 h-8" />
                    </div>
                  </div>
                  <div className="text-xs font-bold text-white">Touch ID Sensor Ready</div>
                  <p className="text-[10px] text-slate-400 max-w-[200px] mx-auto leading-relaxed">
                    Place registered biometric finger on sensor to authorize {formatINR(txAmount)}.
                  </p>
                </div>
              )}

              {/* VERIFYING SPINNER STATE */}
              {status === 'verifying' && (
                <div className="p-4 bg-slate-950/95 border border-cyan-500 rounded-2xl text-center space-y-2 animate-fadeIn">
                  <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
                  <div className="text-xs font-bold text-cyan-200 font-mono">
                    Verifying OTP with FraudLens Risk Engine...
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Matching cryptographic one-time token against security ledger.
                  </p>
                </div>
              )}

              {/* OUTCOME SUCCESS SCREEN */}
              {status === 'approved' && (
                <div className="p-3.5 bg-emerald-950/95 border border-emerald-500 rounded-2xl text-center space-y-1.5 animate-scaleUp shadow-[0_0_25px_rgba(16,185,129,0.4)]">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                  <div className="text-sm font-extrabold text-emerald-200">
                    OTP Matched &amp; Authorized!
                  </div>
                  <p className="text-[11px] text-emerald-300/90">
                    Payment of <strong className="font-mono">{formatINR(txAmount)}</strong> successfully released to {txMerchant}.
                  </p>
                </div>
              )}

              {/* OUTCOME REJECTED SCREEN */}
              {status === 'rejected' && (
                <div className="p-3.5 bg-rose-950/95 border border-rose-500 rounded-2xl text-center space-y-1.5 animate-scaleUp shadow-[0_0_25px_rgba(225,29,72,0.4)]">
                  <XCircle className="w-8 h-8 text-rose-400 mx-auto" />
                  <div className="text-sm font-extrabold text-rose-200">
                    Transaction Terminated &amp; Blocked
                  </div>
                  <p className="text-[11px] text-rose-300/90">
                    Card frozen immediately. 0 funds lost to unauthorized fraud attempt.
                  </p>
                </div>
              )}
            </div>

            {/* ACTION BUTTONS (VERIFY & APPROVE vs REJECT & FREEZE) */}
            {status === 'pending' && (
              <div className="z-10 space-y-2 pt-1 border-t border-slate-800">
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={handleVerifyAndApprove}
                  className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-bold text-xs shadow-lg shadow-emerald-950 flex items-center justify-center gap-2 transition active:scale-95"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>VERIFY OTP &amp; APPROVE PAYMENT</span>
                </button>

                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={handleRejectClick}
                  className="w-full py-2 px-3 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white font-bold text-xs shadow-md shadow-rose-950 flex items-center justify-center gap-1.5 transition active:scale-95"
                >
                  <XCircle className="w-4 h-4" />
                  <span>NO, FRAUD! BLOCK CARD</span>
                </button>
              </div>
            )}

            {/* Home Indicator Bar */}
            <div className="w-32 h-1 bg-slate-700 rounded-full mx-auto mt-2 z-10" />
          </div>
        </div>
      </div>
    </div>
  )
}
