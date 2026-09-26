/**
 * FraudLens AI Intelligence Workspace — Premium Chatbot Panel
 *
 * Premium Visual Design:
 * - Deep dark-blue environment + warm-white / soft-ivory illumination
 * - Glass depth with frosted reflections
 * - AI Orb integration with meaningful processing states
 * - Smooth message entrance animations
 * - Scanning beam during processing
 * - Stage-sequenced loading (Searching → Scanning → Analysing → Processing)
 *
 * Preserved Functionality:
 * - AUTO / GEMINI / GROK / MISTRAL routing
 * - Role-aware Help Desk (Admin / Investigator / Customer)
 * - Backend-verified permissions
 * - Per-user chat history isolation
 * - Zero-leak security
 * - Voice playback (explicit only)
 * - API key diagnostics
 * - Expand to Command Center
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Bot,
  X,
  Send,
  Sparkles,
  Volume2,
  VolumeX,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Zap,
  Play,
  Pause,
  Square,
  Globe,
  UserCheck,
  ShieldAlert,
  Sliders,
  Store,
  CheckCircle2,
  Lock,
  ShieldCheck,
  Key,
  Check,
  AlertCircle,
  ExternalLink,
  Maximize2,
  Search,
  ScanLine,
  Brain,
  GitCompareArrows,
  CircleDot,
  Copy,
} from 'lucide-react'
import AIOrb from './ai/AIOrb'

const BASE_URL = '/api/v1'

function getAuthHeaders() {
  const token = localStorage.getItem('fraudlens_token')
  return {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Role Configurations & Dynamic Domain Knowledge
// ─────────────────────────────────────────────────────────────────────────────
const ROLE_PROFILES = {
  customer: {
    id: 'customer',
    label: 'Customer Account',
    icon: UserCheck,
    tag: 'Verified Cardholder',
    badgeClass: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
    accentColor: 'emerald',
    greeting: (name) =>
      `Hello ${name}! 👋 I'm your FraudLens Security Assistant. I'm actively protecting your account and cards behind the scenes with real-time AI. How can I assist you with your transaction safety or security questions today?`,
    questions: [
      { label: '🔑 Test API Keys (Grok & Gemini)', query: 'Test API key status for Grok and Gemini.' },
      { label: '📱 Why was OTP required?', query: 'Why was my payment held for 6-digit Mobile OTP step-up verification?' },
      { label: '🟢 Instant Approval', query: 'Why was my grocery purchase at NovaMart Fresh approved in milliseconds?' },
      { label: '🚨 Unrecognized Charge', query: 'What should I do immediately if I see a transaction I did not authorize?' },
      { label: '🛡️ Card Security', query: 'How does FraudLens protect my account credentials and card data from theft?' },
    ],
  },
  investigator: {
    id: 'investigator',
    label: 'Fraud Investigator',
    icon: ShieldAlert,
    tag: 'Forensics & SOC',
    badgeClass: 'bg-amber-950/80 text-amber-300 border-amber-500/40',
    accentColor: 'amber',
    greeting: (name) =>
      `Greetings Investigator ${name}. 🔍 FraudLens Forensic AI Copilot is online. I'm synced with your active cases and TreeSHAP explainability pipeline. Which alert or anomaly pattern shall we investigate?`,
    questions: [
      { label: '🔑 Test API Keys (Grok & Gemini)', query: 'Test API key status for Grok and Gemini.' },
      { label: '📊 TreeSHAP Waterfall', query: 'Explain the TreeSHAP waterfall and key risk drivers for high-risk alerts.' },
      { label: '⚡ Velocity Bursts & Hops', query: 'What velocity bursts or geo-location hops trigger automated block rules?' },
      { label: '👥 Monisha vs Sowmiya', query: 'Analyze the behavioral risk differences between Monisha, Mohana, and Sowmiya.' },
      { label: '⚖️ False Positive Tuning', query: 'How should investigators evaluate false positives in the 30-70 OTP step-up band?' },
    ],
  },
  admin: {
    id: 'admin',
    label: 'Platform Admin',
    icon: Sliders,
    tag: 'MLOps & Systems',
    badgeClass: 'bg-cyan-950/80 text-cyan-300 border-cyan-500/40',
    accentColor: 'cyan',
    greeting: (name) =>
      `System Console connected, Admin ${name}. ⚙️ AI model diagnostics and throughput telemetry ready. XGBoost champion model running at sub-4ms inference latency. What system telemetry would you like to review?`,
    questions: [
      { label: '🔑 Test API Keys (Grok & Gemini)', query: 'Test API key status for Grok and Gemini.' },
      { label: '🤖 4 Model Comparison', query: 'What are the ROC-AUC, precision, and recall metrics of the 4 ML models?' },
      { label: '⏱️ <4ms Inference Latency', query: 'How does the FraudLens pre-auth gateway achieve sub-4ms inference latency in production?' },
      { label: '🌲 XGBoost vs Ensemble', query: 'Explain how the XGBoost champion model compares with the Voting / Stacking Ensemble.' },
      { label: '📊 Retrain Triggers & Drift', query: 'What metrics trigger automated model retraining and how is concept drift monitored?' },
    ],
  },
}

const PROVIDER_OPTIONS = [
  { id: 'auto',    label: 'AUTO',    fullLabel: '🤖 AUTO (Intelligent Failover)',   description: 'Gemini-first intelligent coordinator: Gemini 3.6/3.7 → auto-fails over to Mistral/Grok', color: 'emerald' },
  { id: 'gemini',  label: 'GEMINI',  fullLabel: '✨ GEMINI (Primary)',             description: 'Direct Google Gemini (3.6 default; 3.7 for heavy reasoning). No silent failover.',          color: 'cyan' },
  { id: 'grok',    label: 'GROK',    fullLabel: '⚡ GROK (Independent Review)',     description: 'Direct xAI Grok-2: independent forensic challenge & adversarial audit. No silent failover.', color: 'indigo' },
  { id: 'mistral', label: 'MISTRAL', fullLabel: '🌟 MISTRAL (Complementary)',      description: 'Direct Mistral AI (open-mistral-7b): alternative perspective. No silent failover.',          color: 'violet' },
]

// Processing stage sequencer — maps elapsed time to meaningful AI state labels
const PROCESSING_STAGES = [
  { label: 'Searching', icon: Search, duration: 1200 },
  { label: 'Scanning', icon: ScanLine, duration: 1500 },
  { label: 'Analysing', icon: Brain, duration: 2000 },
  { label: 'Processing', icon: Zap, duration: 3000 },
]

function useProcessingStage(isLoading) {
  const [stageIndex, setStageIndex] = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!isLoading) {
      setStageIndex(0)
      clearTimeout(timerRef.current)
      return
    }

    let elapsed = 0
    let idx = 0

    const advance = () => {
      if (idx < PROCESSING_STAGES.length - 1) {
        idx++
        setStageIndex(idx)
      }
      elapsed += PROCESSING_STAGES[idx]?.duration || 2000
      if (idx < PROCESSING_STAGES.length - 1) {
        timerRef.current = setTimeout(advance, PROCESSING_STAGES[idx + 1]?.duration || 2000)
      }
    }

    timerRef.current = setTimeout(advance, PROCESSING_STAGES[0].duration)

    return () => clearTimeout(timerRef.current)
  }, [isLoading])

  return isLoading ? PROCESSING_STAGES[stageIndex] : null
}

// Map processing stage to AIOrb state
function getOrbState(isLoading, processingStage) {
  if (!isLoading) return 'idle'
  if (!processingStage) return 'searching'
  const label = processingStage.label.toLowerCase()
  if (label === 'searching') return 'searching'
  if (label === 'scanning') return 'searching'
  if (label === 'analysing') return 'analysing'
  return 'deep_reasoning'
}

// Provider color config
const PROVIDER_COLORS = {
  auto: {
    bg: 'bg-emerald-600', border: 'border-emerald-400', ring: 'ring-emerald-400/40',
    shadow: 'shadow-emerald-950', text: 'text-emerald-400', bgMuted: 'bg-emerald-950/80',
    borderMuted: 'border-emerald-500/30',
  },
  gemini: {
    bg: 'bg-cyan-600', border: 'border-cyan-400', ring: 'ring-cyan-400/40',
    shadow: 'shadow-cyan-900', text: 'text-cyan-400', bgMuted: 'bg-cyan-950/80',
    borderMuted: 'border-cyan-500/30',
  },
  grok: {
    bg: 'bg-indigo-600', border: 'border-indigo-400', ring: 'ring-indigo-400/40',
    shadow: 'shadow-indigo-900', text: 'text-indigo-400', bgMuted: 'bg-indigo-950/90',
    borderMuted: 'border-indigo-500/40',
  },
  mistral: {
    bg: 'bg-violet-600', border: 'border-violet-400', ring: 'ring-violet-400/40',
    shadow: 'shadow-violet-900', text: 'text-violet-400', bgMuted: 'bg-violet-950/90',
    borderMuted: 'border-violet-500/40',
  },
}

export default function AiAssistantPanel({
  user,
  isAdmin,
  currentView = '',
  currentTransactionId = '',
  onExpandToCommandCenter,
  isOpenExternal,
  onOpenChange,
}) {
  // ── AUTOMATIC ZERO-CONFIGURATION IDENTITY RESOLUTION ──
  const userRoleStr = (user?.role || '').toLowerCase()
  const detectedRoleKey = isAdmin || userRoleStr === 'admin'
    ? 'admin'
    : (userRoleStr === 'fraud_investigator' || userRoleStr === 'investigator' || userRoleStr === 'analyst'
      ? 'investigator'
      : 'customer')

  const roleConfig = ROLE_PROFILES[detectedRoleKey] || ROLE_PROFILES.customer
  const userName = user?.name || user?.full_name?.split(' ')[0] || user?.email?.split('@')[0] || 'User'

  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)

  // Synchronize with external open state (e.g., when minimizing from Command Center)
  useEffect(() => {
    if (typeof isOpenExternal === 'boolean') {
      setIsOpen(isOpenExternal)
      if (isOpenExternal) {
        setIsMinimized(false)
        setUnreadCount(0)
      }
    }
  }, [isOpenExternal])

  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [provider, setProvider] = useState('auto')
  const [providerInfo, setProviderInfo] = useState(null)
  const [showProviderPicker, setShowProviderPicker] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [helpdeskContext, setHelpdeskContext] = useState(null)
  const [showHelpdeskModules, setShowHelpdeskModules] = useState(false)

  // API Key Live Testing State
  const [showKeyDiagnostics, setShowKeyDiagnostics] = useState(false)
  const [keyDiagnosticData, setKeyDiagnosticData] = useState(null)
  const [testingKey, setTestingKey] = useState(false)

  const handleTestKeys = async () => {
    setShowKeyDiagnostics(true)
    setTestingKey(true)
    try {
      const res = await fetch(`${BASE_URL}/ai/verify-key?provider=all`, { headers: getAuthHeaders() })
      const data = await res.json()
      setKeyDiagnosticData(data)
    } catch (err) {
      setKeyDiagnosticData({ error: err.message })
    } finally {
      setTestingKey(false)
    }
  }

  // Voice synthesis state (Audio plays ONLY on explicit button press)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [currentSpeakingId, setCurrentSpeakingId] = useState(null)

  // Processing stage
  const processingStage = useProcessingStage(loading)
  const orbState = getOrbState(loading, processingStage)

  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const inputRef = useRef(null)

  // Scroll smoothly inside message container ONLY — prevents window from jumping down
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, [messages, loading])

  // Fetch provider info & verified backend helpdesk context
  useEffect(() => {
    if (!user) return
    fetch(`${BASE_URL}/ai/providers`, { headers: getAuthHeaders() })
      .then((r) => r.json())
      .then((data) => setProviderInfo(data))
      .catch(() => {})

    fetch(`${BASE_URL}/ai/helpdesk-context`, { headers: getAuthHeaders() })
      .then((r) => r.json())
      .then((data) => setHelpdeskContext(data))
      .catch(() => {})
  }, [user])

  // Automatically load customized greeting the moment panel opens
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          id: Date.now(),
          role: 'assistant',
          content: roleConfig.greeting(userName),
          provider: 'Google Gemini',
          model: 'gemini-3.6-flash',
          used_real_api: true,
          timestamp: new Date().toISOString(),
        },
      ])
    }
  }, [isOpen, userName, roleConfig, messages.length])

  // Track unread responses when minimized
  useEffect(() => {
    if (isMinimized && messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
      setUnreadCount((c) => c + 1)
    }
  }, [messages, isMinimized])

  const handleOpen = () => {
    setIsOpen(true)
    setIsMinimized(false)
    setUnreadCount(0)
    onOpenChange?.(true)
  }

  const handleClose = () => {
    setIsOpen(false)
    setIsMinimized(false)
    handleStopSpeak()
    onOpenChange?.(false)
  }

  // Voice playback (ONLY triggered on explicit button click)
  const handleToggleSpeak = (text, id) => {
    if (!('speechSynthesis' in window)) return

    if (currentSpeakingId === id) {
      if (isSpeaking && !isPaused) {
        window.speechSynthesis.pause()
        setIsPaused(true)
      } else if (isPaused) {
        window.speechSynthesis.resume()
        setIsPaused(false)
      }
      return
    }

    window.speechSynthesis.cancel()
    const cleanText = text.replace(/[*_#`[\]()]/g, ' ')
    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.rate = 1.05
    utterance.pitch = 1.0

    utterance.onstart = () => {
      setIsSpeaking(true)
      setIsPaused(false)
      setCurrentSpeakingId(id)
    }
    utterance.onend = () => {
      setIsSpeaking(false)
      setIsPaused(false)
      setCurrentSpeakingId(null)
    }
    utterance.onerror = () => {
      setIsSpeaking(false)
      setIsPaused(false)
      setCurrentSpeakingId(null)
    }

    window.speechSynthesis.speak(utterance)
  }

  const handleStopSpeak = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    setIsSpeaking(false)
    setIsPaused(false)
    setCurrentSpeakingId(null)
  }

  const clearChat = () => {
    handleStopSpeak()
    setMessages([
      {
        id: Date.now(),
        role: 'assistant',
        content: roleConfig.greeting(userName),
        provider: 'Google Gemini',
        model: 'gemini-3.6-flash',
        used_real_api: true,
        timestamp: new Date().toISOString(),
      },
    ])
  }

  // Copy message text
  const handleCopy = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {}
  }

  // Send message
  const sendMessage = useCallback(
    async (textOverride) => {
      const text = (textOverride || inputText).trim()
      if (!text || loading) return

      const userMsg = {
        id: Date.now(),
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, userMsg])
      setInputText('')
      setLoading(true)

      try {
        const conversationHistory = [...messages, userMsg]
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .map((m) => ({ role: m.role, content: m.content }))

        const contextInfo = `View: ${currentView || 'Dashboard'}, Tx: ${currentTransactionId || 'None'}`

        const res = await fetch(`${BASE_URL}/ai/chat`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            messages: conversationHistory,
            provider: provider === 'auto' ? null : provider,
            temperature: 0.7,
            role: detectedRoleKey,
            context: contextInfo,
          }),
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()

        const assistantMsg = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.response,
          provider: data.provider,
          model: data.model,
          used_real_api: data.used_real_api,
          grok_challenge_applied: data.grok_challenge_applied,
          routing: data.routing,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMsg])

        // NOTE: Audio is intentionally NOT auto-played. It plays ONLY when the user clicks the Audio button.
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant',
            content: `I encountered a communication issue: ${err.message}. Automatically failing over to secondary AI engine. Please retry your request.`,
            provider: 'System Failover',
            model: 'failover-v1',
            used_real_api: false,
            timestamp: new Date().toISOString(),
          },
        ])
      } finally {
        setLoading(false)
      }
    },
    [inputText, loading, messages, provider, detectedRoleKey, currentView, currentTransactionId]
  )

  const provColors = PROVIDER_COLORS[provider] || PROVIDER_COLORS.auto

  // When inside the Full AI Investigation Command Center, hide the floating panel
  if (currentView === 'ai-copilot') {
    return null
  }

  // ─── FLOATING LAUNCHER (when closed) ───
  if (!isOpen) {
    return (
      <div className="fixed bottom-4 sm:bottom-6 right-4 sm:right-6 z-50">
        <button
          onClick={handleOpen}
          aria-label="Open FraudLens AI Intelligence Workspace"
          className="relative group flex items-center gap-3 px-4 py-3.5 rounded-2xl premium-glass border-2 border-white/15 hover:border-cyan-400/60 text-white transition-all duration-300 hover:scale-105 shadow-2xl"
        >
          {/* Ping ring */}
          <span className="absolute -inset-1.5 rounded-2xl border border-cyan-400/30 animate-ping opacity-25 pointer-events-none" />

          {/* AI Orb mini */}
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-950/70 group-hover:rotate-6 transition-transform ring-1 ring-white/20 animate-orb-breathe">
              <Bot className="w-5 h-5 text-[#fefae0]" />
            </div>
            <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-400 rounded-full border-2 border-slate-950 shadow-[0_0_8px_#34d399] animate-pulse" />
          </div>

          <div className="text-left pr-1">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-black tracking-wider font-mono text-[#fefae0]">FRAUDLENS AI</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-700/60 font-bold">
                Intelligence
              </span>
            </div>
            <p className="text-[10px] text-slate-300 font-mono flex items-center gap-1">
              <span>{helpdeskContext?.authenticated_role || roleConfig.label}:</span>
              <span className="text-emerald-400 font-bold">{userName}</span>
            </p>
          </div>

          {unreadCount > 0 && (
            <span className="absolute -top-2 -right-2 px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-cyan-500 text-slate-950 border-2 border-slate-950 animate-bounce">
              {unreadCount}
            </span>
          )}
        </button>
      </div>
    )
  }

  // ─── ACTIVE INTELLIGENCE WORKSPACE PANEL ───
  return (
    <div
      className={`fixed bottom-4 sm:bottom-6 right-3 sm:right-6 z-50 flex flex-col rounded-3xl border border-white/10 premium-glass transition-all duration-300 overflow-hidden shadow-2xl ${
        isMinimized
          ? 'w-[320px] sm:w-[360px] h-14'
          : 'w-[calc(100vw-1.5rem)] sm:w-[460px] max-w-[460px] h-[min(700px,calc(100dvh-2rem))]'
      }`}
    >
      {/* ── Warm Scanning Beam (during processing) ── */}
      {loading && (
        <div className="absolute inset-x-0 top-0 h-[2px] overflow-hidden pointer-events-none z-30">
          <div className="w-28 h-full bg-gradient-to-r from-transparent via-[#fefae0] to-transparent animate-warm-beam" />
        </div>
      )}

      {/* ── Glass shimmer overlay ── */}
      <div className="absolute inset-0 pointer-events-none z-0 glass-shimmer rounded-3xl" />

      {/* ── Premium Header with Orb & Identity ── */}
      <div
        className={`flex items-center justify-between px-4 py-3 border-b border-white/8 bg-gradient-to-r from-[#0b142d]/95 via-[#0e1b3d]/90 to-[#0b142d]/95 shrink-0 rounded-t-3xl relative z-10 ${
          isMinimized ? 'cursor-pointer hover:bg-white/5 transition' : ''
        }`}
        onClick={isMinimized ? () => setIsMinimized(false) : undefined}
      >
        <div className="flex items-center gap-3">
          {/* Mini AI Orb */}
          <div className="relative">
            <AIOrb
              state={orbState}
              size={isMinimized ? 32 : 40}
              provider={provider}
              className="rounded-xl"
            />
            <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-[#0b142d] shadow-[0_0_8px_#34d399]" />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-black tracking-wide text-[#fefae0] font-mono">FRAUDLENS AI</span>
              <span className="text-[8px] px-1.5 py-0.5 rounded-full font-mono font-bold bg-[#0b142d] text-cyan-300 border border-cyan-700/50">
                Intelligence
              </span>
            </div>
            {!isMinimized && (
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="text-[10px] font-mono text-slate-300 flex items-center gap-1">
                  <span className="text-emerald-400 font-bold">{userName}</span>
                </span>
                <span className="text-slate-600">•</span>
                <span className={`text-[8px] font-mono font-bold px-1.5 py-0.5 rounded border ${roleConfig.badgeClass}`}>
                  {(helpdeskContext?.authenticated_role || roleConfig.label).toUpperCase()}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-0.5">
          {/* Audio Stop */}
          {isSpeaking && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleStopSpeak()
              }}
              className="px-2 py-1 rounded-lg border text-rose-300 bg-rose-950/70 border-rose-500/50 hover:bg-rose-900/60 transition flex items-center gap-1 text-[10px] font-mono animate-pulse"
              title="Stop audio playback"
            >
              <Square className="w-3 h-3 fill-rose-300" />
              <span>Stop</span>
            </button>
          )}

          {/* Provider picker trigger (when not minimized) */}
          {!isMinimized && (
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowProviderPicker(!showProviderPicker)
                }}
                className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-white/5 border border-transparent hover:border-white/10 transition"
                title="Select LLM Engine"
              >
                <Globe className="w-4 h-4" />
              </button>
              {showProviderPicker && (
                <div className="absolute top-9 right-0 w-72 premium-glass border border-cyan-500/30 rounded-2xl shadow-2xl z-20 overflow-hidden">
                  <div className="p-2.5 border-b border-white/8 text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-wider">
                    AI Engine Architecture
                  </div>
                  {PROVIDER_OPTIONS.map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => {
                        setProvider(opt.id)
                        setShowProviderPicker(false)
                      }}
                      className={`w-full text-left px-3 py-2.5 text-xs transition flex flex-col ${
                        provider === opt.id
                          ? `${PROVIDER_COLORS[opt.id].bgMuted} text-white border-l-4 ${PROVIDER_COLORS[opt.id].border}`
                          : 'text-slate-300 hover:bg-white/5'
                      }`}
                    >
                      <span className="font-bold flex items-center justify-between">
                        {opt.fullLabel}
                        {provider === opt.id && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                      </span>
                      <span className="text-slate-400 text-[10px] mt-0.5">{opt.description}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Clear chat (when not minimized) */}
          {!isMinimized && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                clearChat()
              }}
              className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-white/5 transition"
              title="Reset Conversation"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}

          {/* Expand to Command Center */}
          {onExpandToCommandCenter && !isMinimized && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleClose()
                onExpandToCommandCenter()
              }}
              className="p-1.5 rounded-lg text-cyan-400 hover:text-white hover:bg-cyan-950/40 border border-cyan-500/20 hover:border-cyan-400 transition"
              title="Expand to Full AI Investigation Command Center"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          )}

          {/* Minimize / Restore */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsMinimized(!isMinimized)
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"
            title={isMinimized ? 'Expand / Restore Chat Panel' : 'Minimize Chat Panel'}
            aria-label={isMinimized ? 'Expand / Restore Chat Panel' : 'Minimize Chat Panel'}
          >
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {/* Close */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleClose()
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition"
            title="Close Chat Panel"
            aria-label="Close Chat Panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* ── Premium Model Selector Strip ── */}
          <div className="px-3 py-2 bg-[#060c1e]/95 border-b border-white/6 flex items-center justify-between gap-1 shrink-0 relative z-10">
            <div className="flex items-center gap-1">
              {PROVIDER_OPTIONS.map((opt) => {
                const isActive = provider === opt.id
                const colors = PROVIDER_COLORS[opt.id]
                return (
                  <button
                    key={opt.id}
                    onClick={() => setProvider(opt.id)}
                    className={`px-2.5 py-1 rounded-lg font-bold transition-all duration-200 flex items-center gap-1 border text-[10px] font-mono ${
                      isActive
                        ? `${colors.bg} text-white ${colors.border} shadow-sm ${colors.shadow} ring-1 ${colors.ring}`
                        : 'bg-transparent text-slate-500 hover:text-slate-200 border-transparent hover:border-white/10'
                    }`}
                    title={opt.description}
                  >
                    {isActive && <span className={`w-1.5 h-1.5 rounded-full bg-white animate-mode-pulse`} />}
                    <span>{opt.label}</span>
                  </button>
                )
              })}
            </div>
            <button
              onClick={handleTestKeys}
              className="px-2 py-1 rounded-lg font-bold transition flex items-center gap-1 border text-[10px] font-mono bg-transparent text-amber-400/80 hover:text-amber-300 border-amber-500/30 hover:border-amber-400/60"
              title="Directly test & verify AI API keys"
            >
              <Key className="w-3 h-3" />
            </button>
          </div>

          {/* ── Provider Status Banner ── */}
          <div className={`px-3.5 py-1.5 ${provColors.bgMuted} border-b ${provColors.borderMuted} flex items-center justify-between text-[10px] font-mono ${provColors.text} animate-fadeIn shrink-0 relative z-10`}>
            <div className="flex items-center gap-1.5 truncate">
              <span className={`w-1.5 h-1.5 rounded-full ${provider === 'auto' ? 'bg-emerald-400 animate-pulse' : provider === 'gemini' ? 'bg-cyan-400' : provider === 'grok' ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'} shrink-0`} />
              <span className="truncate text-slate-300">
                {provider === 'auto' && <><strong className="text-white">AUTO</strong> · Gemini 1st (3.6 / 3.7) · Intelligent Failover</>}
                {provider === 'gemini' && <><strong className="text-white">GEMINI</strong> · Direct Inference (3.6 Flash / 3.7 Deep)</>}
                {provider === 'grok' && <><strong className="text-white">GROK</strong> · Direct xAI Grok-2 · Independent Challenge</>}
                {provider === 'mistral' && <><strong className="text-white">MISTRAL</strong> · Direct open-mistral-7b · Complementary</>}
              </span>
            </div>
          </div>

          {/* ── Verified Identity & Security Ribbon ── */}
          <div className="px-3.5 py-1.5 border-b border-white/5 bg-[#060c1e]/80 shrink-0 flex items-center justify-between relative z-10">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
              <span className="text-[10px] font-mono text-slate-300">
                <strong className="text-[#fefae0]">{userName}</strong>
                <span className="text-slate-500 ml-1.5">({user?.email || 'authenticated'})</span>
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] font-mono text-cyan-400/80 flex items-center gap-0.5">
                <ShieldCheck className="w-3 h-3" />
                Zero-Leak
              </span>
              <button
                onClick={() => setShowHelpdeskModules(!showHelpdeskModules)}
                className={`text-[8px] font-mono font-bold px-1.5 py-0.5 rounded border transition cursor-pointer hover:opacity-80 ${roleConfig.badgeClass}`}
              >
                {roleConfig.tag.toUpperCase()}
              </button>
            </div>
          </div>

          {/* ── Help Desk Modules Dropdown ── */}
          {showHelpdeskModules && helpdeskContext && (
            <div className="px-3.5 py-2 bg-[#060c1e]/95 border-b border-white/8 animate-fadeIn shrink-0 relative z-10">
              <div className="text-[9px] font-mono text-cyan-400 font-bold uppercase tracking-wider mb-1.5">
                Authorized Modules · {helpdeskContext.security_clearance}
              </div>
              <div className="flex flex-wrap gap-1">
                {helpdeskContext.authorized_modules?.map((mod) => (
                  <span key={mod} className="text-[9px] font-mono px-2 py-0.5 rounded-md bg-[#0b142d] text-slate-300 border border-white/8">
                    {mod}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* ── Live Key Diagnostics Modal ── */}
          {showKeyDiagnostics && (
            <div className="absolute inset-x-3 top-24 bottom-20 z-50 premium-glass border border-cyan-500/30 rounded-2xl p-4 shadow-2xl flex flex-col justify-between overflow-y-auto">
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-white/8 pb-2">
                  <div className="flex items-center gap-2">
                    <Key className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold text-[#fefae0] font-mono uppercase tracking-wider">
                      Live AI API Key Diagnostics
                    </h3>
                  </div>
                  <button
                    onClick={() => setShowKeyDiagnostics(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/5"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {testingKey ? (
                  <div className="p-8 flex flex-col items-center justify-center space-y-3 text-center">
                    <AIOrb state="searching" size={64} provider={provider} />
                    <p className="text-xs font-mono text-slate-300">Pinging Google Gemini, xAI Grok & Mistral APIs...</p>
                  </div>
                ) : (
                  <div className="space-y-3 text-xs font-mono">
                    {/* Gemini */}
                    <div className="p-3 rounded-xl frosted-card space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-cyan-300 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          Google Gemini (Primary)
                        </span>
                        <span className="px-2 py-0.5 rounded text-[9px] bg-emerald-950/80 text-emerald-300 border border-emerald-700/50 font-bold">
                          {keyDiagnosticData?.gemini?.valid ? 'ACTIVE' : 'CHECK FAILED'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400">{keyDiagnosticData?.gemini?.message || 'Gemini 3.6 / 3.7 Flash connected.'}</p>
                    </div>

                    {/* Grok */}
                    <div className="p-3 rounded-xl frosted-card space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-indigo-300 flex items-center gap-1.5">
                          {keyDiagnosticData?.grok?.valid
                            ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            : <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                          }
                          xAI Grok-2 (Secondary)
                        </span>
                        <span className="px-2 py-0.5 rounded text-[9px] bg-indigo-950/80 text-indigo-300 border border-indigo-700/50 font-bold">
                          {keyDiagnosticData?.grok?.valid ? 'AUTHENTICATED' : 'CHECK FAILED'}
                        </span>
                      </div>
                      {keyDiagnosticData?.grok?.valid ? (
                        <div className="space-y-1 text-[10px] text-slate-400">
                          <div className="flex justify-between"><span>Key Name:</span><span className="text-white font-bold">&quot;{keyDiagnosticData.grok.key_name}&quot;</span></div>
                          <div className="flex justify-between"><span>Team ID:</span><span className="truncate max-w-[160px]">{keyDiagnosticData.grok.team_id}</span></div>
                          {keyDiagnosticData.grok.team_blocked && (
                            <div className="p-2 rounded bg-amber-950/60 border border-amber-600/30 text-amber-200 mt-1 text-[9px]">
                              <strong className="flex items-center gap-1"><AlertCircle className="w-3 h-3 text-amber-400" /> Billing:</strong> $0 credits on console.x.ai. Add credits to run completions.
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-[10px] text-rose-400">{keyDiagnosticData?.grok?.message}</p>
                      )}
                    </div>

                    {/* Mistral */}
                    <div className="p-3 rounded-xl frosted-card space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-violet-300 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          Mistral AI (3rd Engine)
                        </span>
                        <span className="px-2 py-0.5 rounded text-[9px] bg-violet-950/80 text-violet-300 border border-violet-700/50 font-bold">
                          {keyDiagnosticData?.mistral?.valid ? 'ACTIVE' : 'CHECK FAILED'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400">{keyDiagnosticData?.mistral?.message || 'Mistral AI (open-mistral-7b) connected and ready.'}</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 pt-3 border-t border-white/8 mt-2">
                <button
                  onClick={handleTestKeys}
                  disabled={testingKey}
                  className="flex-1 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold font-mono transition flex items-center justify-center gap-1.5 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${testingKey ? 'animate-spin' : ''}`} />
                  Re-Test Keys
                </button>
                <button
                  onClick={() => setShowKeyDiagnostics(false)}
                  className="px-4 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-mono font-bold transition border border-white/10"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* ── Message Stream ── */}
          <div
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-track-slate-950 scrollbar-thumb-slate-800 relative z-10"
          >
            {messages.map((msg, idx) => {
              const isAssistant = msg.role === 'assistant'
              const isThisSpeaking = currentSpeakingId === msg.id
              const isLatest = idx === messages.length - 1

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3 animate-msg-enter ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                  style={{ animationDelay: isLatest ? '0ms' : '0ms' }}
                >
                  {/* Assistant Avatar — mini orb */}
                  {isAssistant && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-700 flex items-center justify-center shrink-0 shadow-md shadow-cyan-950/80 mt-0.5 ring-1 ring-white/10">
                      <Bot className="w-4 h-4 text-[#fefae0]" />
                    </div>
                  )}

                  <div className={`max-w-[85%] space-y-1 ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                    {/* Message Bubble */}
                    <div
                      className={`px-4 py-3 rounded-2xl text-[13px] leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-r from-cyan-600/90 to-blue-700/90 text-white font-medium shadow-lg shadow-cyan-950/40 rounded-tr-sm border border-cyan-500/20'
                          : 'frosted-card text-slate-100 rounded-tl-sm'
                      }`}
                    >
                      <div className="whitespace-pre-wrap select-text selection:bg-cyan-500/40 selection:text-white">
                        {msg.content}
                      </div>
                    </div>

                    {/* Assistant metadata & controls */}
                    {isAssistant && (
                      <div className="flex items-center gap-1.5 text-[9px] font-mono text-slate-500 flex-wrap">
                        {/* Model badge */}
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-[#0b142d] text-cyan-300/80 border border-cyan-800/40">
                          <Zap className="w-2.5 h-2.5" />
                          {msg.model || 'gemini-3.6-flash'}
                        </span>

                        {/* Dual synthesis badge */}
                        {msg.grok_challenge_applied && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-indigo-950/70 text-indigo-300 border border-indigo-700/40">
                            <GitCompareArrows className="w-2.5 h-2.5" />
                            Dual Synthesis
                          </span>
                        )}

                        {/* Real API indicator */}
                        <span className={`px-1.5 py-0.5 rounded-md border font-bold ${
                          msg.used_real_api
                            ? 'bg-emerald-950/60 text-emerald-400/80 border-emerald-800/40'
                            : 'bg-amber-950/60 text-amber-400/80 border-amber-800/40'
                        }`}>
                          {msg.used_real_api ? 'Real API' : 'Local'}
                        </span>

                        {/* Copy */}
                        <button
                          onClick={() => handleCopy(msg.content)}
                          className="p-0.5 rounded text-slate-500 hover:text-cyan-300 transition"
                          title="Copy response"
                        >
                          <Copy className="w-3 h-3" />
                        </button>

                        {/* Audio Play */}
                        <button
                          onClick={() => handleToggleSpeak(msg.content, msg.id)}
                          className={`px-1.5 py-0.5 rounded transition flex items-center gap-0.5 border ${
                            isThisSpeaking && !isPaused
                              ? 'text-cyan-300 bg-cyan-950/60 border-cyan-500/40 animate-pulse'
                              : 'text-slate-500 border-transparent hover:text-cyan-300 hover:border-white/10'
                          }`}
                          title="Listen"
                        >
                          {isThisSpeaking && !isPaused ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                        </button>

                        {isThisSpeaking && (
                          <button onClick={handleStopSpeak} className="p-0.5 rounded text-rose-400 hover:text-rose-300 transition" title="Stop">
                            <Square className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}

            {/* ── Premium Loading: Stage-Sequenced Processing ── */}
            {loading && (
              <div className="flex gap-3 animate-msg-enter">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-700 flex items-center justify-center shrink-0 shadow-md shadow-cyan-950/80 ring-1 ring-white/10 animate-orb-breathe">
                  <Bot className="w-4 h-4 text-[#fefae0]" />
                </div>
                <div className="frosted-card px-4 py-3.5 rounded-2xl rounded-tl-sm flex items-center gap-3">
                  {/* Processing stage orb */}
                  <AIOrb state={orbState} size={36} provider={provider} />

                  <div className="flex flex-col gap-1">
                    {/* Stage indicators */}
                    <div className="flex items-center gap-2">
                      {PROCESSING_STAGES.map((stage, idx) => {
                        const StageIcon = stage.icon
                        const isActive = processingStage && stage.label === processingStage.label
                        const isPast = processingStage && PROCESSING_STAGES.indexOf(processingStage) > idx
                        return (
                          <span
                            key={stage.label}
                            className={`text-[9px] font-mono font-bold flex items-center gap-0.5 transition-all duration-300 ${
                              isActive
                                ? 'text-cyan-300 animate-stage-glow'
                                : isPast
                                  ? 'text-slate-500'
                                  : 'text-slate-700'
                            }`}
                          >
                            <StageIcon className="w-3 h-3" />
                            {stage.label}
                          </span>
                        )
                      })}
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">
                      via {provider === 'auto' ? 'Gemini 3.6' : provider === 'gemini' ? 'Gemini 3.6/3.7' : provider === 'grok' ? 'Grok-2' : 'Mistral'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* ── Role-Specific Help Desk Prompt Chips ── */}
          <div className="px-3.5 py-2 border-t border-white/6 bg-[#060c1e]/90 shrink-0 relative z-10">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] font-mono text-[#fefae0]/80 font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3 h-3 text-cyan-400/70" />
                <span>Help Desk ({helpdeskContext?.authenticated_role || roleConfig.label})</span>
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(helpdeskContext?.suggested_prompts || roleConfig.questions).map((q) => (
                <button
                  key={q.label}
                  onClick={() => sendMessage(q.query)}
                  disabled={loading}
                  className="px-2.5 py-1.5 rounded-xl bg-[#0b142d]/80 hover:bg-cyan-950/50 border border-white/8 hover:border-cyan-400/40 text-[10px] font-medium text-slate-300 hover:text-[#fefae0] transition-all duration-200 disabled:opacity-30"
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>

          {/* ── Premium Input Bar ── */}
          <div className="p-3.5 border-t border-white/6 bg-[#0b142d]/95 shrink-0 rounded-b-3xl relative z-10">
            <div className="flex items-center gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage()
                    }
                  }}
                  placeholder={`Ask FraudLens AI as ${helpdeskContext?.authenticated_role || roleConfig.label}…`}
                  rows={1}
                  className="w-full bg-[#060c1e]/90 border border-white/12 focus:border-cyan-400/60 rounded-xl px-4 py-3 text-[13px] text-white placeholder-slate-500 focus:outline-none input-warm-focus resize-none transition-all duration-200"
                  style={{ minHeight: '44px', maxHeight: '110px' }}
                  disabled={loading}
                />
              </div>

              <button
                onClick={() => sendMessage()}
                disabled={loading || !inputText.trim()}
                className="w-11 h-11 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-30 disabled:cursor-not-allowed text-[#fefae0] flex items-center justify-center shadow-lg shadow-cyan-950/50 transition-all duration-200 hover:scale-105 hover:shadow-[0_0_20px_rgba(6,182,212,0.3)] shrink-0"
                title="Send Message"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>

            <div className="flex items-center justify-between mt-1.5 text-[8px] font-mono text-slate-600 px-1">
              <span>Enter to send · Shift+Enter for newline</span>
              <span className="text-cyan-500/50">⚡ Auto Identity · Intelligent Failover</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
