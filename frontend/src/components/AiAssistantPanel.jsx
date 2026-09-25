/**
 * FraudLens AI Assistant Panel — Powered by Google Gemini & xAI Grok
 *
 * A premium floating chat panel with:
 * - Real Gemini 2.0 Flash / Grok-2 AI answers about fraud, SHAP, risk
 * - Role-aware context (customer vs investigator framing)
 * - Sweet voice read-aloud for every AI response
 * - Provider selector (Gemini / Grok / Auto)
 * - Animated gradient UI with glassmorphism
 * - Quick-access topic chips
 * - Conversation history (in-session)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Bot,
  X,
  Send,
  Sparkles,
  Mic,
  Volume2,
  VolumeX,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Zap,
  Brain,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  TrendingUp,
  Cpu,
  Play,
  Pause,
  Square,
  CheckCircle2,
  Lock,
  Globe,
} from 'lucide-react'

const BASE_URL = '/api/v1'

function getAuthHeaders() {
  const token = localStorage.getItem('fraudlens_token')
  return {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

// Quick-topic suggestions
const QUICK_TOPICS = [
  { label: '🔍 What is Fraud?', query: 'What is financial fraud in digital payments? Explain simply.' },
  { label: '📊 SHAP Explained', query: 'Explain TreeSHAP game-theoretic Shapley values in simple terms.' },
  { label: '🤖 AI Models', query: 'What are the 4 AI models in FraudLens and how do they work together?' },
  { label: '🛡️ Risk Score', query: 'How is the composite risk score (0-100) calculated?' },
  { label: '📱 OTP Step-Up', query: 'How does mobile OTP step-up authentication work to protect my payment?' },
  { label: '👥 3 Customers', query: 'Tell me about the 3 customer personas: Monisha, Mohana, and Sowmiya.' },
  { label: '🏪 Merchants', query: 'What are the 29 canonical merchants in FraudLens?' },
  { label: '🚨 Attack Vectors', query: 'What are the most common fraud attack vectors in digital banking?' },
]

const PROVIDER_OPTIONS = [
  { id: 'auto', label: '🤖 Auto (Best Available)', description: 'Uses Gemini, then Grok, then Smart AI' },
  { id: 'gemini', label: '✨ Google Gemini 2.0 Flash', description: 'Google AI Studio powered' },
  { id: 'grok', label: '⚡ xAI Grok-2 Enterprise', description: 'xAI powered' },
]

export default function AiAssistantPanel({ user, isAdmin, currentView = '', currentTransactionId = '' }) {
  const isCustomer = !isAdmin && (user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user')
  const userName = user?.full_name?.split(' ')[0] || user?.email?.split('@')[0] || 'there'

  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [provider, setProvider] = useState('auto')
  const [providerInfo, setProviderInfo] = useState(null)
  const [showProviderPicker, setShowProviderPicker] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [hasGreeted, setHasGreeted] = useState(false)

  // Voice synthesis state
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [currentSpeakingId, setCurrentSpeakingId] = useState(null)

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Scroll to bottom when new message arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load provider status
  useEffect(() => {
    if (!user) return
    fetch(`${BASE_URL}/ai/providers`, { headers: getAuthHeaders() })
      .then((r) => r.json())
      .then((data) => setProviderInfo(data))
      .catch(() => {})
  }, [user])

  // Show greeting when panel first opens
  useEffect(() => {
    if (isOpen && !hasGreeted) {
      setHasGreeted(true)
      const greeting = isCustomer
        ? `Hello ${userName}! 👋 I'm your personal FraudLens AI Assistant. I'm here to help you understand your account security, transaction explanations, and how our AI protects your money. What would you like to know?`
        : `Hello ${userName}! 👋 I'm your FraudLens AI Copilot. I can help you investigate fraud cases, understand SHAP attributions, analyze risk patterns, and answer questions about the FraudLens detection system. How can I assist?`

      setMessages([
        {
          id: Date.now(),
          role: 'assistant',
          content: greeting,
          provider: 'FraudLens',
          model: 'greeting',
          used_real_api: false,
          timestamp: new Date().toISOString(),
        },
      ])
    }
  }, [isOpen, hasGreeted, isCustomer, userName])

  // Increment unread count when minimized and new message arrives
  useEffect(() => {
    if (isMinimized && messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
      setUnreadCount((c) => c + 1)
    }
  }, [messages, isMinimized])

  const handleOpen = () => {
    setIsOpen(true)
    setIsMinimized(false)
    setUnreadCount(0)
  }

  const buildContext = useCallback(() => {
    const parts = []
    if (currentView) parts.push(`Current view: ${currentView}`)
    if (currentTransactionId) parts.push(`Current transaction: ${currentTransactionId}`)
    if (isCustomer) parts.push(`User role: customer (${userName})`)
    else parts.push(`User role: ${isAdmin ? 'admin/investigator' : 'staff'} (${userName})`)
    return parts.join('. ')
  }, [currentView, currentTransactionId, isCustomer, isAdmin, userName])

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

        const res = await fetch(`${BASE_URL}/ai/chat`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            messages: conversationHistory,
            provider: provider === 'auto' ? null : provider,
            temperature: 0.7,
            context: buildContext(),
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
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMsg])

        // Auto-speak if voice enabled
        if (voiceEnabled && 'speechSynthesis' in window) {
          speakMessage(data.response, assistantMsg.id)
        }
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant',
            content: `I encountered an error: ${err.message}. Please try again or check your API key configuration.`,
            provider: 'Error',
            model: 'error',
            used_real_api: false,
            timestamp: new Date().toISOString(),
          },
        ])
      } finally {
        setLoading(false)
        inputRef.current?.focus()
      }
    },
    [inputText, loading, messages, provider, buildContext, voiceEnabled]
  )

  // Voice synthesis
  const speakMessage = (text, msgId) => {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)

    const voices = window.speechSynthesis.getVoices()
    const sweet = voices.find(
      (v) =>
        v.name.includes('Jenny') ||
        v.name.includes('Zira') ||
        v.name.includes('Aria') ||
        v.name.includes('Samantha') ||
        v.name.includes('Google UK English Female') ||
        v.name.includes('Google US English') ||
        (v.lang.startsWith('en') && v.name.toLowerCase().includes('female'))
    )
    if (sweet) utterance.voice = sweet
    utterance.pitch = 1.1
    utterance.rate = 0.95

    utterance.onstart = () => { setIsSpeaking(true); setIsPaused(false); setCurrentSpeakingId(msgId) }
    utterance.onend = () => { setIsSpeaking(false); setIsPaused(false); setCurrentSpeakingId(null) }
    utterance.onerror = () => { setIsSpeaking(false); setIsPaused(false); setCurrentSpeakingId(null) }
    window.speechSynthesis.speak(utterance)
  }

  const handleToggleSpeak = (text, msgId) => {
    if (currentSpeakingId === msgId && isSpeaking && !isPaused) {
      window.speechSynthesis.pause()
      setIsPaused(true)
    } else if (currentSpeakingId === msgId && isPaused) {
      window.speechSynthesis.resume()
      setIsPaused(false)
    } else {
      speakMessage(text, msgId)
    }
  }

  const handleStopSpeak = () => {
    window.speechSynthesis.cancel()
    setIsSpeaking(false)
    setIsPaused(false)
    setCurrentSpeakingId(null)
  }

  const clearChat = () => {
    window.speechSynthesis.cancel()
    setMessages([])
    setHasGreeted(false)
    setIsSpeaking(false)
    setCurrentSpeakingId(null)
  }

  const getProviderBadge = (msg) => {
    if (!msg.provider || msg.provider === 'FraudLens' || msg.provider === 'Error') return null
    const isGemini = msg.provider?.toLowerCase().includes('gemini')
    const isGrok = msg.provider?.toLowerCase().includes('grok')
    if (isGemini) return { label: '✨ Gemini', color: 'text-blue-300 bg-blue-950/60 border-blue-800' }
    if (isGrok) return { label: '⚡ Grok', color: 'text-purple-300 bg-purple-950/60 border-purple-800' }
    if (!msg.used_real_api) return { label: '🛡️ Smart AI', color: 'text-emerald-300 bg-emerald-950/60 border-emerald-800' }
    return null
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Floating Button
  // ─────────────────────────────────────────────────────────────────────────
  if (!isOpen) {
    return (
      <button
        onClick={handleOpen}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-600 shadow-2xl shadow-purple-900/60 flex items-center justify-center hover:scale-110 transition-all duration-300 group animate-pulse"
        title="Open FraudLens AI Assistant"
        id="ai-assistant-fab"
      >
        <Bot className="w-7 h-7 text-white" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
            {unreadCount}
          </span>
        )}
        <span className="absolute right-16 bg-slate-800 text-white text-xs px-3 py-1.5 rounded-xl shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700">
          FraudLens AI Assistant
        </span>
      </button>
    )
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Chat Panel
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex flex-col rounded-3xl shadow-2xl shadow-purple-950/60 border-2 border-purple-500/50 bg-slate-900/98 backdrop-blur-xl transition-all duration-300 ${
        isMinimized ? 'w-80 h-16' : 'w-96 h-[680px] max-h-[90vh]'
      }`}
      style={{ boxShadow: '0 0 60px rgba(168,85,247,0.3), 0 25px 50px rgba(0,0,0,0.7)' }}
    >
      {/* ── Header ── */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800/80 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center shadow-md shadow-purple-900/50">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold text-white">FraudLens AI</span>
              {providerInfo?.gemini_configured && (
                <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800">✨ Gemini</span>
              )}
              {providerInfo?.grok_configured && (
                <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold bg-purple-950 text-purple-300 border border-purple-800">⚡ Grok</span>
              )}
            </div>
            <p className="text-[10px] text-slate-400 font-mono">
              {isCustomer ? `Personal AI — ${userName}` : 'Forensic AI Copilot'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Voice toggle */}
          <button
            onClick={() => { setVoiceEnabled(!voiceEnabled); if (!voiceEnabled) handleStopSpeak() }}
            className={`p-1.5 rounded-lg transition ${voiceEnabled ? 'text-purple-400 hover:text-purple-300 bg-purple-950/40' : 'text-slate-500 hover:text-slate-400'}`}
            title={voiceEnabled ? 'Voice On — Click to Mute' : 'Voice Off — Click to Enable'}
          >
            {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          {/* Provider picker */}
          <div className="relative">
            <button
              onClick={() => setShowProviderPicker(!showProviderPicker)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
              title="Select AI Provider"
            >
              <Globe className="w-4 h-4" />
            </button>
            {showProviderPicker && (
              <div className="absolute top-8 right-0 w-64 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-10 overflow-hidden">
                {PROVIDER_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => { setProvider(opt.id); setShowProviderPicker(false) }}
                    className={`w-full text-left px-3 py-2.5 text-xs transition flex flex-col ${
                      provider === opt.id ? 'bg-purple-950/70 text-purple-200' : 'text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    <span className="font-semibold">{opt.label}</span>
                    <span className="text-slate-500 text-[10px]">{opt.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Clear */}
          <button
            onClick={clearChat}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition"
            title="Clear Conversation"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Minimize */}
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition"
          >
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {/* Close */}
          <button
            onClick={() => { setIsOpen(false); handleStopSpeak() }}
            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* ── Messages ── */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-track-slate-900 scrollbar-thumb-slate-700">
            {messages.map((msg) => {
              const badge = getProviderBadge(msg)
              const isThisSpeaking = currentSpeakingId === msg.id
              return (
                <div
                  key={msg.id}
                  className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  {/* Avatar */}
                  {msg.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div className={`max-w-[84%] space-y-1 ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                    <div
                      className={`px-3.5 py-2.5 rounded-2xl text-xs leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-purple-600 to-indigo-700 text-white rounded-tr-sm shadow-md'
                          : 'bg-slate-800/90 text-slate-200 rounded-tl-sm border border-slate-700/60 shadow-sm'
                      }`}
                    >
                      {msg.content}
                    </div>

                    {/* Message footer */}
                    {msg.role === 'assistant' && (
                      <div className="flex items-center gap-2 flex-wrap">
                        {badge && (
                          <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border font-bold ${badge.color}`}>
                            {badge.label}
                          </span>
                        )}

                        {/* Voice controls */}
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleToggleSpeak(msg.content, msg.id)}
                            className={`p-0.5 rounded transition ${isThisSpeaking && !isPaused ? 'text-purple-400 animate-pulse' : 'text-slate-600 hover:text-purple-400'}`}
                            title="Read aloud"
                          >
                            {isThisSpeaking && !isPaused ? (
                              <Pause className="w-3 h-3" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                          </button>
                          {isThisSpeaking && (
                            <button onClick={handleStopSpeak} className="p-0.5 rounded text-rose-400 hover:text-rose-300 transition">
                              <Square className="w-3 h-3" />
                            </button>
                          )}
                        </div>

                        {/* Soundwave when speaking */}
                        {isThisSpeaking && !isPaused && (
                          <div className="flex items-center gap-0.5">
                            {[1, 2, 3, 4].map((i) => (
                              <span
                                key={i}
                                className="w-0.5 bg-purple-400 rounded-full animate-bounce"
                                style={{ height: `${6 + i * 2}px`, animationDelay: `${i * 100}ms` }}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Loading animation */}
            {loading && (
              <div className="flex gap-2.5">
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-slate-800/90 border border-slate-700/60 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce [animation-delay:300ms]" />
                  <span className="text-[10px] text-slate-400 ml-1">AI thinking…</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* ── Quick Topics (shown when few messages) ── */}
          {messages.length <= 1 && (
            <div className="px-4 pb-2 shrink-0">
              <p className="text-[10px] text-slate-500 font-mono mb-2 uppercase tracking-wider">Quick Topics</p>
              <div className="flex flex-wrap gap-1.5">
                {QUICK_TOPICS.slice(0, 6).map((t) => (
                  <button
                    key={t.label}
                    onClick={() => sendMessage(t.query)}
                    disabled={loading}
                    className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-purple-700 text-[10px] text-slate-300 hover:text-white transition font-medium disabled:opacity-50"
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── Input Bar ── */}
          <div className="p-4 border-t border-slate-800/80 shrink-0">
            <div className="flex items-end gap-2">
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
                  placeholder={
                    isCustomer
                      ? 'Ask about your transactions, fraud protection, SHAP…'
                      : 'Ask about investigations, SHAP, risk scoring, AI models…'
                  }
                  rows={1}
                  className="w-full bg-slate-800/90 border border-slate-700 hover:border-purple-700 focus:border-purple-500 rounded-2xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50 resize-none transition scrollbar-none"
                  style={{ minHeight: '40px', maxHeight: '96px' }}
                  disabled={loading}
                />
              </div>
              <button
                onClick={() => sendMessage()}
                disabled={loading || !inputText.trim()}
                className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-purple-900/50 transition disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-[9px] text-slate-600 mt-1.5 text-center font-mono">
              Enter to send • Shift+Enter for newline •{' '}
              {providerInfo?.gemini_configured
                ? '✨ Gemini Active'
                : providerInfo?.grok_configured
                ? '⚡ Grok Active'
                : '🛡️ Smart AI Mode — add GEMINI_API_KEY to .env for full AI'}
            </p>
          </div>
        </>
      )}
    </div>
  )
}
