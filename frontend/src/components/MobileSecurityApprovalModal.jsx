import React, { useState, useEffect, useRef, useMemo } from 'react'
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
  Activity,
  Clock,
  Zap,
} from 'lucide-react'
import { formatINR, formatDateTime } from '../utils/formatters'
import { sound } from './login/soundEffects'
import { paymentApi } from '../services/api'
import { getCustomerPhone } from '../utils/customerHelper'

/**
 * MobileSecurityApprovalModal
 *
 * Upgraded High-Fintech Security Verification Interface.
 * Implements authoritative rapid transaction detection, "Why OTP is Required?" explanation panel,
 * 3-4s auto-settling futuristic security pulse shield, transaction summary, SMS banner, masked
 * registered phone number display, two-step OTP verification and explicit Allow/Approve controls.
 */
export default function MobileSecurityApprovalModal({
  isOpen,
  onClose,
  transaction,
  approvalId,
  customerName = 'Customer',
  customerPhone = null,
  maskedCustomerPhone = null,
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
  const [verifiedToken, setVerifiedToken] = useState('')
  
  // Verification lifecycle states:
  // 'entering_otp' -> 'otp_verified' -> 'processing_approval' -> 'completed' -> 'rejected'
  const [stage, setStage] = useState('entering_otp')
  const [currentTime, setCurrentTime] = useState('09:41')
  const [copied, setCopied] = useState(false)
  const [expiryCountdown, setExpiryCountdown] = useState(300) // 5 minutes

  // 3-4 Second Auto-Settling Security Animation State
  const [isScanning, setIsScanning] = useState(true)
  const scanTimerRef = useRef(null)

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

  // Trigger 3.5s auto-settling animation when opened
  useEffect(() => {
    if (isOpen) {
      setIsScanning(true)
      if (scanTimerRef.current) clearTimeout(scanTimerRef.current)
      scanTimerRef.current = setTimeout(() => {
        setIsScanning(false)
      }, 3500)
    }
    return () => {
      if (scanTimerRef.current) clearTimeout(scanTimerRef.current)
    }
  }, [isOpen])

  const handleReplayScan = () => {
    setIsScanning(true)
    sound.playAlert && sound.playAlert()
    if (scanTimerRef.current) clearTimeout(scanTimerRef.current)
    scanTimerRef.current = setTimeout(() => {
      setIsScanning(false)
    }, 3500)
  }

  // Modal Initialization
  useEffect(() => {
    if (isOpen) {
      setStage('entering_otp')
      setOtpDigits(['', '', '', '', '', ''])
      setOtpError(null)
      setFailedCount(0)
      setCopied(false)
      setExpiryCountdown(300)

      let initialOtp = transaction?.otp_code

      const initOtp = async () => {
        if (!initialOtp && approvalId && approvalId !== 'PEND_DEMO_01' && !approvalId.startsWith('DEMO_')) {
          try {
            const res = await paymentApi.sendApprovalOtp(approvalId)
            if (res?.otp_code) {
              initialOtp = res.otp_code
            }
          } catch {
            // fallback
          }
        }

        if (!initialOtp) {
          initialOtp = String(Math.floor(100000 + Math.random() * 900000))
        }

        setGeneratedOtp(initialOtp)

        // Incoming SMS Push Banner after 350ms
        setIncomingSms({
          sender: 'FraudLens Bank SMS',
          code: initialOtp,
          amount: transaction?.amount || 500,
          merchant:
            transaction?.merchant_name ||
            transaction?.beneficiary_name ||
            'NovaMart Fresh',
          time: 'now',
        })
        sound.playAlert && sound.playAlert()
      }

      const smsTimer = setTimeout(initOtp, 350)
      setCooldown(30)
      setTimeout(() => inputRefs[0]?.current?.focus(), 300)
      return () => clearTimeout(smsTimer)
    } else {
      setIncomingSms(null)
    }
  }, [isOpen, transaction, approvalId])

  const txCustomerId = transaction?.customer_id || 'CUST_MONISHA_001'
  const txCustomerName = customerName || transaction?.customer_name || 'Cardholder'

  // Customer registered phone resolution (Must be called before any early return)
  const resolvedPhone = useMemo(() => {
    return getCustomerPhone(txCustomerId, {
      name: txCustomerName,
    })
  }, [txCustomerId, txCustomerName])

  if (!isOpen || typeof document === 'undefined') return null

  const txAmount = transaction?.amount || 500
  const txMerchant =
    transaction?.merchant_name || transaction?.beneficiary_name || 'NovaMart Fresh'
  const txLocation = transaction?.location || 'Salem, IN'
  const txRisk = transaction?.risk_score !== undefined ? transaction?.risk_score : 18
  const txLevel = transaction?.risk_level || (txRisk > 70 ? 'HIGH' : (txRisk > 30 ? 'MEDIUM' : 'LOW'))
  const txId = transaction?.transaction_id || transaction?.payment_id || 'PAY-REF9841'
  const txType = transaction?.transaction_type || transaction?.payment_channel || 'UPI / Online Payment'
  const txDate = transaction?.timestamp ? formatDateTime(transaction.timestamp) : new Date().toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })

  const displayMaskedPhone = maskedCustomerPhone || resolvedPhone?.maskedPhone || '+91 94432 ••••5'
  const displayFullPhone = customerPhone || resolvedPhone?.phone || '+91 94432 51845'

  // Rapid Transaction Activity Telemetry & Context
  const isRapid = Boolean(
    transaction?.rapid_activity_detected ||
    transaction?.security_trigger === 'RAPID_TRANSACTION_ACTIVITY' ||
    (transaction?.rapid_activity_count && transaction?.rapid_activity_count >= 3)
  )
  const rapidCount = transaction?.rapid_activity_count || (isRapid ? 4 : 1)
  const rapidWindow = transaction?.rapid_activity_window_minutes || 60
  const recentAmounts = transaction?.recent_transaction_amounts || []
  const securityTrigger = transaction?.security_trigger || (isRapid ? 'RAPID_TRANSACTION_ACTIVITY' : 'SECURITY_HOLD')
  const whyOtpReason = transaction?.why_otp_reason || (isRapid
    ? 'Multiple transactions were detected within a short period. For your account\'s protection, additional verification is required before this payment can be completed.'
    : 'Elevated risk parameters or unusual payment behavior detected. Additional verification is required for account protection.')
  const whyOtpExplanation = transaction?.why_otp_explanation || (isRapid
    ? 'Rapid transaction activity may indicate unusual or unauthorized activity.'
    : 'Security hold active to verify that this payment is authorized by the account owner.')

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

  // STEP 4: VERIFY OTP ACTION (Strict validation without auto-debiting)
  const handleVerifyOtpOnly = async () => {
    if (expiryCountdown <= 0) {
      setOtpError('❌ OTP has expired. Please request a new code.')
      sound.playError && sound.playError()
      return
    }

    let codeToVerify = ''
    if (authMethod === 'otp') {
      codeToVerify = otpDigits.join('').trim()
      if (codeToVerify.length < 6) {
        setOtpError('Please enter all 6 digits of the SMS OTP.')
        sound.playError && sound.playError()
        inputRefs[codeToVerify.length]?.current?.focus()
        return
      }

      if (codeToVerify !== generatedOtp && generatedOtp) {
        const newFail = failedCount + 1
        setFailedCount(newFail)
        setOtpError(`❌ Invalid OTP Code! '${codeToVerify}' does not match the 6-digit security token. (Attempt ${newFail}/3)`)
        sound.playError && sound.playError()
        return
      }
    } else {
      codeToVerify = 'BIOMETRIC_TOUCH_ID'
    }

    // OTP Successfully Verified!
    setVerifiedToken(codeToVerify)
    setStage('otp_verified')
    setOtpError(null)
    sound.playVerified && sound.playVerified()
  }

  // STEP 5: EXPLICIT ALLOW / APPROVE TRANSACTION (Enabled only after OTP is verified)
  const handleExecuteApproval = async () => {
    if (stage !== 'otp_verified') return
    if (expiryCountdown <= 0) {
      setOtpError('❌ Security session expired. Please re-verify OTP.')
      sound.playError && sound.playError()
      setStage('entering_otp')
      return
    }

    setStage('processing_approval')
    sound.playBlip && sound.playBlip()

    try {
      if (onApprove) {
        await onApprove(approvalId, verifiedToken || generatedOtp)
      }
      setStage('completed')
      sound.playVerified && sound.playVerified()

      setTimeout(() => {
        onClose && onClose()
      }, 1600)
    } catch (err) {
      setStage('otp_verified')
      setOtpError(err instanceof Error ? err.message : 'Server approval verification failed.')
      sound.playError && sound.playError()
    }
  }

  // User Action — REJECT / CANCEL / BLOCK
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
      className="fixed inset-0 z-[99999] flex items-center justify-center p-2 sm:p-4 bg-slate-950/90 backdrop-blur-md animate-fadeIn select-none overflow-y-auto"
      style={{ isolation: 'isolate' }}
    >
      {/* Outer Titanium Shell */}
      <div className="relative w-full max-w-md sm:max-w-lg flex flex-col items-center my-auto py-2">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute -top-10 right-2 p-1.5 text-slate-400 hover:text-white rounded-full bg-slate-900 border border-slate-700 hover:border-slate-500 transition shadow-lg z-50 cursor-pointer"
          title="Close Verification"
        >
          <X className="w-4 h-4" />
        </button>

        {/* =========================================================================
            TITANIUM SECURITY CHASSIS & SCREEN
            ========================================================================= */}
        <div className="w-full max-h-[92vh] rounded-[42px] bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900 p-2.5 sm:p-3 shadow-[0_0_90px_rgba(6,182,212,0.35),0_25px_60px_rgba(0,0,0,0.95)] border-4 border-slate-700/80 relative flex flex-col overflow-hidden">
          {/* Dynamic Island Security Indicator */}
          <div className="w-36 h-6 bg-black rounded-full mx-auto z-40 flex items-center justify-between px-3 border border-slate-800 shadow-md mb-2 shrink-0">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-900 border border-slate-700" />
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${isScanning ? 'bg-cyan-400 animate-ping' : 'bg-emerald-400'}`} />
              <div className={`w-2 h-2 rounded-full ${isScanning ? 'bg-cyan-500' : 'bg-emerald-500'}`} />
            </div>
          </div>

          {/* Internal Scrollable Display Viewport */}
          <div className="w-full rounded-[34px] bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 border border-slate-800/80 flex flex-col p-3.5 sm:p-4 relative overflow-y-auto max-h-[calc(92vh-4rem)] text-slate-100 space-y-3.5">
            {/* Ambient Background Aura */}
            <div className="absolute -top-20 -left-20 w-44 h-44 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -right-20 w-44 h-44 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

            {/* 1. SECTION: SECURITY VERIFICATION HEADER */}
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 z-10">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-cyan-950 border border-cyan-700 text-cyan-400 shadow-sm">
                  <Lock className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-xs font-black tracking-wider text-white uppercase font-mono">
                    Security Verification
                  </h2>
                  <p className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                    <span>SMS dispatched to:</span>
                    <strong className="text-cyan-300 font-bold">{displayMaskedPhone}</strong>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1.5 font-mono text-[10px]">
                <span className="text-cyan-400 font-bold">{currentTime}</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-emerald-400 text-[9px] font-bold">
                  256-BIT SSL
                </span>
              </div>
            </div>

            {/* =========================================================================
                2. SECTION: WHY OTP IS REQUIRED — PREMIUM SECURITY EXPLANATION PANEL
                ========================================================================= */}
            <div className="p-3.5 rounded-2xl bg-gradient-to-b from-cyan-950/30 via-slate-900/90 to-slate-950/90 border border-cyan-500/40 shadow-lg space-y-2.5 z-10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <ShieldAlert className={`w-4 h-4 ${isRapid ? 'text-cyan-400' : 'text-amber-400'}`} />
                  <span className="text-xs font-extrabold text-white uppercase tracking-wider font-mono">
                    Why is OTP Required?
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
                  {isRapid ? 'RAPID TRANSACTION DETECTED' : 'SECURITY HOLD'}
                </span>
              </div>

              {/* Explanatory Content */}
              <div className="text-[11px] text-slate-200 leading-relaxed space-y-1">
                <p className="font-medium text-slate-100">
                  &ldquo;{whyOtpReason}&rdquo;
                </p>
                <p className="text-[10px] text-cyan-300/90 font-mono">
                  &ldquo;{whyOtpExplanation}&rdquo;
                </p>
              </div>

              {/* =========================================================================
                  7 & 8. SOPHISTICATED SECURITY VISUAL (AUTO-PLAYS 3-4s, THEN SETTLES)
                  ========================================================================= */}
              <div className="p-3 rounded-xl bg-slate-950/80 border border-cyan-500/20 text-center relative overflow-hidden my-1">
                {/* Visual Rings and Shield */}
                <div className="relative w-20 h-20 mx-auto my-1 flex items-center justify-center">
                  {/* Outer Orbital Pulse Ring */}
                  <div
                    className={`absolute inset-0 rounded-full border-2 transition-all duration-1000 ${
                      isScanning
                        ? 'border-cyan-400/90 animate-spin border-t-transparent shadow-[0_0_20px_rgba(6,182,212,0.6)]'
                        : 'border-emerald-500/70 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
                    }`}
                    style={{ animationDuration: '3.5s' }}
                  />

                  {/* Middle Concentric Ring */}
                  <div
                    className={`absolute inset-2 rounded-full border border-dashed transition-all duration-1000 ${
                      isScanning
                        ? 'border-indigo-400/80 animate-reverse-spin'
                        : 'border-cyan-500/50'
                    }`}
                    style={{ animationDuration: '5s' }}
                  />

                  {/* Core Glow Aura */}
                  <div
                    className={`absolute inset-3 rounded-full blur-md transition-all duration-700 ${
                      isScanning ? 'bg-cyan-500/30 animate-pulse' : 'bg-emerald-500/20'
                    }`}
                  />

                  {/* Central Shield Graphic */}
                  <div
                    className={`relative z-10 w-11 h-11 rounded-xl flex items-center justify-center border transition-all duration-700 ${
                      isScanning
                        ? 'bg-slate-900 border-cyan-400 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.8)] scale-105'
                        : 'bg-emerald-950 border-emerald-500 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.5)]'
                    }`}
                  >
                    {isScanning ? (
                      <ShieldAlert className="w-5 h-5 animate-pulse text-cyan-300" />
                    ) : (
                      <ShieldCheck className="w-5 h-5 text-emerald-400" />
                    )}
                  </div>
                </div>

                {/* Status Telemetry Text & Replay Action */}
                <div className="flex items-center justify-center gap-1.5 mt-1">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isScanning ? 'bg-cyan-400 animate-ping' : 'bg-emerald-400'
                    }`}
                  />
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-cyan-200">
                    {isScanning
                      ? 'Deploying Gateway Protection Ring...'
                      : 'Payment Temporarily Secured & Protected'}
                  </span>
                  {!isScanning && (
                    <button
                      type="button"
                      onClick={handleReplayScan}
                      className="p-1 text-slate-400 hover:text-cyan-300 rounded hover:bg-slate-800 transition cursor-pointer"
                      title="Replay Security Scan"
                    >
                      <RefreshCw className="w-3 h-3" />
                    </button>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Your payment of {formatINR(txAmount)} is temporarily being protected and verified.
                </p>
              </div>

              {/* 6. RAPID TRANSACTION EVIDENCE DETAILS */}
              <div className="p-2.5 rounded-xl bg-slate-950/90 border border-slate-800 space-y-1.5 text-[10px] font-mono">
                <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1">
                  <Activity className="w-3 h-3 text-cyan-400" />
                  <span>Rapid Activity Evidence Details</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[9px] text-slate-400 block">Recent Activity:</span>
                    <strong className="text-white font-bold">
                      {rapidCount} transactions detected
                    </strong>
                    <span className="text-[9px] text-cyan-300 block">within last {rapidWindow} mins</span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[9px] text-slate-400 block">Current Transaction:</span>
                    <strong className="text-white font-bold text-xs">{formatINR(txAmount)}</strong>
                    <span className="text-[9px] text-slate-400 block">Merchant: {txMerchant}</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-1 pt-0.5 text-center">
                  <div className="p-1 rounded bg-slate-900/60 border border-slate-800">
                    <span className="text-[8px] text-slate-400 block uppercase">Fraud Risk</span>
                    <span className={`text-[10px] font-bold ${txLevel === 'LOW' ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {txLevel} ({txRisk}/100)
                    </span>
                  </div>
                  <div className="p-1 rounded bg-slate-900/60 border border-slate-800">
                    <span className="text-[8px] text-slate-400 block uppercase">Security Signal</span>
                    <span className="text-[10px] font-bold text-cyan-300 truncate block">
                      {isRapid ? 'RAPID DETECTED' : 'HOLD ACTIVE'}
                    </span>
                  </div>
                  <div className="p-1 rounded bg-slate-900/60 border border-slate-800">
                    <span className="text-[8px] text-slate-400 block uppercase">OTP Status</span>
                    <span className="text-[10px] font-bold text-amber-300">
                      REQUIRED
                    </span>
                  </div>
                </div>

                {recentAmounts && recentAmounts.length > 0 && (
                  <div className="pt-1 text-[9px] text-slate-400 flex items-center justify-between border-t border-slate-800/80">
                    <span>Recent Prior Amounts:</span>
                    <span className="font-mono text-slate-300 font-semibold">
                      {recentAmounts.slice(0, 4).map((amt) => formatINR(amt)).join(', ')}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* =========================================================================
                10. SECTION: TRANSACTION SUMMARY
                ========================================================================= */}
            <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800 text-xs space-y-1.5 z-10">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5">
                <span className="text-[10px] uppercase font-bold text-slate-400 font-mono flex items-center gap-1">
                  <CreditCard className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Transaction Summary</span>
                </span>
                <span className="text-[10px] font-mono text-cyan-300 font-bold">
                  {txId}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-slate-300 font-mono">
                <div>
                  <span className="text-slate-500">Customer:</span>{' '}
                  <span className="text-white font-medium">{txCustomerName} ({txCustomerId})</span>
                </div>
                <div>
                  <span className="text-slate-500">Amount:</span>{' '}
                  <span className="text-white font-bold">{formatINR(txAmount)}</span>
                </div>
                <div>
                  <span className="text-slate-500">Merchant:</span>{' '}
                  <span className="text-white font-medium">{txMerchant}</span>
                </div>
                <div>
                  <span className="text-slate-500">Registered Phone:</span>{' '}
                  <span className="text-cyan-300 font-bold">{displayMaskedPhone}</span>
                </div>
                <div>
                  <span className="text-slate-500">Type / Channel:</span>{' '}
                  <span className="text-white font-medium">{txType}</span>
                </div>
                <div>
                  <span className="text-slate-500">Date &amp; Time:</span>{' '}
                  <span className="text-white font-medium">{txDate}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-500">Security Trigger:</span>{' '}
                  <span className="text-cyan-300 font-bold">{securityTrigger}</span>
                </div>
              </div>
            </div>

            {/* =====================================================================
                INCOMING REAL SMS POPUP BANNER (Copy & 1-Click Auto-fill)
                ===================================================================== */}
            {incomingSms && (stage === 'entering_otp' || stage === 'otp_verified') && (
              <div className="z-30 p-2.5 rounded-2xl bg-slate-900/98 border border-cyan-500/80 shadow-[0_8px_30px_rgba(6,182,212,0.4)] backdrop-blur-xl animate-bounce-subtle space-y-1.5">
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
                      SMS DISPATCHED ({displayMaskedPhone})
                    </span>
                    <button
                      type="button"
                      onClick={() => setIncomingSms(null)}
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                      title="Dismiss"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <p className="text-[11px] text-slate-200 leading-snug">
                  FraudLens Bank SMS: <strong className="text-white font-mono bg-cyan-950 px-1 py-0.5 rounded border border-cyan-700 tracking-wider font-extrabold text-cyan-300">{incomingSms.code}</strong> is your secret verification OTP for payment of {formatINR(incomingSms.amount)}.
                </p>

                <div className="text-[9px] text-slate-400 font-mono">
                  [DEV/TESTING DELIVERY]: Dispatched to authorized customer phone ({displayMaskedPhone}).
                </div>

                {/* 1-Click Action Buttons */}
                <div className="flex items-center gap-2 pt-0.5 text-[10px]">
                  <button
                    type="button"
                    disabled={stage === 'otp_verified'}
                    onClick={handleAutoFillFromSms}
                    className="flex-1 py-1 px-2 rounded-lg bg-cyan-600/90 hover:bg-cyan-500 text-white font-semibold flex items-center justify-center gap-1 shadow-sm transition active:scale-95 cursor-pointer disabled:opacity-50"
                  >
                    <Check className="w-3 h-3" />
                    <span>Auto-Fill Code ({incomingSms.code})</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCopyOtp}
                    className="py-1 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium flex items-center gap-1 border border-slate-700 transition cursor-pointer"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* =====================================================================
                5. SECTION: OTP INPUT FORM
                ===================================================================== */}
            <div className="z-10 space-y-2">
              {/* Method Toggle: OTP vs Biometric */}
              {stage === 'entering_otp' && (
                <div className="flex p-0.5 bg-slate-950 rounded-xl border border-slate-800 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setAuthMethod('otp')}
                    className={`flex-1 py-1 rounded-lg font-semibold flex items-center justify-center gap-1 transition cursor-pointer ${
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
                    className={`flex-1 py-1 rounded-lg font-semibold flex items-center justify-center gap-1 transition cursor-pointer ${
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

              {/* STAGE 1 & 2: OTP INPUT FORM */}
              {(stage === 'entering_otp' || stage === 'otp_verified') && authMethod === 'otp' && (
                <div className="space-y-2 bg-slate-950/90 p-3 rounded-2xl border border-slate-800">
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                      {stage === 'otp_verified' ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-emerald-300 font-bold">OTP Code Verified:</span>
                        </>
                      ) : (
                        <span>Enter 6-Digit Verification OTP:</span>
                      )}
                    </span>
                    {stage === 'entering_otp' && (
                      <button
                        type="button"
                        disabled={cooldown > 0 || isSending}
                        onClick={handleSendNewOtp}
                        className="text-cyan-400 hover:text-cyan-300 font-semibold underline flex items-center gap-1 disabled:text-slate-600 cursor-pointer"
                      >
                        <RefreshCw className={`w-3 h-3 ${isSending ? 'animate-spin' : ''}`} />
                        <span>{cooldown > 0 ? `Resend (${cooldown}s)` : 'Resend Code'}</span>
                      </button>
                    )}
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
                        disabled={stage === 'otp_verified'}
                        value={digit}
                        onChange={(e) => handleDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleKeyDown(idx, e)}
                        placeholder="•"
                        className={`w-9 sm:w-11 h-10 sm:h-12 text-center font-mono text-lg font-black rounded-xl bg-slate-900 border transition-all ${
                          stage === 'otp_verified'
                            ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
                            : digit
                            ? 'border-cyan-400 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.4)]'
                            : 'border-slate-700 text-slate-500 focus:border-cyan-500'
                        } focus:outline-none focus:scale-105`}
                      />
                    ))}
                  </div>

                  {/* Stage otp_verified explicit banner */}
                  {stage === 'otp_verified' && (
                    <div className="p-2.5 rounded-xl bg-emerald-950/90 border border-emerald-500 text-emerald-200 text-xs font-semibold flex items-start gap-2 shadow-md animate-fadeIn">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="font-extrabold text-emerald-300">OTP Verified Successfully!</div>
                        <div className="text-[10px] text-emerald-200/90 font-normal">
                          Cardholder identity confirmed for {formatINR(txAmount)}. Click &quot;ALLOW / APPROVE TRANSACTION&quot; below to explicitly authorize payment.
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error State Banner */}
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
                    <span className="text-cyan-400 font-bold">Copy/Paste Supported</span>
                  </div>
                </div>
              )}

              {/* STAGE 1: Biometric alternative */}
              {stage === 'entering_otp' && authMethod === 'biometric' && (
                <div className="py-4 px-3 bg-slate-950/90 rounded-2xl border border-slate-800 text-center space-y-2">
                  <div className="relative w-16 h-16 mx-auto flex items-center justify-center">
                    <div className="absolute inset-0 bg-purple-500/20 rounded-full animate-ping pointer-events-none" />
                    <button
                      type="button"
                      onClick={handleVerifyOtpOnly}
                      className="p-3.5 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-[0_0_20px_rgba(168,85,247,0.5)] active:scale-95 transition cursor-pointer"
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

              {/* PROCESSING SPINNER */}
              {stage === 'processing_approval' && (
                <div className="p-4 bg-slate-950/95 border border-cyan-500 rounded-2xl text-center space-y-2 animate-fadeIn">
                  <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
                  <div className="text-xs font-bold text-cyan-200 font-mono">
                    Verifying OTP &amp; Authorizing Payment...
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Executing atomic balance debit and recording transaction to customer ledger.
                  </p>
                </div>
              )}

              {/* OUTCOME: COMPLETED */}
              {stage === 'completed' && (
                <div className="p-3.5 bg-emerald-950/95 border border-emerald-500 rounded-2xl text-center space-y-1.5 animate-scaleUp shadow-[0_0_25px_rgba(16,185,129,0.4)]">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                  <div className="text-sm font-extrabold text-emerald-200">
                    OTP Verified &amp; Payment Completed!
                  </div>
                  <p className="text-[11px] text-emerald-300/90">
                    {formatINR(txAmount)} successfully released to {txMerchant}. Customer ledger updated atomically.
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
                BOTTOM ACTION CONTROLS: VERIFY OTP -> ALLOW/APPROVE -> CANCEL / DENY
                ===================================================================== */}
            <div className="z-10 space-y-2 pt-1 border-t border-slate-800 shrink-0">
              {stage === 'entering_otp' && (
                <>
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={handleVerifyOtpOnly}
                    className="w-full py-3 px-3 rounded-xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-black text-xs shadow-lg shadow-cyan-950/60 flex items-center justify-center gap-2 transition active:scale-95 cursor-pointer"
                  >
                    <KeyRound className="w-4 h-4" />
                    <span>VERIFY OTP CODE</span>
                  </button>

                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={handleRejectClick}
                    className="w-full py-2 px-3 rounded-xl bg-rose-950/70 hover:bg-rose-900/80 border border-rose-700/60 text-rose-300 font-bold text-xs flex items-center justify-center gap-1.5 transition active:scale-95 cursor-pointer"
                  >
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span>CANCEL / DENY TRANSACTION</span>
                  </button>
                </>
              )}

              {stage === 'otp_verified' && (
                <>
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={handleExecuteApproval}
                    className="w-full py-3 px-3 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white font-black text-xs shadow-xl shadow-emerald-950/70 flex items-center justify-center gap-2 transition active:scale-95 cursor-pointer animate-pulse"
                  >
                    <CheckCircle2 className="w-4 h-4 text-white" />
                    <span>ALLOW / APPROVE TRANSACTION</span>
                  </button>

                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={handleRejectClick}
                    className="w-full py-2 px-3 rounded-xl bg-rose-950/70 hover:bg-rose-900/80 border border-rose-700/60 text-rose-300 font-bold text-xs flex items-center justify-center gap-1.5 transition active:scale-95 cursor-pointer"
                  >
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span>CANCEL / DENY TRANSACTION</span>
                  </button>
                </>
              )}
            </div>

            {/* Device Home Indicator Bar */}
            <div className="w-32 h-1 bg-slate-700 rounded-full mx-auto mt-2 z-10 shrink-0" />
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(modalNode, document.body)
}
