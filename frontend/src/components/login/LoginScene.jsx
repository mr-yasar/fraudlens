import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  ShieldCheck,
  Volume2,
  VolumeX,
  Activity,
  CheckCircle2,
  Lock,
  Unlock,
} from 'lucide-react'
import LiveCyberParticles from './LiveCyberParticles'
import InteractiveShieldOverlay from './InteractiveShieldOverlay'
import LoginCard from './LoginCard'
import { sound } from './soundEffects'

/**
 * LoginScene - Uses the cinematic reference image as the main full-screen hero visual,
 * with real interactive React login UI, live cybernetic overlays, audio feedback,
 * and a 2-second forward-zoom transition into the Dashboard.
 */
export default function LoginScene({
  onLoginSuccess,
  login,
  register,
  authLoading,
  authError,
  isConnected,
  latency,
}) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 })
  const [isMuted, setIsMuted] = useState(() => sound.getMuted())

  // Sequence state machine:
  // 'IDLE' | 'AUTHENTICATING' | 'VERIFIED' | 'SHIELD_UNLOCK' | 'SYSTEM_HANDOFF' | 'ENERGY_PULSE' | 'COMMAND_CENTER_OPEN'
  const [sequenceStage, setSequenceStage] = useState('IDLE')
  const [isUnlocked, setIsUnlocked] = useState(false)

  const animRef = useRef(null)
  const targetOffset = useRef({ x: 0, y: 0 })

  const handleMouseMove = useCallback((e) => {
    const { innerWidth, innerHeight } = window
    const x = (e.clientX / innerWidth) * 2 - 1
    const y = (e.clientY / innerHeight) * 2 - 1
    targetOffset.current = { x: x * 0.6, y: y * 0.6 }

    if (!animRef.current) {
      animRef.current = requestAnimationFrame(() => {
        setMouseOffset(targetOffset.current)
        animRef.current = null
      })
    }
  }, [])

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
  }, [handleMouseMove])

  const toggleSound = () => {
    const muted = sound.toggleMute()
    setIsMuted(muted)
    if (!muted) sound.playBlip()
  }

  // Real authentication & handoff to SecurityUnlockTransition
  const handleLoginSubmit = async (e) => {
    e?.preventDefault?.()
    if (authLoading) return

    setSequenceStage('AUTHENTICATING')

    try {
      // 1. Await cryptographic authentication from backend
      await login(email, password)
      sound.playVerified()
      // 2. Handoff to SecurityUnlockTransition overlay
      onLoginSuccess && onLoginSuccess()
    } catch {
      sound.playError()
      setSequenceStage('IDLE')
      setIsUnlocked(false)
    }
  }

  // Real registration & handoff to SecurityUnlockTransition
  const handleRegisterSubmit = async (e) => {
    e?.preventDefault?.()
    if (authLoading) return

    setSequenceStage('AUTHENTICATING')

    try {
      await register(name, email, password)
      sound.playVerified()
      onLoginSuccess && onLoginSuccess()
    } catch {
      sound.playError()
      setSequenceStage('IDLE')
      setIsUnlocked(false)
    }
  }

  const isZooming = sequenceStage === 'COMMAND_CENTER_OPEN' || sequenceStage === 'ENERGY_PULSE'

  return (
    <div className="relative min-h-screen w-full bg-slate-950 text-slate-100 flex flex-col justify-between overflow-hidden select-none">
      {/* =========================================================================
          1. MAIN FULL-SCREEN HERO BACKGROUND IMAGE (Ultra-Sharp 4K WebP / JPG)
          ========================================================================= */}
      <div className="absolute inset-0 overflow-hidden z-0">
        <picture className="w-full h-full">
          <source srcSet="/command_center_bg.webp" type="image/webp" />
          <img
            src="/command_center_bg.jpg"
            alt="FraudLens AI Financial Security Command Center"
            className="w-full h-full object-cover object-center pointer-events-none select-none"
            style={{
              transformOrigin: '36.3% 47.2%',
              transform: isZooming
                ? 'scale(3.2)'
                : `scale(1.02) translate(${mouseOffset.x * -6}px, ${mouseOffset.y * -6}px)`,
              filter: isZooming
                ? 'brightness(1.5) contrast(1.1) blur(2px)'
                : 'brightness(1) blur(0px)',
              transition: isZooming
                ? 'transform 1.8s cubic-bezier(0.12, 0.8, 0.32, 1), filter 1.8s ease-in'
                : 'transform 0.5s ease-out',
            }}
          />
        </picture>

        {/* Subtle dark gradient overlay to ensure perfect contrast while preserving background vibrance */}
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950/20 via-transparent to-slate-950/30 pointer-events-none" />
      </div>

      {/* =========================================================================
          2. LIVE SUBTLE CYBER PARTICLES & SCAN LINE OVERLAY
          ========================================================================= */}
      <LiveCyberParticles
        mouseOffset={mouseOffset}
        isHyperSpeed={sequenceStage === 'SYSTEM_HANDOFF' || sequenceStage === 'ENERGY_PULSE' || sequenceStage === 'COMMAND_CENTER_OPEN'}
      />

      {/* =========================================================================
          3. INTERACTIVE SHIELD OVERLAY (AI Security Core Center-Left)
          ========================================================================= */}
      <div className="hidden md:block">
        <InteractiveShieldOverlay
          sequenceStage={sequenceStage}
          isUnlocked={isUnlocked}
        />
      </div>

      {/* =========================================================================
          4. TOP RIGHT CONTROLS & STATUS BAR
          ========================================================================= */}
      <header className="relative z-30 px-6 sm:px-10 py-4 flex items-center justify-end pointer-events-auto">
        <div className="flex items-center space-x-3 bg-slate-950/75 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-cyan-500/40 shadow-lg">
          {/* Audio Synthesizer Toggle */}
          <button
            onClick={toggleSound}
            className={`p-1.5 rounded-full text-xs font-mono transition flex items-center gap-1.5 ${
              isMuted
                ? 'text-slate-500 hover:text-slate-300'
                : 'text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.5)]'
            }`}
            title={isMuted ? 'Unmute Audio Synthesizer' : 'Mute Audio Synthesizer'}
            aria-label={isMuted ? 'Unmute Audio Synthesizer' : 'Mute Audio Synthesizer'}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            <span className="hidden sm:inline text-[10px] uppercase font-bold">{isMuted ? 'Muted' : 'Sound ON'}</span>
          </button>

          <span className="text-slate-700">|</span>

          {/* Backend Connectivity Status Badge */}
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]' : 'bg-rose-500'
              }`}
            />
            <span className="font-semibold text-slate-300 text-[11px]">
              {isConnected ? `Online (${latency || 42}ms)` : 'Connecting...'}
            </span>
          </div>
        </div>
      </header>

      {/* =========================================================================
          5. MAIN CONTENT COMPOSITION (Right: Real Interactive Login Panel)
          ========================================================================= */}
      <main className="relative z-20 flex-1 w-full px-4 sm:px-8 py-3 flex items-center justify-center lg:justify-end">
        <LoginCard
          name={name}
          setName={setName}
          email={email}
          setEmail={setEmail}
          password={password}
          setPassword={setPassword}
          onSubmit={handleLoginSubmit}
          onRegister={handleRegisterSubmit}
          authLoading={authLoading || sequenceStage === 'AUTHENTICATING'}
          authError={authError}
          isUnlocked={isUnlocked}
          sequenceStage={sequenceStage}
        />
      </main>

      {/* =========================================================================
          6. MULTI-PHASE CINEMATIC TRANSITION OVERLAY
          ========================================================================= */}
      {sequenceStage !== 'IDLE' && sequenceStage !== 'AUTHENTICATING' && (
        <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center">
          {/* Expanding Energy Pulse Shockwave Originating from Security Core */}
          {(sequenceStage === 'ENERGY_PULSE' || sequenceStage === 'COMMAND_CENTER_OPEN') && (
            <div
              className="absolute pointer-events-none flex items-center justify-center -translate-x-1/2 -translate-y-1/2"
              style={{ left: '36.3%', top: '47.2%' }}
            >
              <div className="absolute w-64 h-64 rounded-full border-4 border-cyan-400 shadow-[0_0_150px_rgba(6,182,212,1)] animate-shockwave" />
              <div className="absolute w-64 h-64 rounded-full border-2 border-emerald-400 shadow-[0_0_100px_rgba(52,211,153,1)] animate-shockwave [animation-delay:150ms]" />
              <div className="fixed inset-0 bg-cyan-500/15 backdrop-blur-xs animate-pulse" />
            </div>
          )}

          {/* Access Verified Floating HUD Banner */}
          <div className="relative px-8 py-5 rounded-3xl bg-slate-950/90 border-2 border-emerald-400/80 backdrop-blur-2xl shadow-[0_0_60px_rgba(52,211,153,0.6)] flex items-center gap-4.5 animate-bounce">
            <div className="p-3.5 rounded-full bg-emerald-500/20 border border-emerald-400 text-emerald-300 shadow-[0_0_25px_rgba(52,211,153,0.9)]">
              <CheckCircle2 className="w-9 h-9" />
            </div>
            <div>
              <div className="text-xs font-mono font-bold tracking-widest text-emerald-400 uppercase">
                {sequenceStage === 'SYSTEM_HANDOFF'
                  ? 'SECURITY VERIFIED • INITIALIZING COMMAND CENTER'
                  : sequenceStage === 'ENERGY_PULSE' || sequenceStage === 'COMMAND_CENTER_OPEN'
                  ? 'COMMAND CENTER ACTIVATED • DECRYPTING TELEMETRY'
                  : 'CRYPTOGRAPHIC ACCESS VERIFIED ✓'}
              </div>
              <h3 className="text-2xl font-black text-white tracking-tight">
                Entering FraudLens AI Command Center
              </h3>
              <p className="text-xs font-mono text-slate-300">
                Session Token Issued • Launching Multi-Model Fraud Defense Systems...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Spacer to preserve bottom HUD branding */}
      <div className="h-4 pointer-events-none" />
    </div>
  )
}
