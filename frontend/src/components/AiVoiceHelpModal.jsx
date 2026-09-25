import React, { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  Bot,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Play,
  Pause,
  Square,
  X,
  HelpCircle,
  BrainCircuit,
  ShieldCheck,
  ShieldAlert,
  Smartphone,
  Send,
  RefreshCw,
  GitBranch,
  Layers,
  ArrowRight,
  CheckCircle2,
  Zap,
} from 'lucide-react'
import { investigationsApi } from '../services/api'

export default function AiVoiceHelpModal({ isOpen, onClose }) {
  const [topic, setTopic] = useState('what_is_fraud')
  const [provider, setProvider] = useState('gemini') // 'gemini' | 'grok' | 'claude'
  const [loading, setLoading] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [error, setError] = useState(null)
  const [customInput, setCustomInput] = useState('')

  // Speech Synthesis state (Siri / Google Voice)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [voiceVoice, setVoiceVoice] = useState(null)
  const [availableVoices, setAvailableVoices] = useState([])
  const [voiceSpeed, setVoiceSpeed] = useState(1.0)

  // Speech Recognition state (Voice Commands)
  const [isListening, setIsListening] = useState(false)
  const [voiceTranscript, setVoiceTranscript] = useState('')
  const recognitionRef = useRef(null)

  // Initialize Speech Synthesis Voices
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices()
        setAvailableVoices(voices)
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
          const transcript = event.results[0][0].transcript.trim()
          setVoiceTranscript(transcript)
          setIsListening(false)
          handleAskCustom(transcript)
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
  }, [provider])

  // Stop speaking when modal closes
  useEffect(() => {
    if (!isOpen && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      setIsPaused(false)
    }
  }, [isOpen])

  // Fetch explanation when topic or provider changes
  useEffect(() => {
    if (isOpen) {
      fetchExplanation(topic, null, provider)
    }
  }, [isOpen, topic, provider])

  const fetchExplanation = async (topicKey, query = null, prov = provider) => {
    setLoading(true)
    setError(null)
    handleStopSpeech()
    try {
      const data = await investigationsApi.getAiVoiceHelp(topicKey, query, prov)
      setExplanation(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI synthesis failed')
    } finally {
      setLoading(false)
    }
  }

  const handleAskCustom = (queryText) => {
    const text = queryText || customInput
    if (!text || text.trim().length < 2) return
    fetchExplanation('custom_query', text.trim(), provider)
  }

  // Voice Narration (Text-to-Speech)
  const handleToggleSpeak = () => {
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

    const script = explanation?.voice_narration_script || explanation?.summary
    if (!script) return

    window.speechSynthesis.cancel()
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
    }
    setIsSpeaking(false)
    setIsPaused(false)
  }

  const handleToggleMic = () => {
    if (!recognitionRef.current) {
      alert('Speech Recognition is supported in Chrome, Edge, and Safari.')
      return
    }

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      handleStopSpeech()
      setVoiceTranscript('')
      try {
        recognitionRef.current.start()
        setIsListening(true)
      } catch (err) {
        setIsListening(false)
      }
    }
  }

  if (!isOpen) return null

  const topicsList = [
    { id: 'what_is_fraud', label: '1. What is Fraud?', icon: HelpCircle, desc: 'Core definition & digital UPI threats' },
    { id: 'attack_vectors', label: '2. Attack Vectors & Botnets', icon: ShieldAlert, desc: 'ATO, carding & money mules' },
    { id: 'how_ai_detects', label: '3. How AI Detects Fraud', icon: BrainCircuit, desc: 'Pre-auth sub-4ms & 4 ML models' },
    { id: 'treeshap_explained', label: '4. TreeSHAP Game Theory', icon: Sparkles, desc: 'Mathematical explainability' },
    { id: 'customer_personas', label: '5. The 3 Customer Personas', icon: Layers, desc: 'Monisha 3%, Mohana 12%, Sowmiya 26%' },
    { id: 'otp_step_up', label: '6. Mobile Phone OTP Step-Up', icon: Smartphone, desc: 'Frictionless adaptive challenge' },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md animate-fadeIn">
      <div className="max-w-5xl w-full rounded-3xl bg-slate-900 border-2 border-cyan-500/70 shadow-[0_0_60px_rgba(6,182,212,0.35)] flex flex-col max-h-[92vh] overflow-hidden text-slate-200">
        
        {/* Top Header Bar */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/80 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 text-white shadow-lg shadow-cyan-500/30 animate-pulse">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                  FraudLens AI Assistant &amp; Voice Help
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                  Siri &amp; Google Voice
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Autonomous GenAI Explainer: Learn What is Fraud, TreeSHAP &amp; Real-Time Risk with Voice
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* AI Provider Switcher (Gemini / Grok) */}
            <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-700/80 text-xs">
              <button
                onClick={() => setProvider('gemini')}
                className={`px-3 py-1 rounded-lg font-bold transition flex items-center gap-1.5 ${
                  provider === 'gemini'
                    ? 'bg-cyan-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Google Gemini</span>
              </button>
              <button
                onClick={() => setProvider('grok')}
                className={`px-3 py-1 rounded-lg font-bold transition flex items-center gap-1.5 ${
                  provider === 'grok'
                    ? 'bg-purple-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Bot className="w-3.5 h-3.5" />
                <span>xAI Grok-2</span>
              </button>
            </div>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
              aria-label="Close Voice Help"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Voice Control Bar (Siri / Google Voice & Microphone) */}
        <div className="px-6 py-3 bg-gradient-to-r from-slate-950 via-cyan-950/30 to-slate-950 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
              <Volume2 className="w-4 h-4 text-cyan-400" />
              Voice Copilot:
            </span>

            {/* Listen / Pause */}
            <button
              onClick={handleToggleSpeak}
              disabled={loading || !explanation}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-md transition ${
                isSpeaking && !isPaused
                  ? 'bg-amber-600 hover:bg-amber-500 text-white animate-pulse'
                  : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white'
              }`}
            >
              {isSpeaking && !isPaused ? (
                <>
                  <Pause className="w-3.5 h-3.5" />
                  <span>Pause Spoken Briefing</span>
                </>
              ) : isPaused ? (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Resume Spoken Briefing</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Listen to Spoken Voice Briefing</span>
                </>
              )}
            </button>

            {/* Stop Speech */}
            {isSpeaking && (
              <button
                onClick={handleStopSpeech}
                className="p-1.5 rounded-xl bg-rose-950 hover:bg-rose-900 border border-rose-800 text-rose-300 transition"
                title="Stop Speech"
              >
                <Square className="w-3.5 h-3.5" />
              </button>
            )}

            {/* Soundwave Visualizer when speaking */}
            {isSpeaking && !isPaused && (
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-cyan-950/60 border border-cyan-800/80">
                <span className="w-1 h-3.5 bg-cyan-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1 h-5 bg-cyan-300 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1 h-2 bg-cyan-400 rounded-full animate-bounce [animation-delay:300ms]" />
                <span className="w-1 h-6 bg-cyan-200 rounded-full animate-bounce [animation-delay:450ms]" />
                <span className="w-1 h-3 bg-cyan-400 rounded-full animate-bounce [animation-delay:600ms]" />
                <span className="text-[10px] font-mono text-cyan-300 ml-1.5 font-bold">SPEAKING</span>
              </div>
            )}
          </div>

          {/* Microphone Speech Recognition Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleToggleMic}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-bold border transition ${
                isListening
                  ? 'bg-rose-600 text-white border-rose-400 shadow-lg shadow-rose-500/30 animate-pulse'
                  : 'bg-slate-800 hover:bg-slate-700 text-cyan-300 border-slate-700'
              }`}
            >
              {isListening ? (
                <>
                  <Mic className="w-4 h-4 text-white animate-spin" />
                  <span>Listening... Speak Now!</span>
                </>
              ) : (
                <>
                  <Mic className="w-4 h-4 text-cyan-400" />
                  <span>Voice Command (Speak Question)</span>
                </>
              )}
            </button>

            {/* Voice Speed Selector */}
            <select
              value={voiceSpeed}
              onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
              className="bg-slate-900 border border-slate-700 text-slate-300 text-[11px] rounded-lg px-2 py-1 focus:ring-1 focus:ring-cyan-500"
              title="Voice Speed"
            >
              <option value="0.85">0.85x Speed</option>
              <option value="1.0">1.0x Normal</option>
              <option value="1.2">1.2x Fast</option>
            </select>
          </div>
        </div>

        {/* Voice Feedback Banner */}
        {voiceTranscript && (
          <div className="px-6 py-2 bg-indigo-950/70 border-b border-indigo-800 text-xs text-indigo-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mic className="w-3.5 h-3.5 text-indigo-400" />
              <span>Voice Question Heard: <strong>&ldquo;{voiceTranscript}&rdquo;</strong></span>
            </div>
            <span className="text-[10px] text-indigo-300 font-mono">Synthesizing AI Answer...</span>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-5">
          
          {/* Left Column: Topics Sidebar */}
          <div className="lg:col-span-4 space-y-3">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
              Interactive Topics
            </h3>

            <div className="space-y-2">
              {topicsList.map((t) => {
                const Icon = t.icon
                const isActive = topic === t.id
                return (
                  <button
                    key={t.id}
                    onClick={() => {
                      setTopic(t.id)
                      setCustomInput('')
                    }}
                    className={`w-full text-left p-3 rounded-2xl border transition group ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-950 to-blue-950 border-cyan-500 text-white shadow-md'
                        : 'bg-slate-950/60 hover:bg-slate-800/60 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 mb-1">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-cyan-400'}`} />
                      <span className="text-xs font-bold">{t.label}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 pl-6 leading-relaxed">
                      {t.desc}
                    </p>
                  </button>
                )
              })}
            </div>

            {/* Ask Custom Question Box */}
            <div className="pt-2">
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-300">
                  <Bot className="w-3.5 h-3.5" />
                  <span>Ask AI Custom Question:</span>
                </div>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAskCustom(customInput)}
                    placeholder="e.g. What is an anomaly score?"
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={() => handleAskCustom(customInput)}
                    disabled={!customInput.trim()}
                    className="p-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50 transition"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: AI Explanation & Diagram */}
          <div className="lg:col-span-8 space-y-4">
            {loading ? (
              <div className="h-72 flex flex-col items-center justify-center gap-3 text-cyan-400">
                <RefreshCw className="w-8 h-8 animate-spin" />
                <span className="text-xs font-mono font-bold tracking-wider">
                  {provider === 'grok' ? 'xAI Grok-2' : 'Google Gemini 1.5 Pro'} Synthesizing Voice Dossier...
                </span>
              </div>
            ) : error ? (
              <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
                {error}
              </div>
            ) : explanation ? (
              <div className="space-y-4 animate-fadeIn">
                {/* Title Card */}
                <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                      {explanation.provider}
                    </span>
                    <button
                      onClick={handleToggleSpeak}
                      className="text-xs font-bold text-cyan-400 hover:text-cyan-300 flex items-center gap-1.5"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                      <span>{isSpeaking ? 'Pause Voice' : 'Play Voice Narration'}</span>
                    </button>
                  </div>

                  <h3 className="text-base font-black text-white">
                    {explanation.title}
                  </h3>
                  <p className="text-xs text-cyan-400 font-medium">
                    {explanation.subtitle}
                  </p>

                  <p className="text-xs text-slate-300 leading-relaxed pt-1">
                    {explanation.summary}
                  </p>
                </div>

                {/* Key Points */}
                {explanation.key_points && explanation.key_points.length > 0 && (
                  <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-2.5">
                    <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Key Principles &amp; Takeaways
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {explanation.key_points.map((pt, i) => (
                        <div key={i} className="flex items-start gap-2.5 text-xs text-slate-300 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
                          <span className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          <span className="leading-relaxed">{pt}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Spoken Voice Script Card */}
                {explanation.voice_narration_script && (
                  <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-slate-950 border border-indigo-800/60 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-bold text-indigo-300">
                        <Volume2 className="w-4 h-4 text-indigo-400" />
                        <span>Siri / Google Spoken Script</span>
                      </div>
                      <button
                        onClick={handleToggleSpeak}
                        className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold transition flex items-center gap-1"
                      >
                        <Play className="w-3 h-3" />
                        <span>{isSpeaking ? 'Playing' : 'Listen Now'}</span>
                      </button>
                    </div>
                    <blockquote className="text-xs text-indigo-100 italic bg-indigo-950/40 p-3 rounded-xl border border-indigo-900/50 leading-relaxed font-mono">
                      &ldquo;{explanation.voice_narration_script}&rdquo;
                    </blockquote>
                  </div>
                )}
              </div>
            ) : null}
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-950 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>FraudLens AI Voice Suite • Speech Recognition &amp; Web Speech Synthesis Active</span>
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  )
}
