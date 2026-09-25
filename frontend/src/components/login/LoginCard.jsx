import React, { useState } from 'react'
import {
  ShieldCheck,
  Shield,
  KeyRound,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  UserCheck,
  User,
  Search,
  CheckCircle2,
  Sparkles,
  CreditCard,
  ShieldAlert,
} from 'lucide-react'
import { sound } from './soundEffects'

/**
 * LoginCard - Floating Glass Authentication & Registration Panel.
 * Supports Sign In & Customer Self-Registration with instant token provisioning,
 * 1-click quick-fill demo credentials, and real-time audio/visual cyber feedback.
 */
export default function LoginCard({
  name = '',
  setName = () => {},
  email = '',
  setEmail = () => {},
  password = '',
  setPassword = () => {},
  onSubmit,
  onRegister,
  authLoading,
  authError,
  isUnlocked,
  sequenceStage,
}) {
  const [activeTab, setActiveTab] = useState('signin') // 'signin' | 'register'
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(true)
  const [showForgotNotice, setShowForgotNotice] = useState(false)

  const handleFormSubmit = (e) => {
    e.preventDefault()
    if (authLoading || isUnlocked) return
    sound.playBlip()
    onSubmit && onSubmit(e)
  }

  const isTransitioningOut =
    sequenceStage === 'SYSTEM_HANDOFF' ||
    sequenceStage === 'ENERGY_PULSE' ||
    sequenceStage === 'COMMAND_CENTER_OPEN'

  return (
    <div
      className={`w-full max-w-md lg:w-[32vw] lg:max-w-[460px] lg:mr-[3.8vw] rounded-3xl bg-slate-950/85 backdrop-blur-xl border-2 border-cyan-400/60 p-5 sm:p-6 shadow-[0_0_50px_rgba(6,182,212,0.35),inset_0_0_20px_rgba(6,182,212,0.15)] relative transition-all duration-700 ${
        isTransitioningOut
          ? 'scale-75 opacity-0 blur-md pointer-events-none'
          : 'scale-100 opacity-100'
      }`}
    >
      {/* Outer Cyan Neon Corner Brackets */}
      <div className="absolute -top-1.5 -left-1.5 w-6 h-6 border-t-2 border-l-2 border-cyan-300 rounded-tl-xl pointer-events-none" />
      <div className="absolute -top-1.5 -right-1.5 w-6 h-6 border-t-2 border-r-2 border-cyan-300 rounded-tr-xl pointer-events-none" />
      <div className="absolute -bottom-1.5 -left-1.5 w-6 h-6 border-b-2 border-l-2 border-cyan-300 rounded-bl-xl pointer-events-none" />
      <div className="absolute -bottom-1.5 -right-1.5 w-6 h-6 border-b-2 border-r-2 border-cyan-300 rounded-br-xl pointer-events-none" />

      {/* Card Header Branding */}
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 border border-cyan-400/50 shadow-[0_0_15px_rgba(6,182,212,0.6)]">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-extrabold text-white tracking-tight leading-none">
            FraudLens <span className="text-cyan-400">AI</span>
          </h2>
          <div className="text-[10px] font-mono font-bold text-cyan-300 uppercase tracking-wider mt-0.5">
            SECURE ENTERPRISE AUTHENTICATION
          </div>
        </div>
      </div>

      <div className="mb-3.5">
        <h3 className="text-lg font-black text-white tracking-tight">
          Sign In to Access Platform
        </h3>
        <p className="text-xs text-slate-300 mt-0.5">
          Select one of the 4 role portals below or enter your credentials.
        </p>
      </div>

      {/* Authentication Error Banner */}
      {authError && (
        <div
          role="alert"
          className="p-2.5 rounded-xl bg-rose-950/80 border border-rose-600 text-rose-200 text-xs flex items-center gap-2 mb-3 shadow-[0_0_20px_rgba(225,29,72,0.4)] animate-shake"
        >
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span className="font-medium">{authError}</span>
        </div>
      )}

      {/* Forgot Password Modal Helper */}
      {showForgotNotice && (
        <div className="p-3 rounded-xl bg-cyan-950/80 border border-cyan-600 text-cyan-200 text-xs mb-3 flex items-start justify-between gap-2">
          <div>
            <strong className="block font-semibold mb-0.5">Enterprise Password Reset</strong>
            Contact your fraud platform administrator to provision a password reset token.
          </div>
          <button
            type="button"
            onClick={() => setShowForgotNotice(false)}
            className="text-cyan-400 hover:text-white text-sm font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Form Controls */}
      <form onSubmit={handleFormSubmit} className="space-y-3">
        {/* Email Address Input */}
        <div className="space-y-1">
          <label htmlFor="login-email" className="block text-xs font-semibold text-slate-300">
            Email Address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Mail className="w-4 h-4" />
            </div>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="username"
              disabled={authLoading || isUnlocked}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@fraudlens.internal"
              className="w-full bg-slate-900/80 border border-slate-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-xl pl-10 pr-3.5 py-2 text-xs sm:text-sm text-white placeholder:text-slate-500 font-sans transition outline-none disabled:opacity-50"
            />
          </div>
        </div>

        {/* Password Input with Eye Toggle */}
        <div className="space-y-1">
          <label htmlFor="login-password" className="block text-xs font-semibold text-slate-300">
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              required
              autoComplete="current-password"
              disabled={authLoading || isUnlocked}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full bg-slate-900/80 border border-slate-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-xl pl-10 pr-10 py-2 text-xs sm:text-sm text-white placeholder:text-slate-500 font-sans transition outline-none disabled:opacity-50"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Remember Me & Forgot Password Row */}
        <div className="flex items-center justify-between text-xs pt-0.5">
          <label className="flex items-center gap-2 cursor-pointer text-slate-400 hover:text-slate-300 select-none">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-3.5 h-3.5 rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-slate-950"
            />
            <span>Remember me</span>
          </label>
          <button
            type="button"
            onClick={() => setShowForgotNotice(!showForgotNotice)}
            className="text-cyan-400 hover:text-cyan-300 font-medium transition"
          >
            Forgot password?
          </button>
        </div>

        {/* Primary Action Button */}
        <button
          type="submit"
          disabled={authLoading || isUnlocked}
          className={`w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-black tracking-wide shadow-2xl transition-all duration-300 flex items-center justify-center gap-2 mt-2 disabled:cursor-not-allowed uppercase ${
            isUnlocked
              ? 'bg-emerald-500 text-white shadow-[0_0_35px_rgba(52,211,153,0.85)]'
              : authLoading
              ? 'bg-cyan-700 text-cyan-100 border border-cyan-400 shadow-[0_0_25px_rgba(6,182,212,0.6)]'
              : 'bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:shadow-[0_0_45px_rgba(168,85,247,0.7)] active:scale-[0.99]'
          }`}
        >
          {isUnlocked ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-white animate-bounce" />
              <span>ACCESS VERIFIED • INITIALIZING...</span>
            </>
          ) : authLoading ? (
            <>
              <span className="w-4 h-4 border-2 border-cyan-200 border-t-transparent rounded-full animate-spin" />
              <span>AUTHENTICATING...</span>
            </>
          ) : (
            <>
              <ArrowRight className="w-4 h-4 text-white" />
              <span>ENTER COMMAND CENTER</span>
            </>
          )}
        </button>

        {/* Distinct 4 Portals: 1 Admin + 3 Unique User Logins */}
        <div className="pt-3 border-t border-slate-800/80 space-y-2">
          <div className="text-[10px] font-mono font-bold text-slate-400 flex items-center justify-between">
            <span className="text-cyan-400">SELECT 1-CLICK AUTH PORTAL:</span>
            <span className="text-[9px] text-slate-400 font-mono">ADMIN + 3 CUSTOMERS</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* 1. Admin Login Portal */}
            <button
              type="button"
              onClick={() => {
                setEmail('admin@fraudlens.internal')
                setPassword('AdminSecure@2026!')
                sound.playBlip()
              }}
              className="p-2.5 rounded-xl bg-slate-900/90 hover:bg-purple-950/70 border border-slate-800 hover:border-purple-500/70 text-slate-300 hover:text-purple-300 transition flex flex-col items-center justify-center text-center gap-1 group shadow-md"
            >
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
                <span className="font-bold text-xs text-white group-hover:text-purple-300 font-mono">Admin</span>
              </div>
              <span className="text-[10px] text-purple-300/80 font-mono">Full Audit Access</span>
            </button>

            {/* 2. User 1: Monisha (Safe Habitual) */}
            <button
              type="button"
              onClick={() => {
                setEmail('monisha@fraudlens.ai')
                setPassword('Customer@1234')
                sound.playBlip()
              }}
              className="p-2.5 rounded-xl bg-slate-900/90 hover:bg-emerald-950/70 border border-slate-800 hover:border-emerald-500/70 text-slate-300 hover:text-emerald-300 transition flex flex-col items-center justify-center text-center gap-1 group shadow-md"
            >
              <div className="flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                <span className="font-bold text-xs text-white group-hover:text-emerald-300 font-mono">Monisha</span>
              </div>
              <span className="text-[10px] text-emerald-400/80 font-mono">User 1 • Safe Account</span>
            </button>

            {/* 3. User 2: Mohana (Elevated Velocity) */}
            <button
              type="button"
              onClick={() => {
                setEmail('mohana@fraudlens.ai')
                setPassword('Customer@1234')
                sound.playBlip()
              }}
              className="p-2.5 rounded-xl bg-slate-900/90 hover:bg-amber-950/70 border border-slate-800 hover:border-amber-500/70 text-slate-300 hover:text-amber-300 transition flex flex-col items-center justify-center text-center gap-1 group shadow-md"
            >
              <div className="flex items-center gap-1.5">
                <User className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                <span className="font-bold text-xs text-white group-hover:text-amber-300 font-mono">Mohana</span>
              </div>
              <span className="text-[10px] text-amber-400/80 font-mono">User 2 • Step-Up OTP</span>
            </button>

            {/* 4. User 3: Sowmiya (Botnet ATO Attack) */}
            <button
              type="button"
              onClick={() => {
                setEmail('sowmiya@fraudlens.ai')
                setPassword('Customer@1234')
                sound.playBlip()
              }}
              className="p-2.5 rounded-xl bg-slate-900/90 hover:bg-rose-950/70 border border-slate-800 hover:border-rose-500/70 text-slate-300 hover:text-rose-300 transition flex flex-col items-center justify-center text-center gap-1 group shadow-md"
            >
              <div className="flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-400 group-hover:scale-110 transition-transform" />
                <span className="font-bold text-xs text-white group-hover:text-rose-300 font-mono">Sowmiya</span>
              </div>
              <span className="text-[10px] text-rose-400/80 font-mono">User 3 • ATO Defense</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
