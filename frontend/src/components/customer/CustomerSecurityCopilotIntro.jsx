import React, { useState, useRef, useEffect } from 'react'
import {
  ShieldCheck,
  Sparkles,
  ArrowRight,
  AlertTriangle,
  Lock,
  Activity,
  Maximize2,
  Minimize2,
  X,
} from 'lucide-react'

/**
 * CustomerSecurityCopilotIntro.jsx
 * FraudLens AI — Customer Security Copilot Opening Experience
 *
 * Visual Language adapted from Vesper specification:
 * - Pure-black foundation (#000000 / #07080b)
 * - Restrained silver / liquid-metal surfaces & buttons
 * - High-contrast typography with serif italic accent
 * - Staggered entrance motion with cubic-bezier easing
 * - Prefers-reduced-motion fallback
 * - Integrated local Gemini video (/gemini_generated_video_ac9e89b9.mp4) with poster fallback
 * - Thumb-friendly, accessible controls and responsive layout
 */
export default function CustomerSecurityCopilotIntro({
  customerName = 'Valued Customer',
  _customerPersona = null,
  onStartConversation,
  onSelectSuggestion,
  _recentTransactions = [],
  flaggedTx = null,
  isMaximized = true,
  onToggleMaximize,
  onClose,
}) {
  const videoRef = useRef(null)
  const [videoLoaded, setVideoLoaded] = useState(false)
  const [videoError, setVideoError] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    }
    return false
  })

  // Listen for reduced motion preference changes
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
      const listener = (e) => setPrefersReducedMotion(e.matches)
      mediaQuery.addEventListener?.('change', listener)
      return () => mediaQuery.removeEventListener?.('change', listener)
    }
  }, [])

  // Safely manage video autoplay
  useEffect(() => {
    if (prefersReducedMotion && videoRef.current) {
      videoRef.current.pause()
    } else if (videoRef.current && !videoError) {
      videoRef.current.play().catch(() => {
        // Autoplay may be restricted by browser policy; poster remains visible
      })
    }
  }, [prefersReducedMotion, videoError])

  const suggestedPrompts = [
    {
      id: 'why_flagged',
      label: 'Why was a transaction flagged?',
      description: 'Explain security hold factors and verification checkpoints',
      query: 'Why was a transaction flagged on my account?',
      icon: AlertTriangle,
      tag: 'Risk Insight',
    },
    {
      id: 'check_activity',
      label: 'Check my recent activity',
      description: 'Audit authorized payments and real-time settlement status',
      query: 'Check my recent activity and verify my transactions.',
      icon: Activity,
      tag: 'Audit Stream',
    },
    {
      id: 'account_secure',
      label: 'Is my account secure right now?',
      description: 'Inspect active pre-auth neural defense and account standing',
      query: 'Is my account secure right now?',
      icon: ShieldCheck,
      tag: 'Defense Health',
    },
    {
      id: 'report_suspicious',
      label: 'Report suspicious activity',
      description: 'Trigger autonomous transaction freeze and SOC review',
      query: 'I want to report suspicious activity or an unauthorized charge.',
      icon: Lock,
      tag: 'Dispute Action',
    },
  ]

  return (
    <div className="relative w-full h-full flex flex-col justify-between overflow-hidden bg-[#050608] text-white rounded-[28px] sm:rounded-[32px] border border-white/10 shadow-[0_30px_90px_rgba(0,0,0,0.85)]">
      {/* ── Scoped Keyframe Animations ── */}
      <style>{`
        @keyframes vesperStaggerIn {
          from {
            opacity: 0;
            transform: translateY(16px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-vesper-stagger-1 {
          animation: vesperStaggerIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.05s both;
        }
        .animate-vesper-stagger-2 {
          animation: vesperStaggerIn 0.75s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both;
        }
        .animate-vesper-stagger-3 {
          animation: vesperStaggerIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.25s both;
        }
        .animate-vesper-stagger-4 {
          animation: vesperStaggerIn 0.85s cubic-bezier(0.16, 1, 0.3, 1) 0.35s both;
        }
        .animate-vesper-stagger-5 {
          animation: vesperStaggerIn 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.45s both;
        }
        @media (prefers-reduced-motion: reduce) {
          .animate-vesper-stagger-1,
          .animate-vesper-stagger-2,
          .animate-vesper-stagger-3,
          .animate-vesper-stagger-4,
          .animate-vesper-stagger-5 {
            animation: none !important;
            opacity: 1 !important;
            transform: none !important;
          }
        }
      `}</style>

      {/* ── Background Media Layer (Gemini Video + Poster + Gradients) ── */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none">
        {/* Poster Image (Immediate First-Paint Fallback) */}
        <img
          src="/copilot_video_poster.jpg"
          alt=""
          aria-hidden="true"
          className={`absolute inset-0 w-full h-full object-cover object-center transition-opacity duration-1000 ${
            videoLoaded ? 'opacity-10' : 'opacity-25'
          }`}
          style={{ filter: 'blur(4px)' }}
        />

        {/* Local Gemini Video Loop (Ambient Cinematic Backdrop) */}
        {!videoError && (
          <video
            ref={videoRef}
            src="/gemini_generated_video_ac9e89b9.mp4"
            poster="/copilot_video_poster.jpg"
            autoPlay
            loop
            muted
            playsInline
            preload="metadata"
            aria-hidden="true"
            onLoadedData={() => setVideoLoaded(true)}
            onError={() => setVideoError(true)}
            className="absolute inset-0 w-full h-full object-cover object-center opacity-20 mix-blend-screen pointer-events-none transition-opacity duration-1000"
            style={{ filter: 'blur(3px)' }}
          />
        )}

        {/* Deep Vignette & Dark Radial Gradients for Pristine Contrast */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#050608]/95 via-[#07090e]/85 to-[#050608]/98" />
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'radial-gradient(circle at 50% 30%, rgba(20, 184, 166, 0.12) 0%, rgba(5, 6, 8, 0) 70%)',
          }}
        />
        {/* Subtle Liquid Edge Highlight */}
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      </div>

      {/* ── Top Bar: Brand Identifier & Window Controls ── */}
      <div className="relative z-20 flex items-center justify-between px-6 py-5 border-b border-white/[0.08] bg-[#050608]/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          {/* Brand "F" Liquid Badge */}
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-white/20 via-white/5 to-transparent p-px border border-white/20 shadow-sm flex items-center justify-center">
            <div className="w-full h-full rounded-[11px] bg-[#090b10] flex items-center justify-center">
              <span className="font-black text-sm bg-gradient-to-br from-emerald-400 via-teal-300 to-cyan-200 bg-clip-text text-transparent">
                F
              </span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase">
                FraudLens AI
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] font-mono text-emerald-400 font-semibold">Active</span>
            </div>
            <div className="text-xs font-semibold text-slate-200">
              Personal Security Copilot
            </div>
          </div>
        </div>

        {/* Window Controls */}
        <div className="flex items-center gap-2">
          {onToggleMaximize && (
            <button
              onClick={onToggleMaximize}
              className="p-2 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-slate-300 hover:text-white border border-white/10 transition"
              title={isMaximized ? 'Restore Panel' : 'Maximize Panel'}
              aria-label="Toggle size"
            >
              {isMaximized ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </button>
          )}

          {onClose && (
            <button
              onClick={onClose}
              className="p-2 rounded-full bg-white/[0.06] hover:bg-rose-500/80 hover:text-white text-slate-300 border border-white/10 transition"
              title="Close Copilot"
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* ── Main Content Hero Section (Centered & Restrained) ── */}
      <div className="relative z-10 flex-1 flex flex-col justify-center items-center text-center px-6 sm:px-12 py-8 overflow-y-auto">
        <div className="max-w-2xl w-full mx-auto space-y-6">
          
          {/* Eyebrow / Badge */}
          <div className="animate-vesper-stagger-1 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.05] border border-white/15 backdrop-blur-md shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
            <span className="text-[11px] font-extrabold tracking-[0.18em] text-slate-200 uppercase">
              FRAUDLENS SECURITY COPILOT
            </span>
          </div>

          {/* Main Heading */}
          <div className="animate-vesper-stagger-2 space-y-2">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-[1.12]">
              Understand your transactions.{' '}
              <span className="font-serif italic font-normal text-slate-300 block sm:inline">
                Stay ahead of fraud.
              </span>
            </h1>
          </div>

          {/* Supporting Copy */}
          <p className="animate-vesper-stagger-3 text-sm sm:text-base text-slate-400 font-normal leading-relaxed max-w-xl mx-auto">
            Get clear explanations of transaction risk, account activity, and security alerts through your personalized security assistant.
          </p>

          {/* Live Customer Personalization Context */}
          <div className="animate-vesper-stagger-3 flex items-center justify-center gap-2 text-xs text-slate-400 pt-1">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#10141f] border border-white/10 text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
              <span>Grounded account: <strong className="text-white font-semibold">{customerName}</strong></span>
            </span>
            {flaggedTx && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-950/60 border border-amber-600/40 text-amber-300">
                <AlertTriangle className="w-3 h-3 text-amber-400" />
                <span>1 review item available</span>
              </span>
            )}
          </div>

          {/* Primary Action Button (Liquid-Metal Silver Primary) */}
          <div className="animate-vesper-stagger-4 pt-2">
            <button
              onClick={onStartConversation}
              className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 rounded-full font-bold text-sm tracking-wide text-slate-950 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-[0_10px_35px_rgba(255,255,255,0.18),inset_0_1px_0_rgba(255,255,255,0.95)]"
              style={{
                background: 'linear-gradient(180deg, #FFFFFF 0%, #D4D8E0 100%)',
                border: '1px solid rgba(255, 255, 255, 0.9)',
              }}
            >
              {/* Highlight sweep effect */}
              <span className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
              
              <Sparkles className="w-4 h-4 text-slate-900 group-hover:rotate-12 transition-transform duration-300" />
              <span>Start Conversation</span>
              <ArrowRight className="w-4 h-4 text-slate-900 transform group-hover:translate-x-1 transition-transform duration-300" />
            </button>
          </div>

          {/* Suggested Questions Grid (Liquid-Metal Graphite Glass) */}
          <div className="animate-vesper-stagger-5 pt-4 space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 px-1">
              <span>EXPLORE SUGGESTED QUESTIONS</span>
              <span className="text-[10px] font-mono text-slate-500">Instant RAG Grounding</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left">
              {suggestedPrompts.map((item) => {
                const IconComponent = item.icon
                return (
                  <button
                    key={item.id}
                    onClick={() => onSelectSuggestion(item.query)}
                    className="group relative p-3.5 rounded-2xl bg-white/[0.04] hover:bg-white/[0.09] border border-white/10 hover:border-white/25 transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0 text-left flex items-start gap-3 cursor-pointer shadow-[0_4px_16px_rgba(0,0,0,0.3)] backdrop-blur-sm"
                  >
                    <div className="p-2 rounded-xl bg-white/[0.06] border border-white/10 text-slate-300 group-hover:text-teal-300 group-hover:bg-teal-950/40 transition shrink-0 mt-0.5">
                      <IconComponent className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-1">
                        <span className="text-xs font-bold text-white group-hover:text-teal-200 transition truncate">
                          {item.label}
                        </span>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-400 group-hover:text-slate-300 border border-white/5 shrink-0">
                          {item.tag}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 group-hover:text-slate-300 transition line-clamp-1 pt-0.5">
                        {item.description}
                      </p>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-white shrink-0 mt-2 transform group-hover:translate-x-0.5 transition-transform" />
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Ambient Footer ── */}
      <div className="relative z-10 px-6 py-3 border-t border-white/[0.06] bg-[#050608]/60 backdrop-blur-md flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
          <span>Server-Enforced Isolation & Zero Cross-Customer Leakage</span>
        </div>
        <div className="font-mono text-[10px] text-slate-500 hidden sm:block">
          FraudLens Pre-Auth Defense • Grounded RAG
        </div>
      </div>
    </div>
  )
}
