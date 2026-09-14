import React from 'react'
import { Unlock } from 'lucide-react'

/**
 * InteractiveShieldOverlay - Perfectly aligns with the central AI Security Core
 * shield (34.2% X, 47% Y) of the cinematic background.
 *
 * - Idle: Preserves the background artwork's glowing shield, adding a subtle rotating
 *   holographic targeting reticle and a status indicator pill.
 * - Authenticating: Accelerates reticle rotation, activates vertical laser scan lines.
 * - Verified / Unlocking: Detonates radiant emerald pulse, reveals glowing unlock emblem,
 *   and announces core activation.
 * - Zooming: Dissolves into blinding light as camera pushes through the portal.
 */
export default function InteractiveShieldOverlay({
  sequenceStage = 'IDLE',
  isUnlocked = false,
}) {
  const isAuthenticating = sequenceStage === 'AUTHENTICATING'
  const isUnlocking =
    sequenceStage === 'VERIFIED' ||
    sequenceStage === 'SHIELD_UNLOCK' ||
    sequenceStage === 'SYSTEM_HANDOFF' ||
    sequenceStage === 'ENERGY_PULSE'
  const isZooming = sequenceStage === 'COMMAND_CENTER_OPEN'

  return (
    <div
      className={`absolute top-[47.2%] left-[36.3%] -translate-x-1/2 -translate-y-1/2 z-20 pointer-events-none flex flex-col items-center justify-center transition-all duration-700 ${
        isZooming ? 'scale-150 opacity-0 blur-md' : 'scale-100 opacity-100'
      }`}
    >
      {/* 1. Shield Atmospheric Glow Aura */}
      <div
        className={`w-36 sm:w-44 h-36 sm:h-44 rounded-full filter blur-2xl transition-all duration-700 ${
          isUnlocked
            ? 'bg-emerald-400/50 scale-150'
            : isAuthenticating
            ? 'bg-cyan-400/40 scale-125'
            : 'bg-cyan-500/20 scale-100'
        }`}
      />

      {/* 2. Interactive Holographic Reticle Rings */}
      <div className="relative flex items-center justify-center w-28 h-28 sm:w-32 sm:h-32">
        {/* Outer Rotating Dashed Targeting Ring */}
        <div
          className={`absolute inset-0 rounded-full border border-dashed transition-all duration-500 ${
            isUnlocked
              ? 'border-emerald-400 shadow-[0_0_35px_rgba(52,211,153,0.9)] animate-ping'
              : isAuthenticating
              ? 'border-cyan-400 animate-radar-spin shadow-[0_0_20px_rgba(6,182,212,0.8)]'
              : 'border-cyan-400/40 animate-radar-spin'
          }`}
          style={{ animationDuration: isAuthenticating ? '4s' : '18s' }}
        />

        {/* Inner Counter-Rotating Reticle */}
        <div
          className={`absolute inset-2 rounded-full border transition-all duration-500 ${
            isUnlocked
              ? 'border-emerald-300'
              : isAuthenticating
              ? 'border-cyan-300/80 animate-radar-spin-reverse'
              : 'border-cyan-500/20 animate-radar-spin-reverse'
          }`}
          style={{ animationDuration: isAuthenticating ? '5s' : '24s' }}
        />

        {/* Authenticating Vertical Scanning Beam */}
        {isAuthenticating && (
          <div className="absolute inset-x-2 h-1 bg-gradient-to-r from-transparent via-cyan-300 to-transparent shadow-[0_0_15px_#22d3ee] animate-beam-scan" />
        )}

        {/* Unlocked Emerald Holographic Emblem (Appears ONLY on successful verification) */}
        {isUnlocked && (
          <div className="p-3 sm:p-4 rounded-full bg-slate-950/90 border-2 border-emerald-400 shadow-[0_0_35px_rgba(52,211,153,1)] animate-bounce z-10">
            <Unlock className="w-8 h-8 sm:w-9 sm:h-9 text-emerald-300 drop-shadow-[0_0_12px_#34d399]" />
          </div>
        )}
      </div>

      {/* 3. Status Capsule Pill Underneath Shield */}
      <div className="mt-4 px-3.5 py-1 rounded-full bg-slate-950/90 border border-cyan-500/50 backdrop-blur-md shadow-[0_0_20px_rgba(6,182,212,0.3)] flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            isUnlocked
              ? 'bg-emerald-400 shadow-[0_0_10px_#34d399]'
              : isAuthenticating
              ? 'bg-amber-400 animate-ping shadow-[0_0_8px_#f59e0b]'
              : 'bg-cyan-400 shadow-[0_0_8px_#22d3ee]'
          }`}
        />
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-200">
          {isUnlocked
            ? 'CORE UNLOCKED • ACCESS GRANTED'
            : isAuthenticating
            ? 'VERIFYING CIPHERS...'
            : 'AI NEURAL SHIELD • LOCKED 🔒'}
        </span>
      </div>
    </div>
  )
}
