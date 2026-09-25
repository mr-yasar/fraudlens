import React, { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  Bot,
  BrainCircuit,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Play,
  Pause,
  Square,
  Copy,
  Check,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  FileText,
  Workflow,
  Download,
  Share2,
  RefreshCw,
  X,
  Radio,
  Layers,
  Zap,
} from 'lucide-react'
import { investigationsApi } from '../services/api'
import { formatINR } from '../utils/formatters'
import { sound } from './login/soundEffects'

export default function AiInvestigationModal({
  isOpen,
  onClose,
  caseId,
  transaction,
  onDecisionApplied,
}) {
  const [provider, setProvider] = useState('gemini') // 'gemini' | 'grok' | 'claude'
  const [loading, setLoading] = useState(false)
  const [dossier, setDossier] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('summary') // 'summary' | 'diagram' | 'sar' | 'voice'
  const [copiedSar, setCopiedSar] = useState(false)

  // Voice Assistant state (Siri / Google Voice)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [voiceVoice, setVoiceVoice] = useState(null)
  const [availableVoices, setAvailableVoices] = useState([])
  const [voiceSpeed, setVoiceSpeed] = useState(1.0)

  // Speech Recognition state (Voice Commands)
  const [isListening, setIsListening] = useState(false)
  const [voiceTranscript, setVoiceTranscript] = useState('')
  const [voiceCommandFeedback, setVoiceCommandFeedback] = useState(null)
  const recognitionRef = useRef(null)

  // Initialize Speech Synthesis Voices
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices()
        setAvailableVoices(voices)
        // Default to natural English Siri / Google / Samantha voice
        const preferred = voices.find(
          (v) =>
            v.name.includes('Google') ||
            v.name.includes('Siri') ||
            v.name.includes('Samantha') ||
            v.name.includes('Natural') ||
            (v.lang.startsWith('en') && !v.name.includes('Desktop'))
        )
        setVoiceVoice(preferred || voices[0] || null)
      }

      loadVoices()
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices
      }
    }
  }, [])

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = false
        recognition.lang = 'en-US'

        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript.toLowerCase().trim()
          setVoiceTranscript(transcript)
          handleVoiceCommand(transcript)
          setIsListening(false)
        }

        recognition.onerror = () => {
          setIsListening(false)
        }

        recognition.onend = () => {
          setIsListening(false)
        }

        recognitionRef.current = recognition
      }
    }
  }, [dossier])

  // Stop speaking when modal closes
  useEffect(() => {
    if (!isOpen && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      setIsPaused(false)
    }
  }, [isOpen])

  // Fetch AI Dossier
  const fetchDossier = async (prov = provider) => {
    if (!caseId) return
    setLoading(true)
    setError(null)
    try {
      const data = await investigationsApi.getAiDossier(caseId, prov)
      setDossier(data)
      sound.playSuccess && sound.playSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI Copilot synthesis failed')
      sound.playError && sound.playError()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && caseId) {
      fetchDossier(provider)
    }
  }, [isOpen, caseId, provider])

  // Voice Command Dispatcher
  const handleVoiceCommand = (cmd) => {
    sound.playBlip && sound.playBlip()
    if (cmd.includes('summarize') || cmd.includes('brief') || cmd.includes('explain') || cmd.includes('speak')) {
      setVoiceCommandFeedback('Executing: Reading Executive Briefing (Siri Voice)')
      handleSpeakScript()
    } else if (cmd.includes('freeze') || cmd.includes('fraud') || cmd.includes('block')) {
      setVoiceCommandFeedback('Executing: Confirming Fraud & Freezing Card')
      if (onDecisionApplied) {
        onDecisionApplied('CONFIRMED_FRAUD')
      }
    } else if (cmd.includes('genuine') || cmd.includes('safe') || cmd.includes('allow')) {
      setVoiceCommandFeedback('Executing: Marking Genuine False Positive')
      if (onDecisionApplied) {
        onDecisionApplied('GENUINE')
      }
    } else if (cmd.includes('diagram') || cmd.includes('flow') || cmd.includes('kill chain')) {
      setVoiceCommandFeedback('Executing: Switching to Attack Diagram')
      setActiveTab('diagram')
    } else if (cmd.includes('sar') || cmd.includes('report')) {
      setVoiceCommandFeedback('Executing: Opening Regulatory SAR Draft')
      setActiveTab('sar')
    } else {
      setVoiceCommandFeedback(`Heard: "${cmd}". Say "Summarize", "Attack Diagram", or "Confirm Fraud".`)
    }
    setTimeout(() => setVoiceCommandFeedback(null), 4500)
  }

  // Voice Narration (Text-to-Speech)
  const handleSpeakScript = () => {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported on this browser.')
      return
    }

    if (isSpeaking && !isPaused) {
      window.speechSynthesis.pause()
      setIsPaused(true)
      return
    }

    if (isPaused) {
      window.speechSynthesis.resume()
      setIsPaused(false)
      return
    }

    window.speechSynthesis.cancel()

    const script =
      dossier?.voice_narration_script ||
      `FraudLens Security Alert. Case ${caseId} is under review. The risk engine flagged an anomalous transaction with elevated risk. Zero funds lost.`

    const utterance = new SpeechSynthesisUtterance(script)
    if (voiceVoice) utterance.voice = voiceVoice
    utterance.rate = voiceSpeed
    utterance.pitch = 1.0

    utterance.onstart = () => {
      setIsSpeaking(true)
      setIsPaused(false)
    }

    utterance.onend = () => {
      setIsSpeaking(false)
      setIsPaused(false)
    }

    utterance.onerror = () => {
      setIsSpeaking(false)
      setIsPaused(false)
    }

    window.speechSynthesis.speak(utterance)
  }

  const handleStopSpeech = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      setIsPaused(false)
    }
  }

  // Voice recognition toggle
  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech Recognition is supported in Chrome, Edge, and Safari.')
      return
    }
    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      setVoiceTranscript('')
      recognitionRef.current.start()
      setIsListening(true)
      sound.playAlert && sound.playAlert()
    }
  }

  // Copy SAR to clipboard
  const handleCopySar = () => {
    if (!dossier?.regulatory_sar_draft) return
    navigator.clipboard?.writeText(dossier.regulatory_sar_draft)
    setCopiedSar(true)
    setTimeout(() => setCopiedSar(false), 2500)
    sound.playSuccess && sound.playSuccess()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md animate-fadeIn select-none overflow-y-auto">
      <div className="relative w-full max-w-4xl rounded-3xl bg-slate-950 border border-purple-500/40 shadow-[0_0_60px_rgba(168,85,247,0.25)] flex flex-col max-h-[92vh] overflow-hidden my-auto text-slate-100">
        {/* Top Header Glow */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-cyan-500 to-indigo-500" />

        {/* Modal Top Bar */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-600 text-white shadow-lg shadow-purple-500/25">
              <Bot className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black text-white tracking-tight">
                  AI Forensic Copilot &amp; Case Intelligence
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-950 text-purple-300 border border-purple-700 flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  GENAI INVESTIGATOR
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                Case: <strong className="text-cyan-400">{caseId}</strong> • Transaction:{' '}
                <span className="text-slate-300">{dossier?.transaction_id || transaction?.transaction_id}</span>
              </p>
            </div>
          </div>

          {/* AI Model Switcher & Close Button */}
          <div className="flex items-center gap-2">
            <div className="flex p-0.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono">
              <button
                type="button"
                onClick={() => setProvider('gemini')}
                className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                  provider === 'gemini'
                    ? 'bg-purple-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-3 h-3 text-cyan-300" />
                <span>Gemini 1.5</span>
              </button>
              <button
                type="button"
                onClick={() => setProvider('grok')}
                className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                  provider === 'grok'
                    ? 'bg-purple-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Zap className="w-3 h-3 text-amber-300" />
                <span>Grok-2</span>
              </button>
              <button
                type="button"
                onClick={() => setProvider('claude')}
                className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                  provider === 'claude'
                    ? 'bg-purple-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <BrainCircuit className="w-3 h-3 text-indigo-300" />
                <span>Claude 3.5</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition"
              title="Close Copilot"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* VOICE ASSISTANT BAR (Siri & Google Assistant Voice Bar) */}
        <div className="px-5 py-2.5 bg-gradient-to-r from-purple-950/70 via-slate-950 to-indigo-950/70 border-b border-purple-900/40 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-purple-300 font-semibold font-mono text-[11px]">
              <Radio className={`w-3.5 h-3.5 text-cyan-400 ${isSpeaking ? 'animate-ping' : ''}`} />
              <span>Voice Copilot (Siri / Google Voice):</span>
            </div>

            {/* Audio Waveform Animation when speaking */}
            {isSpeaking && (
              <div className="flex items-center gap-1 px-2 py-1 bg-purple-900/50 rounded-lg border border-purple-500/40 animate-pulse">
                <span className="w-1 h-3 bg-cyan-400 rounded-full animate-bounce" />
                <span className="w-1 h-5 bg-purple-400 rounded-full animate-bounce delay-75" />
                <span className="w-1 h-2 bg-indigo-400 rounded-full animate-bounce delay-150" />
                <span className="w-1 h-4 bg-emerald-400 rounded-full animate-bounce delay-100" />
                <span className="text-[10px] font-mono text-cyan-200 ml-1">Narrating Briefing...</span>
              </div>
            )}
          </div>

          {/* Voice Controls & Mic Button */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleSpeakScript}
              disabled={loading || !dossier}
              className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md transition flex items-center gap-1.5 active:scale-95"
            >
              {isSpeaking && !isPaused ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              <span>{isSpeaking && !isPaused ? 'Pause Voice' : isPaused ? 'Resume Voice' : 'Listen to Briefing'}</span>
            </button>

            {isSpeaking && (
              <button
                type="button"
                onClick={handleStopSpeech}
                className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                title="Stop Speech"
              >
                <Square className="w-3.5 h-3.5" />
              </button>
            )}

            {/* Speech-to-Text Microphone (Voice Command like Siri) */}
            <button
              type="button"
              onClick={toggleListening}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition flex items-center gap-1.5 active:scale-95 ${
                isListening
                  ? 'bg-rose-600 text-white animate-pulse shadow-lg shadow-rose-900/50'
                  : 'bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700'
              }`}
              title="Speak voice command (e.g. 'Summarize case', 'Confirm fraud', 'Attack diagram')"
            >
              {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
              <span>{isListening ? 'Listening...' : 'Voice Command'}</span>
            </button>
          </div>
        </div>

        {/* Live Voice Command Feedback Banner */}
        {voiceCommandFeedback && (
          <div className="px-5 py-2 bg-cyan-950/80 border-b border-cyan-800 text-cyan-200 text-xs font-mono flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
              <span>{voiceCommandFeedback}</span>
            </span>
            <span className="text-[10px] text-slate-400">Siri Assistant Ready</span>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-900/60 px-5 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('summary')}
            className={`py-3 px-4 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'summary'
                ? 'border-purple-400 text-purple-300 font-bold'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>Forensic Synthesis</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('diagram')}
            className={`py-3 px-4 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'diagram'
                ? 'border-purple-400 text-purple-300 font-bold'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Workflow className="w-4 h-4" />
            <span>Attack Architecture Diagram</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('sar')}
            className={`py-3 px-4 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'sar'
                ? 'border-purple-400 text-purple-300 font-bold'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Regulatory SAR Draft</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {loading && (
            <div className="py-16 text-center space-y-3">
              <RefreshCw className="w-10 h-10 text-purple-400 animate-spin mx-auto" />
              <div className="text-sm font-bold text-purple-200 font-mono">
                Synthesizing Forensic Intelligence with {provider === 'gemini' ? 'Google Gemini' : provider === 'grok' ? 'Grok-2' : 'Claude 3.5'}...
              </div>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Correlating customer behavioral history, multi-factor TreeSHAP attributions, and threat kill-chains.
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded-2xl bg-rose-950/70 border border-rose-700 text-rose-200 text-xs space-y-2">
              <div className="flex items-center gap-2 font-bold">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <span>AI Copilot Analysis Error</span>
              </div>
              <p>{error}</p>
              <button
                type="button"
                onClick={() => fetchDossier(provider)}
                className="px-3 py-1 bg-rose-700 hover:bg-rose-600 rounded-lg text-white font-semibold"
              >
                Retry Analysis
              </button>
            </div>
          )}

          {!loading && dossier && (
            <>
              {/* TAB 1: FORENSIC SYNTHESIS */}
              {activeTab === 'summary' && (
                <div className="space-y-4 animate-fadeIn">
                  {/* Executive Summary Card */}
                  <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                        Executive Forensic Summary
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Model: {dossier.model_name} • Confidence: {(dossier.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed font-sans">
                      {dossier.executive_summary}
                    </p>
                  </div>

                  {/* Threat Telemetry Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                    <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase">Attack Vector</div>
                      <div className="text-sm font-bold text-rose-400 mt-1 truncate">
                        {dossier.attack_vector}
                      </div>
                    </div>

                    <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase">AI Fraud Probability</div>
                      <div className="text-sm font-bold text-cyan-300 mt-1">
                        {(dossier.fraud_probability * 100).toFixed(1)}%
                      </div>
                    </div>

                    <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase">Independent Risk Score</div>
                      <div className="text-sm font-bold text-amber-300 mt-1">
                        {dossier.risk_score} / 100 ({dossier.risk_level})
                      </div>
                    </div>
                  </div>

                  {/* Modus Operandi & Root Cause */}
                  <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                      <BrainCircuit className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Modus Operandi &amp; Forensic Root Cause</span>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-xs text-slate-300 whitespace-pre-line leading-relaxed font-mono">
                      {dossier.modus_operandi}
                    </div>
                  </div>

                  {/* Recommended Action Recommendation Banner */}
                  <div className="p-4 rounded-2xl bg-purple-950/40 border border-purple-700/60 flex items-center justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-mono text-purple-300 uppercase font-bold">
                        AI Recommended Determination
                      </div>
                      <div className="text-xs font-bold text-white mt-0.5">
                        {dossier.recommended_action}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => onDecisionApplied && onDecisionApplied('CONFIRMED_FRAUD')}
                        className="px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-md transition"
                      >
                        Confirm Fraud &amp; Freeze
                      </button>
                      <button
                        type="button"
                        onClick={() => onDecisionApplied && onDecisionApplied('GENUINE')}
                        className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition"
                      >
                        Mark Genuine
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: ATTACK ARCHITECTURE DIAGRAM */}
              {activeTab === 'diagram' && (
                <div className="space-y-4 animate-fadeIn">
                  {/* Interactive Attack Flow Visual Diagram */}
                  <div className="p-5 rounded-2xl bg-slate-900/90 border border-purple-800/60 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Workflow className="w-4 h-4 text-cyan-400" />
                        <h3 className="text-sm font-bold text-white">
                          End-to-End Attack &amp; Defense Barrier Diagram
                        </h3>
                      </div>
                      <span className="text-[10px] font-mono text-purple-300 bg-purple-950 px-2 py-0.5 rounded border border-purple-800">
                        Visual Kill-Chain
                      </span>
                    </div>

                    {/* Visual Flow Representation Boxes */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      {/* Box 1: Threat Origin */}
                      <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-600/80 space-y-1.5 shadow-md">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold text-rose-300 uppercase">1. Threat Origin</span>
                          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                        </div>
                        <div className="text-xs font-bold text-white">Compromised Session</div>
                        <p className="text-[11px] text-rose-200/80 leading-snug">
                          Untrusted client attempting unauthorized injection.
                        </p>
                      </div>

                      {/* Box 2: Payment Execution */}
                      <div className="p-3.5 rounded-xl bg-amber-950/60 border border-amber-600/80 space-y-1.5 shadow-md">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold text-amber-300 uppercase">2. Target Intent</span>
                          <span className="w-2 h-2 rounded-full bg-amber-500" />
                        </div>
                        <div className="text-xs font-bold text-white">Anomalous Spike</div>
                        <p className="text-[11px] text-amber-200/80 leading-snug">
                          High ticket attempt with zero prior merchant history.
                        </p>
                      </div>

                      {/* Box 3: AI Gatekeeper */}
                      <div className="p-3.5 rounded-xl bg-indigo-950/60 border border-indigo-600/80 space-y-1.5 shadow-md">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold text-indigo-300 uppercase">3. AI Gatekeeper</span>
                          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                        </div>
                        <div className="text-xs font-bold text-white">TreeSHAP &amp; Isolation</div>
                        <p className="text-[11px] text-indigo-200/80 leading-snug">
                          Interception in &lt;4ms. Risk scored at {dossier.risk_score}/100.
                        </p>
                      </div>

                      {/* Box 4: Protected Outcome */}
                      <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-600/80 space-y-1.5 shadow-md">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold text-emerald-300 uppercase">4. Outcome</span>
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        </div>
                        <div className="text-xs font-bold text-white">Asset Preservation</div>
                        <p className="text-[11px] text-emerald-200/80 leading-snug">
                          Zero funds lost. Card frozen pending customer verification.
                        </p>
                      </div>
                    </div>

                    {/* Raw Mermaid Syntax Box (For Evaluators/Presentation) */}
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono space-y-1">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Architecture Diagram Definition (Mermaid Syntax):</span>
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard?.writeText(dossier.attack_diagram_mermaid)
                            alert('Mermaid diagram code copied to clipboard!')
                          }}
                          className="text-cyan-400 hover:text-white underline text-[10px]"
                        >
                          Copy Diagram Code
                        </button>
                      </div>
                      <pre className="text-slate-300 whitespace-pre overflow-x-auto p-2 bg-slate-900 rounded-lg text-[10px]">
                        {dossier.attack_diagram_mermaid}
                      </pre>
                    </div>
                  </div>

                  {/* Kill-Chain Chronological Steps */}
                  <div className="space-y-2">
                    <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                      Attack Kill-Chain Phases
                    </div>
                    <div className="space-y-2">
                      {dossier.kill_chain?.map((step, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start justify-between gap-3 text-xs"
                        >
                          <div>
                            <div className="text-[10px] font-mono text-purple-400 font-bold">
                              {step.phase}
                            </div>
                            <div className="font-bold text-white mt-0.5">{step.title}</div>
                            <p className="text-[11px] text-slate-400 mt-0.5">{step.detail}</p>
                          </div>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 ${
                              step.severity === 'CRITICAL'
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : step.severity === 'WARNING'
                                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            }`}
                          >
                            {step.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: REGULATORY SAR REPORT */}
              {activeTab === 'sar' && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-purple-400" />
                        <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                          Ready-to-File Regulatory Suspicious Activity Report (SAR)
                        </h3>
                      </div>

                      <button
                        type="button"
                        onClick={handleCopySar}
                        className="px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 transition active:scale-95"
                      >
                        {copiedSar ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedSar ? 'Copied to Clipboard!' : 'Copy SAR Text'}</span>
                      </button>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-[350px] overflow-y-auto">
                      {dossier.regulatory_sar_draft}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between text-xs">
          <span className="text-[11px] text-slate-400 font-mono">
            FraudLens AI Copilot • Powered by Google Gemini &amp; TreeSHAP
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold transition"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  )
}
