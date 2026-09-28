import React, { useEffect, useState } from 'react'
import { ShieldCheck, Lock, CheckCircle2, ShieldAlert, Cpu } from 'lucide-react'
import { sound } from '../login/soundEffects'
import { resetWelcomeVoiceCache } from '../../utils/welcomeVoice'

/**
 * SecurityLogoutDoor
 *
 * Premium 2.8s Cybersecurity Digital Vault Door & Secure Session Lockdown.
 * Visually communicates a high-assurance session termination with dual sliding
 * metallic security panels, cryptographic lock clamping, laser telemetry scan,
 * and optional subtle electronic lock sound.
 */
export default function SecurityLogoutDoor({ onComplete, userName = 'Operator' }) {
  // Sequence stage: 0 = INIT, 1 = SCANNING, 2 = CLOSING_DOORS, 3 = LOCKED, 4 = SECURED
  const [stage, setStage] = useState(0)
  const [isFadingOut, setIsFadingOut] = useState(false)

  useEffect(() => {
    // Reset welcome voice cache on logout so subsequent logins can trigger voice cleanly
    resetWelcomeVoiceCache()

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      sound.playVaultLock()
      const reducedTimer = setTimeout(() => {
        onComplete && onComplete()
      }, 850)
      return () => clearTimeout(reducedTimer)
    }

    // Sequence timing
    // 0.0s - Init & Scan sound
    sound.playDoorScan()
    setStage(1) // Scanning

    // 0.6s - Doors start closing
    const t1 = setTimeout(() => {
      setStage(2) // Closing panels
    }, 600)

    // 1.6s - Lock mechanism snaps shut
    const t2 = setTimeout(() => {
      setStage(3) // Locked
      sound.playVaultLock()
    }, 1600)

    // 2.3s - Verified Session Secured
    const t3 = setTimeout(() => {
      setStage(4) // Secured
      sound.playSecureExit()
    }, 2300)

    // 2.75s - Fade out
    const t4 = setTimeout(() => {
      setIsFadingOut(true)
    }, 2750)

    // 2.95s - Finish and trigger logout callback
    const t5 = setTimeout(() => {
      onComplete && onComplete()
    }, 2950)

    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      clearTimeout(t3)
      clearTimeout(t4)
      clearTimeout(t5)
    }
  }, [onComplete])

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`fixed inset-0 z-50 flex items-center justify-center select-none bg-slate-950/95 backdrop-blur-2xl transition-all duration-300 ease-out ${
        isFadingOut ? 'opacity-0 scale-105' : 'opacity-100 scale-100'
      }`}
    >
      {/* Background Cyber Grid & Vignette */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
      <div className="absolute inset-0 bg-radial-gradient from-transparent via-slate-950/60 to-slate-950 pointer-events-none" />

      {/* Central Security Vault Door Assembly */}
      <div className="relative z-10 w-[92vw] max-w-lg mx-auto flex flex-col items-center">
        {/* Top Telemetry HUD Status */}
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/90 border border-slate-700/80 text-[10px] font-mono font-bold uppercase tracking-widest text-cyan-300 shadow-lg">
            <span
              className={`w-2 h-2 rounded-full ${
                stage === 4
                  ? 'bg-emerald-400'
                  : stage >= 2
                  ? 'bg-rose-500 animate-pulse'
                  : 'bg-cyan-400 animate-ping'
              }`}
            />
            {stage === 4
              ? 'SESSION SECURED • ENCLAVE LOCKED'
              : stage === 3
              ? 'SEALING CRYPTOGRAPHIC VAULT'
              : stage === 2
              ? 'CLOSING HARDWARE GATES'
              : 'SECURING ACTIVE SESSION...'}
          </div>
        </div>

        {/* Digital Vault Door Housing */}
        <div className="relative w-full h-72 sm:h-80 rounded-3xl bg-slate-900/90 border-2 border-slate-700/80 shadow-[0_0_60px_rgba(0,0,0,0.9),0_0_30px_rgba(6,182,212,0.2)] overflow-hidden flex items-center justify-center p-3">
          {/* Neon Corner Brackets */}
          <div className="absolute top-2 left-2 w-5 h-5 border-t-2 border-l-2 border-cyan-400 rounded-tl-lg pointer-events-none" />
          <div className="absolute top-2 right-2 w-5 h-5 border-t-2 border-r-2 border-cyan-400 rounded-tr-lg pointer-events-none" />
          <div className="absolute bottom-2 left-2 w-5 h-5 border-b-2 border-l-2 border-cyan-400 rounded-bl-lg pointer-events-none" />
          <div className="absolute bottom-2 right-2 w-5 h-5 border-b-2 border-r-2 border-cyan-400 rounded-br-lg pointer-events-none" />

          {/* Left Metallic Security Shutter Panel */}
          <div
            className={`absolute top-2 bottom-2 left-2 w-[calc(50%-8px)] rounded-l-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-y border-l border-slate-700 shadow-2xl transition-transform duration-700 ease-in-out flex flex-col justify-between p-4 overflow-hidden ${
              stage >= 2 ? 'translate-x-0' : '-translate-x-full'
            }`}
          >
            {/* Texture Lines */}
            <div className="space-y-2 opacity-30">
              <div className="h-0.5 bg-cyan-400 w-full" />
              <div className="h-0.5 bg-slate-600 w-3/4" />
              <div className="h-0.5 bg-slate-600 w-1/2" />
            </div>
            <div className="font-mono text-[9px] text-slate-400 uppercase tracking-widest">
              VAULT-L // ISOLATION
            </div>
          </div>

          {/* Right Metallic Security Shutter Panel */}
          <div
            className={`absolute top-2 bottom-2 right-2 w-[calc(50%-8px)] rounded-r-2xl bg-gradient-to-l from-slate-900 via-slate-800 to-slate-900 border-y border-r border-slate-700 shadow-2xl transition-transform duration-700 ease-in-out flex flex-col justify-between items-end p-4 overflow-hidden ${
              stage >= 2 ? 'translate-x-0' : 'translate-x-full'
            }`}
          >
            {/* Texture Lines */}
            <div className="space-y-2 opacity-30 w-full flex flex-col items-end">
              <div className="h-0.5 bg-cyan-400 w-full" />
              <div className="h-0.5 bg-slate-600 w-3/4" />
              <div className="h-0.5 bg-slate-600 w-1/2" />
            </div>
            <div className="font-mono text-[9px] text-slate-400 uppercase tracking-widest">
              VAULT-R // ENCRYPTED
            </div>
          </div>

          {/* Vertical Laser Scan Beam Line */}
          {stage === 1 && (
            <div className="absolute inset-y-0 w-1 bg-gradient-to-b from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] animate-[scan_1.2s_ease-in-out_infinite]" />
          )}

          {/* Center Vault Lock Hub */}
          <div
            className={`relative z-20 flex flex-col items-center justify-center p-6 transition-all duration-500 ${
              stage >= 3 ? 'scale-100 opacity-100' : 'scale-90 opacity-70'
            }`}
          >
            {/* Rotating Outer Ring */}
            <div
              className={`w-24 h-24 sm:w-28 sm:h-28 rounded-full border-2 border-dashed flex items-center justify-center transition-all duration-700 ${
                stage === 4
                  ? 'border-emerald-400/80 shadow-[0_0_35px_rgba(16,185,129,0.5)] rotate-180 bg-emerald-950/40'
                  : stage === 3
                  ? 'border-cyan-400/80 shadow-[0_0_35px_rgba(6,182,212,0.5)] rotate-90 bg-slate-950/90'
                  : 'border-slate-600/60 rotate-0 bg-slate-950/70'
              }`}
            >
              {/* Inner Core */}
              <div
                className={`w-16 h-16 sm:w-18 sm:h-18 rounded-full flex items-center justify-center border transition-all duration-500 ${
                  stage === 4
                    ? 'bg-emerald-900/80 border-emerald-400 text-emerald-300'
                    : stage === 3
                    ? 'bg-cyan-950/90 border-cyan-400 text-cyan-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                {stage === 4 ? (
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 animate-bounce" />
                ) : stage >= 3 ? (
                  <Lock className="w-8 h-8 text-cyan-300 animate-pulse" />
                ) : (
                  <Cpu className="w-8 h-8 text-slate-400 animate-spin" />
                )}
              </div>
            </div>

            {/* Lock Status Text */}
            <div className="mt-4 text-center">
              <h2 className="text-base sm:text-lg font-black text-white tracking-tight uppercase font-mono">
                {stage === 4 ? 'Session Secured' : 'Locking Vault'}
              </h2>
              <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                {stage === 4
                  ? `Cryptographic tokens purged • Goodbye, ${userName}`
                  : 'Terminating enclave bindings & zeroing memory'}
              </p>
            </div>
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="w-48 h-1 rounded-full bg-slate-800 mt-5 overflow-hidden border border-slate-700/60">
          <div
            className={`h-full transition-all duration-[2400ms] ease-out ${
              stage === 4 ? 'bg-emerald-400 w-full' : 'bg-cyan-400 w-4/5'
            }`}
          />
        </div>
      </div>
    </div>
  )
}
