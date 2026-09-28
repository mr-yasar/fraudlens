import React, { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import {
  Smartphone,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Fingerprint,
  KeyRound,
  Wifi,
  BatteryCharging,
  Signal,
  ArrowRight,
  X,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  MessageSquare,
  Copy,
  Check,
  Lock,
  Unlock,
  CreditCard,
  Building2,
  UserCheck,
} from 'lucide-react'
import { formatINR } from '../utils/formatters'
import { sound } from './login/soundEffects'
import { paymentApi } from '../services/api'

/**
 * MobileSecurityApprovalModal
 *
 * Peak Fintech Showcase: Embedded Apple-grade Secure Smartphone Interface.
 * Features realistic device proportions, titanium frame, Dynamic Island security pulse,
 * incoming SMS OTP banner with 1-click Auto-fill & Copy-Paste, strict OTP verification,
 * Security Hold multi-stage verification state, and explicit illuminated ALLOW / APPROVE flow.
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
  
  // Verification lifecycle states:
  // 'entering_otp' -> 'verifying_otp' -> 'otp_verified' -> 'processing_approval' -> 'completed' -> 'rejected'
  const [stage, setStage] = useState('entering_otp')
  const [currentTime, setCurrentTime] = useState('09:41')
  const [copied, setCopied] = useState(false)
  const [expiryCountdown, setExpiryCountdown] = useState(300) // 5 minutes

  const inputRefs = [
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
  ]

  // Background Scroll Lock
  useEffect(() => {
    if (!isOpen || typeof document === 'undefined') return

    const windowY = window.scrollY || window.pageYOffset || 0
    const originalBodyPadding = document.body.style.paddingRight
    const originalBodyOverflow = document.body.style.overflow
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth

    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`
    }
    document.body.style.overflow = 'hidden'

    return () => {
      document.body.style.overflow = originalBodyOverflow || ''
      document.body.style.paddingRight = originalBodyPadding || ''
      window.scrollTo(0, windowY)
    }
  }, [isOpen])

  // Device Clock
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

  // Cooldown countdown
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown((c) => c - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [cooldown])

  // 5-minute security expiry countdown
  useEffect(() => {
    if (isOpen && expiryCountdown > 0 && stage !== 'completed' && stage !== 'rejected') {
      const timer = setTimeout(() => setExpiryCountdown((c) => c - 1), 1000)
      return () => clearTimeout(timer)
    } else if (isOpen && expiryCountdown === 0 && stage !== 'completed' && stage !== 'rejected') {
      setStage('rejected')
      setOtpError('Security OTP token expired. Transaction cancelled.')
      sound.playError && sound.playError()
    }
  }, [isOpen, expiryCountdown, stage])

  // Modal Initialization
  useEffect(() => {
    if (isOpen) {
      setStage('entering_otp')
      setOtpDigits(['', '', '', '', '', ''])
      setOtpError(null)
      setFailedCount(0)
      setCopied(false)
      setExpiryCountdown(300)

      const initialOtp =
        transaction?.otp_code ||
        String(Math.floor(100000 + Math.random() * 900000))
      setGeneratedOtp(initialOtp)

      // Incoming SMS Push Banner after 400ms
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
      }, 400)

      setCooldown(30)
      setTimeout(() => inputRefs[0]?.current?.focus(), 300)
      return () => clearTimeout(smsTimer)
    } else {
      setIncomingSms(null)
    }
  }, [isOpen, transaction])

  if (!isOpen || typeof document === 'undefined') return null

  const txAmount = transaction?.amount || 14500
  const txMerchant =
    transaction?.merchant_name || transaction?.beneficiary_name || 'NovaMart Fresh'
  const txLocation = transaction?.location || 'Chennai, IN'
  const txRisk = transaction?.risk_score || 72
  const txLevel = transaction?.risk_level || (txRisk > 70 ? 'HIGH' : 'MEDIUM')

  // Request/Resend fresh OTP
  const handleSendNewOtp = async () => {
    if (cooldown > 0 || isSending) return
    setIsSending(true)
    setOtpError(null)
    setCopied(false)
    setStage('entering_otp')

    try {
      let freshCode = String(Math.floor(100000 + Math.random() * 900000))
      if (approvalId) {
        try {
          const res = await paymentApi.sendApprovalOtp(approvalId)
          if (res?.otp_code) {
            freshCode = res.otp_code
          }
        } catch {
          // fallback
        }
      }

      setGeneratedOtp(freshCode)
      setOtpDigits(['', '', '', '', '', ''])
      setCooldown(30)
      setExpiryCountdown(300)

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
      inputRefs[0]?.current?.focus()
    } finally {
      setIsSending(false)
    }
  }

  // Handle single digit typing or paste
  const handleDigitChange = (index, value) => {
    setOtpError(null)

    // Support full 6-digit paste
    if (value.length > 1) {
      const clean = value.replace(/\D/g, '').slice(0, 6)
      if (clean.length > 0) {
        const nextDigits = ['', '', '', '', '', '']
        for (let i = 0; i < clean.length; i++) {
          nextDigits[i] = clean[i]
        }
        setOtpDigits(nextDigits)
        setIncomingSms(null)
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

  // 1-Click Auto-fill from incoming SMS
  const handleAutoFillFromSms = () => {
    if (!generatedOtp) return
    const split = generatedOtp.split('').slice(0, 6)
    while (split.length < 6) split.push('')
    setOtpDigits(split)
    setOtpError(null)
    setIncomingSms(null)
    sound.playBlip && sound.playBlip()
    inputRefs[5]?.current?.focus()
  }

  // Copy OTP to clipboard
  const handleCopyOtp = () => {
    if (!generatedOtp) return
    navigator.clipboard?.writeText(generatedOtp)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    sound.playBlip && sound.playBlip()
  }

  // STEP 1: Verify OTP (Does NOT release transaction)
  const handleVerifyOtp = () => {
    if (expiryCountdown <= 0) {
      setOtpError('❌ OTP has expired. Please request a new code.')
      sound.playError && sound.playError()
      return
    }

    if (authMethod === 'otp') {
      const enteredCode = otpDigits.join('').trim()
      if (enteredCode.length < 6) {
        setOtpError('Please enter all 6 digits of the SMS OTP.')
        sound.playError && sound.playError()
        inputRefs[enteredCode.length]?.current?.focus()
        return
      }

      if (enteredCode !== generatedOtp) {
        const newFail = failedCount + 1
        setFailedCount(newFail)
        setOtpError(`❌ Invalid OTP Code! '${enteredCode}' does not match the 6-digit code. (Attempt ${newFail}/3)`)
        sound.playError && sound.playError()
        return
      }
    }

    // OTP verified successfully! Transition to 'otp_verified'
    // Transaction remains on SECURITY HOLD until user explicitly clicks ALLOW/APPROVE
    setStage('otp_verified')
    setOtpError(null)
    sound.playVerified && sound.playVerified()
  }

  // STEP 2: Explicit User Action — ALLOW / APPROVE
  const handleExplicitApprove = async () => {
    setStage('processing_approval')
    sound.playBlip && sound.playBlip()

    try {
      const challengeResponse = authMethod === 'otp' ? otpDigits.join('').trim() : 'BIOMETRIC_TOUCH_ID'
      if (onApprove) {
        await onApprove(approvalId, challengeResponse)
      }
      setStage('completed')
      sound.playVerified && sound.playVerified()

      setTimeout(() => {
        onClose && onClose()
      }, 1600)
    } catch (err) {
      setStage('otp_verified')
      setOtpError(err instanceof Error ? err.message : 'Server approval processing failed.')
      sound.playError && sound.playError()
    }
  }

  // User Action — REJECT / BLOCK
  const handleRejectClick = async () => {
    setStage('rejected')
    sound.playError && sound.playError()
    if (onReject) {
      await onReject(approvalId)
    }
    setTimeout(() => {
      onClose && onClose()
    }, 1800)
  }

  const formatSeconds = (sec) => {
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  const modalNode = (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-[99999] flex items-center justify-center p-3 sm:p-4 bg-slate-950/85 backdrop-blur-md animate-fadeIn select-none overflow-y-auto"
      style={{ isolation: 'isolate' }}
    >
      {/* Outer Shell */}
      <div className="relative w-full max-w-sm flex flex-col items-center my-auto">
        {/* Dismiss Button */}
        <button
          onClick={onClose}
          className="absolute -top-11 right-2 p-1.5 text-slate-400 hover:text-white rounded-full bg-slate-900 border border-slate-700 hover:border-slate-500 transition shadow-lg z-50"
          title="Close Phone Verification"
        >
          <X className="w-4 h-4" />
        </button>

        {/* =========================================================================
            TITANIUM SMARTPHONE CHASSIS
            ========================================================================= */}
        <div className="w-[335px] sm:w-[365px] min-h-[660px] rounded-[48px] bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900 p-3 shadow-[0_0_80px_rgba(6,182,212,0.35),0_25px_60px_rgba(0,0,0,0.95)] border-4 border-slate-700/80 relative flex flex-col justify-between overflow-hidden">
          {/* Dynamic Island Pill with Security Indicator */}
          <div className="absolute top-3.5 left-1/2 -translate-x-1/2 w-32 h-6 bg-black rounded-full z-40 flex items-center justify-between px-3 border border-slate-800 shadow-md">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-900 border border-slate-700" />
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${stage === 'otp_verified' ? 'bg-emerald-400 animate-ping' : 'bg-cyan-400 animate-ping'}`} />
              <div className={`w-2 h-2 rounded-full ${stage === 'otp_verified' ? 'bg-emerald-500' : 'bg-cyan-500'}`} />
            </div>
          </div>

          {/* Phone Glass Display Screen */}
          <div className="w-full h-full rounded-[38px] bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 border border-slate-800/80 flex flex-col justify-between p-3.5 pt-8 relative overflow-hidden text-slate-100">
            {/* Ambient Background Aura */}
            <div className="absolute -top-20 -left-20 w-44 h-44 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -right-20 w-44 h-44 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

            {/* Status Bar */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1 mb-1.5 z-10">
              <span className="font-bold text-white">{currentTime}</span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-cyan-400 font-mono">5G</span>
                <Signal className="w-3.5 h-3.5 text-slate-300" />
                <Wifi className="w-3.5 h-3.5 text-slate-300" />
                <div className="flex items-center gap-0.5">
                  <span className="text-[10px]">100%</span>
                  <BatteryCharging className="w-4 h-4 text-emerald-400" />
                </div>
              </div>
            </div>

            {/* =====================================================================
                INCOMING REAL SMS POPUP BANNER (Copy & 1-Click Auto-fill)
                ===================================================================== */}
            {incomingSms && (stage === 'entering_otp' || stage === 'verifying_otp') && (
              <div className="z-30 mb-2 p-2.5 rounded-2xl bg-slate-900/98 border border-cyan-500/80 shadow-[0_8px_30px_rgba(6,182,212,0.4)] backdrop-blur-xl animate-bounce-subtle space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <div className="p-1 rounded-lg bg-emerald-600 text-white shadow-sm">
                      <MessageSquare className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-bold text-white tracking-tight">
                      MESSAGES • {incomingSms.time}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-mono text-[9px] font-bold">
                      SMS DELIVERED
                    </span>
                    <button
                      type="button"
                      onClick={() => setIncomingSms(null)}
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
                      title="Dismiss"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <p className="text-[11px] text-slate-200 leading-snug">
                  FraudLens Bank: <strong className="text-white font-mono bg-cyan-950 px-1 py-0.5 rounded border border-cyan-700 tracking-wider font-extrabold text-cyan-300">{incomingSms.code}</strong> is your secret verification OTP for payment of {formatINR(incomingSms.amount)}.
                </p>

                {/* 1-Click Action Buttons */}
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

            {/* =====================================================================
                SECURITY HOLD HEADER & TRANSACTION CONTEXT
                ===================================================================== */}
            <div className="z-10 space-y-2">
              <div className="p-2.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md backdrop-blur-md">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <ShieldAlert className={`w-4 h-4 ${txLevel === 'HIGH' ? 'text-rose-400' : 'text-amber-400'}`} />
                    <span className="font-bold text-white text-[11px] uppercase tracking-wide">
                      Security Hold Active
                    </span>
                  </div>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                    txLevel === 'HIGH'
                      ? 'text-rose-300 bg-rose-950/80 border-rose-800'
                      : 'text-amber-300 bg-amber-950/80 border-amber-800'
                  }`}>
                    {txLevel} RISK ({txRisk}/100)
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

                {/* Multi-Stage Verification Progress Indicator */}
                <div className="mt-2 pt-2 border-t border-slate-800/80 grid grid-cols-3 gap-1 text-[9px] font-mono text-center">
                  <div className="p-1 rounded bg-slate-950/60 border border-emerald-700/60 text-emerald-400">
                    <div className="font-bold">1. Risk Check</div>
                    <div className="text-[8px] text-emerald-300">COMPLETE</div>
                  </div>
                  <div className={`p-1 rounded border ${
                    stage === 'otp_verified' || stage === 'processing_approval' || stage === 'completed'
                      ? 'bg-slate-950/60 border-emerald-700/60 text-emerald-400'
                      : 'bg-slate-950/60 border-cyan-600/60 text-cyan-300 animate-pulse'
                  }`}>
                    <div className="font-bold">2. OTP Check</div>
                    <div className="text-[8px]">
                      {stage === 'otp_verified' || stage === 'processing_approval' || stage === 'completed' ? 'VERIFIED' : 'PENDING'}
                    </div>
                  </div>
                  <div className={`p-1 rounded border ${
                    stage === 'completed'
                      ? 'bg-slate-950/60 border-emerald-700/60 text-emerald-400'
                      : stage === 'otp_verified'
                      ? 'bg-slate-950/60 border-amber-500/80 text-amber-300 animate-pulse font-bold'
                      : 'bg-slate-950/60 border-slate-800 text-slate-500'
                  }`}>
                    <div className="font-bold">3. Approval</div>
                    <div className="text-[8px]">
                      {stage === 'completed' ? 'APPROVED' : stage === 'otp_verified' ? 'WAITING' : 'LOCKED'}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* =====================================================================
                MAIN INTERACTIVE AUTHENTICATION BODY
                ===================================================================== */}
            <div className="z-10 my-auto py-1 space-y-2.5">
              {/* Method Toggle: OTP vs Biometric */}
              {(stage === 'entering_otp' || stage === 'verifying_otp') && (
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
                    <span>SMS OTP</span>
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
                    <span>Touch ID</span>
                  </button>
                </div>
              )}

              {/* STAGE 1: OTP INPUT FORM */}
              {stage === 'entering_otp' && authMethod === 'otp' && (
                <div className="space-y-2 bg-slate-950/90 p-3 rounded-2xl border border-slate-800">
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span className="font-semibold text-slate-300">
                      Enter 6-Digit Code:
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

                  {/* Error State */}
                  {otpError && (
                    <div className="p-2 rounded-xl bg-rose-950/90 border border-rose-600 text-rose-200 text-[10px] font-semibold flex items-start gap-1.5 animate-shake shadow-md">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-rose-400 mt-0.5" />
                      <span className="leading-tight">{otpError}</span>
                    </div>
                  )}

                  {/* Footer Expiry & Security Badge */}
                  <div className="flex items-center justify-between text-[9px] font-mono text-slate-500 pt-0.5 border-t border-slate-800/80">
                    <span className="flex items-center gap-1">
                      <Lock className="w-2.5 h-2.5 text-cyan-400" />
                      Expires in: <span className="text-cyan-300 font-bold">{formatSeconds(expiryCountdown)}</span>
                    </span>
                    <span className="text-cyan-400 font-bold">Copy/Paste Allowed</span>
                  </div>
                </div>
              )}

              {/* STAGE 1 (Biometric alternative) */}
              {stage === 'entering_otp' && authMethod === 'biometric' && (
                <div className="py-4 px-3 bg-slate-950/90 rounded-2xl border border-slate-800 text-center space-y-2">
                  <div className="relative w-16 h-16 mx-auto flex items-center justify-center">
                    <div className="absolute inset-0 bg-purple-500/20 rounded-full animate-ping pointer-events-none" />
                    <button
                      type="button"
                      onClick={handleVerifyOtp}
                      className="p-3.5 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-[0_0_20px_rgba(168,85,247,0.5)] active:scale-95 transition"
                    >
                      <Fingerprint className="w-8 h-8" />
                    </button>
                  </div>
                  <div className="text-xs font-bold text-white">Touch ID Sensor Ready</div>
                  <p className="text-[10px] text-slate-400 max-w-[200px] mx-auto leading-relaxed">
                    Tap sensor to scan registered biometric token for {formatINR(txAmount)}.
                  </p>
                </div>
              )}

              {/* STAGE 2: OTP VERIFIED — WAITING FOR EXPLICIT USER APPROVAL */}
              {stage === 'otp_verified' && (
                <div className="p-3.5 bg-slate-950/95 border-2 border-emerald-500/80 rounded-2xl text-center space-y-2 animate-fadeIn shadow-[0_0_25px_rgba(16,185,129,0.3)]">
                  <div className="w-10 h-10 rounded-full bg-emerald-950 border border-emerald-500 text-emerald-400 flex items-center justify-center mx-auto shadow-inner">
                    <CheckCircle2 className="w-6 h-6 animate-pulse" />
                  </div>
                  <div>
                    <div className="text-xs font-extrabold text-emerald-300 uppercase tracking-wide">
                      ✓ OTP Verified Successfully
                    </div>
                    <div className="text-[10px] text-slate-300 font-mono mt-0.5">
                      Transaction remains held until explicit authorization.
                    </div>
                  </div>

                  <div className="p-2 rounded-xl bg-amber-950/60 border border-amber-600/70 text-amber-200 text-[10px] text-left flex items-start gap-2">
                    <Lock className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block font-bold">Explicit Authorization Required:</strong>
                      Click <span className="text-white font-bold underline">ALLOW / APPROVE</span> below to finalize transaction and debit bank balance.
                    </div>
                  </div>
                </div>
              )}

              {/* PROCESSING SPINNER */}
              {stage === 'processing_approval' && (
                <div className="p-4 bg-slate-950/95 border border-cyan-500 rounded-2xl text-center space-y-2 animate-fadeIn">
                  <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
                  <div className="text-xs font-bold text-cyan-200 font-mono">
                    Executing Bank Authorization &amp; Balance Debit...
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Updating ledger balance atomically in database.
                  </p>
                </div>
              )}

              {/* OUTCOME: COMPLETED */}
              {stage === 'completed' && (
                <div className="p-3.5 bg-emerald-950/95 border border-emerald-500 rounded-2xl text-center space-y-1.5 animate-scaleUp shadow-[0_0_25px_rgba(16,185,129,0.4)]">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                  <div className="text-sm font-extrabold text-emerald-200">
                    Payment Authorized &amp; Completed!
                  </div>
                  <p className="text-[11px] text-emerald-300/90">
                    {formatINR(txAmount)} released to {txMerchant}. Bank balance updated immediately.
                  </p>
                </div>
              )}

              {/* OUTCOME: REJECTED */}
              {stage === 'rejected' && (
                <div className="p-3.5 bg-rose-950/95 border border-rose-500 rounded-2xl text-center space-y-1.5 animate-scaleUp shadow-[0_0_25px_rgba(225,29,72,0.4)]">
                  <XCircle className="w-8 h-8 text-rose-400 mx-auto" />
                  <div className="text-sm font-extrabold text-rose-200">
                    Transaction Terminated &amp; Blocked
                  </div>
                  <p className="text-[11px] text-rose-300/90">
                    Zero funds deducted. Available bank balance remains completely protected.
                  </p>
                </div>
              )}
            </div>

            {/* =====================================================================
                BOTTOM ACTION CONTROLS (TWO-STEP ENFORCEMENT)
                ===================================================================== */}
            <div className="z-10 space-y-2 pt-1 border-t border-slate-800">
              {/* Step 1: Verify OTP Button */}
              {stage === 'entering_otp' && (
                <>
                  <button
                    type="button"
                    onClick={handleVerifyOtp}
                    className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-black text-xs shadow-lg shadow-cyan-950 flex items-center justify-center gap-2 transition active:scale-95"
                  >
                    <KeyRound className="w-4 h-4" />
                    <span>VERIFY OTP</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleRejectClick}
                    className="w-full py-2 px-3 rounded-xl bg-rose-950/70 hover:bg-rose-900/80 border border-rose-700/60 text-rose-300 font-bold text-xs flex items-center justify-center gap-1.5 transition active:scale-95"
                  >
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span>NO, FRAUD! BLOCK CARD</span>
                  </button>
                </>
              )}

              {/* Step 2: Explicit ALLOW / APPROVE Button (Only activates after OTP verified) */}
              {stage === 'otp_verified' && (
                <>
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={handleExplicitApprove}
                    className="w-full py-3 px-3 rounded-xl bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-white font-black text-xs shadow-[0_0_25px_rgba(16,185,129,0.5)] flex items-center justify-center gap-2 transition transform active:scale-95 animate-pulse"
                  >
                    <Unlock className="w-4 h-4 text-white" />
                    <span>ALLOW / APPROVE TRANSACTION</span>
                  </button>

                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={handleRejectClick}
                    className="w-full py-2 px-3 rounded-xl bg-slate-900 hover:bg-rose-950/80 border border-slate-700 hover:border-rose-600 text-slate-300 hover:text-rose-200 font-bold text-xs flex items-center justify-center gap-1.5 transition active:scale-95"
                  >
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span>DENY &amp; CANCEL PAYMENT</span>
                  </button>
                </>
              )}
            </div>

            {/* iPhone Home Indicator Bar */}
            <div className="w-32 h-1 bg-slate-700 rounded-full mx-auto mt-2 z-10" />
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(modalNode, document.body)
}
