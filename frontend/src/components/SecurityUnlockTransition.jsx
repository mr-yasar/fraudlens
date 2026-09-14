import React, { useState, useEffect, useRef } from 'react'
import {
  Lock,
  Unlock,
  ShieldCheck,
  CheckCircle2,
  Cpu,
  Sparkles,
  Activity,
} from 'lucide-react'

/**
 * SecurityUnlockTransition
 *
 * Cinematic 5-phase security access transition from successful login into the
 * existing FraudLens AI Command Center Dashboard (Total duration: 1.7s).
 *
 * Timeline:
 * - Phase 1 (0.0s - 0.3s): Futuristic Security Lock (🔒), HUD rings, "SECURITY ACCESS - AUTHENTICATING..."
 * - Phase 2 (0.3s - 0.6s): Laser scan beam sweep, checkmark energy pulse, "ACCESS VERIFIED"
 * - Phase 3 (0.6s - 0.9s): Mechanical + holographic unlock (🔓), radial ring burst, "ACCESS GRANTED"
 * - Phase 4 (0.9s - 1.2s): Lock morphs into AI Neural Core / Shield, "AI SECURITY CORE ONLINE"
 * - Phase 5 (1.2s - 1.7s): Dissolve + zoom + HUD expansion, smoothly revealing the real dashboard underneath
 */
export default function SecurityUnlockTransition({ onComplete }) {
  // Phase state: 1 | 2 | 3 | 4 | 5
  const [phase, setPhase] = useState(1)
  const [isFadingOut, setIsFadingOut] = useState(false)
  const timerRef = useRef([])

  useEffect(() => {
    // Accessibility check: prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      const fastTimer = setTimeout(() => {
        onComplete && onComplete()
      }, 300)
      return () => clearTimeout(fastTimer)
    }

    // Phase 1 -> 2: Verification at 320ms
    timerRef.current.push(
      setTimeout(() => {
        setPhase(2)
      }, 320)
    )

    // Phase 2 -> 3: Unlock at 620ms
    timerRef.current.push(
      setTimeout(() => {
        setPhase(3)
      }, 620)
    )

    // Phase 3 -> 4: AI Security Core activation at 950ms
    timerRef.current.push(
      setTimeout(() => {
        setPhase(4)
      }, 950)
    )

    // Phase 4 -> 5: Dashboard reveal begins at 1250ms
    timerRef.current.push(
      setTimeout(() => {
        setPhase(5)
        setIsFadingOut(true)
      }, 1250)
    )

    // Complete transition and unmount at 1720ms
    timerRef.current.push(
      setTimeout(() => {
        onComplete && onComplete()
      }, 1720)
    )

    return () => {
      timerRef.current.forEach((t) => clearTimeout(t))
    }
  }, [onComplete])

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center overflow-hidden transition-all duration-500 ease-out select-none pointer-events-none ${
        isFadingOut ? 'opacity-0 scale-110 blur-sm' : 'opacity-100 scale-100 blur-0'
      }`}
      style={{
        background:
          phase >= 5
            ? 'radial-gradient(circle at 50% 45%, rgba(6, 182, 212, 0.18) 0%, rgba(2, 6, 23, 0.4) 60%, rgba(2, 6, 23, 0.85) 100%)'
            : 'radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.95) 0%, rgba(2, 6, 23, 0.98) 70%, rgba(2, 6, 23, 1) 100%)',
      }}
    >
      {/* Background Cyber Perspective Grid */}
      <div className="absolute inset-0 cyber-grid-floor opacity-30 pointer-events-none" />

      {/* Screen flash pulse on Phase 3 unlock */}
      {phase === 3 && (
        <div className="absolute inset-0 bg-cyan-400/20 animate-pulse pointer-events-none" />
      )}

      {/* Outer Shockwave Energy Expansion on Phase 4 & 5 */}
      {phase >= 4 && (
        <div className="absolute w-[500px] h-[500px] rounded-full border border-cyan-400/40 shadow-[0_0_120px_rgba(6,182,212,0.5)] animate-shockwave pointer-events-none" />
      )}

      {/* Central Holographic Chamber */}
      <div className="relative flex flex-col items-center justify-center text-center px-4 max-w-lg z-10">
        {/* ====================================================================
            HOLOGRAPHIC RETICLE & CENTRAL SECURITY EMBLEM
            ==================================================================== */}
        <div className="relative flex items-center justify-center w-48 h-48 sm:w-56 sm:h-56 mb-8">
          {/* Radial Ambient Glow Aura */}
          <div
            className={`absolute inset-0 rounded-full filter blur-2xl transition-all duration-500 ${
              phase >= 4
                ? 'bg-gradient-to-tr from-cyan-500/40 via-purple-500/30 to-indigo-500/40 scale-125'
                : phase === 3
                ? 'bg-emerald-400/40 scale-120'
                : phase === 2
                ? 'bg-cyan-400/35 scale-110'
                : 'bg-cyan-500/25 scale-100'
            }`}
          />

          {/* HUD Ring 1 - Outermost Dashed Reticle */}
          <div
            className={`absolute inset-0 rounded-full border border-dashed transition-all duration-500 ${
              phase >= 4
                ? 'border-cyan-400/60 shadow-[0_0_30px_rgba(6,182,212,0.5)] animate-radar-spin'
                : phase === 3
                ? 'border-emerald-400 shadow-[0_0_25px_rgba(52,211,153,0.7)] animate-ping'
                : phase === 2
                ? 'border-cyan-400 animate-radar-spin shadow-[0_0_20px_rgba(6,182,212,0.6)]'
                : 'border-cyan-500/40 animate-radar-spin'
            }`}
            style={{ animationDuration: phase >= 2 ? '6s' : '18s' }}
          />

          {/* HUD Ring 2 - Segmented Mid-Ring with Corner Markers */}
          <div
            className={`absolute inset-3 rounded-full border-2 transition-all duration-500 ${
              phase >= 4
                ? 'border-purple-500/50 animate-radar-spin-reverse'
                : phase === 3
                ? 'border-emerald-400/80 scale-105'
                : phase === 2
                ? 'border-cyan-300/80 animate-radar-spin-reverse'
                : 'border-cyan-600/30 animate-radar-spin-reverse'
            }`}
            style={{ animationDuration: phase >= 2 ? '8s' : '24s' }}
          />

          {/* HUD Ring 3 - Circuit Ring with Compass Nodes */}
          <div className="absolute inset-7 rounded-full border border-cyan-400/30 flex items-center justify-center">
            <span className="absolute -top-1 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
            <span className="absolute -bottom-1 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
            <span className="absolute -left-1 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
            <span className="absolute -right-1 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
          </div>

          {/* Horizontal Laser Scanning Beam (Active during Phase 2 Verification) */}
          {phase === 2 && (
            <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyan-300 to-transparent shadow-[0_0_20px_#22d3ee] animate-beam-scan z-20" />
          )}

          {/* Central Holographic Icon Pod */}
          <div
            className={`relative flex items-center justify-center w-24 h-24 sm:w-28 sm:h-28 rounded-3xl backdrop-blur-xl border-2 transition-all duration-500 z-10 ${
              phase >= 4
                ? 'bg-slate-900/90 border-cyan-400 shadow-[0_0_45px_rgba(6,182,212,0.8),inset_0_0_20px_rgba(6,182,212,0.3)] scale-110'
                : phase === 3
                ? 'bg-emerald-950/90 border-emerald-400 shadow-[0_0_40px_rgba(52,211,153,0.9),inset_0_0_20px_rgba(52,211,153,0.3)] scale-105'
                : phase === 2
                ? 'bg-slate-900/90 border-cyan-300 shadow-[0_0_35px_rgba(6,182,212,0.7)] scale-100'
                : 'bg-slate-950/90 border-cyan-500/60 shadow-[0_0_25px_rgba(6,182,212,0.4)] scale-100'
            }`}
          >
            {/* Phase 1: Holographic Locked Icon 🔒 */}
            {phase === 1 && (
              <Lock className="w-10 h-10 sm:w-12 sm:h-12 text-cyan-400 drop-shadow-[0_0_12px_rgba(6,182,212,0.8)] animate-pulse" />
            )}

            {/* Phase 2: Access Verified Checkmark Badge ✓ */}
            {phase === 2 && (
              <div className="flex items-center justify-center animate-bounce">
                <CheckCircle2 className="w-11 h-11 sm:w-13 sm:h-13 text-cyan-300 drop-shadow-[0_0_15px_rgba(34,211,238,1)]" />
              </div>
            )}

            {/* Phase 3: Mechanical Holographic Unlocked 🔓 */}
            {phase === 3 && (
              <Unlock className="w-11 h-11 sm:w-13 sm:h-13 text-emerald-300 drop-shadow-[0_0_16px_rgba(52,211,153,1)] animate-pulse" />
            )}

            {/* Phase 4 & 5: AI Neural Security Core Shield 🛡️ */}
            {phase >= 4 && (
              <div className="relative flex items-center justify-center">
                <ShieldCheck className="w-12 h-12 sm:w-14 sm:h-14 text-cyan-300 drop-shadow-[0_0_18px_rgba(6,182,212,0.9)] animate-pulse" />
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <Sparkles className="w-6 h-6 text-purple-300 animate-spin" style={{ animationDuration: '4s' }} />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ====================================================================
            STATUS TEXT & TELEMETRY STREAM
            ==================================================================== */}
        <div className="space-y-2">
          {/* Main Title Badge */}
          <div className="flex items-center justify-center gap-2">
            <span
              className={`w-2 h-2 rounded-full transition-colors duration-300 ${
                phase >= 4
                  ? 'bg-cyan-400 shadow-[0_0_10px_#22d3ee] animate-pulse'
                  : phase === 3
                  ? 'bg-emerald-400 shadow-[0_0_10px_#34d399]'
                  : phase === 2
                  ? 'bg-cyan-300 shadow-[0_0_8px_#67e8f9]'
                  : 'bg-amber-400 shadow-[0_0_8px_#fbbf24] animate-ping'
              }`}
            />
            <span className="text-[11px] font-mono font-bold uppercase tracking-widest text-cyan-300">
              {phase === 1 && 'SECURITY ACCESS'}
              {phase === 2 && 'SECURITY VERIFICATION'}
              {phase === 3 && 'CLEARANCE APPROVED'}
              {phase >= 4 && 'COMMAND CENTER INITIALIZED'}
            </span>
          </div>

          {/* Primary Cinematic Headline */}
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-none">
            {phase === 1 && 'Authenticating Session'}
            {phase === 2 && 'Access Verified'}
            {phase === 3 && 'Access Granted'}
            {phase >= 4 && 'AI Security Core Online'}
          </h2>

          {/* Subtitle / Telemetry Microcopy */}
          <p className="text-xs sm:text-sm font-mono text-slate-300 max-w-sm">
            {phase === 1 && 'Validating cryptographic tokens & roles...'}
            {phase === 2 && 'Decryption key validated • Security scan passed'}
            {phase === 3 && 'Releasing hardware enclave locks • Opening gate'}
            {phase >= 4 && 'Multi-Model Risk Engine & SHAP Explainability Active'}
          </p>

          {/* Phase 4 AI Subsystems Pill Chips */}
          {phase >= 4 && (
            <div className="flex flex-wrap items-center justify-center gap-2 pt-3">
              <span className="px-2.5 py-1 rounded-full bg-slate-900/80 border border-cyan-500/40 text-[10px] font-mono font-bold text-cyan-300 flex items-center gap-1.5 shadow-sm">
                <Cpu className="w-3 h-3 text-cyan-400" />
                ML INFERENCE
              </span>
              <span className="px-2.5 py-1 rounded-full bg-slate-900/80 border border-purple-500/40 text-[10px] font-mono font-bold text-purple-300 flex items-center gap-1.5 shadow-sm">
                <Activity className="w-3 h-3 text-purple-400" />
                SHAP EXPLAINABILITY
              </span>
              <span className="px-2.5 py-1 rounded-full bg-slate-900/80 border border-emerald-500/40 text-[10px] font-mono font-bold text-emerald-300 flex items-center gap-1.5 shadow-sm">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                FRAUD SHIELD
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
