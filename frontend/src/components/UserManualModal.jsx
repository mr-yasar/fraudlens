import React, { useState } from 'react'
import {
  BookOpen,
  X,
  Store,
  BrainCircuit,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Zap,
  Sparkles,
  Users,
  Search,
  HelpCircle,
  IndianRupee,
  Radio,
  Cpu,
  Database,
  Smartphone,
  Bot,
  Volume2,
  Mic,
  GitBranch,
  FileText,
  KeyRound,
  ShieldAlert,
  ArrowRight,
  Clock,
  ExternalLink,
  Lock,
  UserCheck,
} from 'lucide-react'
import { getCustomerPersona } from '../utils/customerHelper'

export default function UserManualModal({ isOpen, onClose, onOpenVoiceHelp, user, isAdmin }) {
  const isCustomer = !isAdmin && (user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user')
  const customerPersona = getCustomerPersona(user)

  // Default active tab based on role
  const [activeTab, setActiveTab] = useState(isCustomer ? 'cust_security' : 'quickstart')

  if (!isOpen) return null

  // Customer navigation tabs (Strictly isolated - No cross-customer fraud rates)
  const customerTabs = [
    { id: 'cust_security', label: '1. Account Privacy & Security', icon: ShieldCheck },
    { id: 'cust_otp', label: '2. Mobile Phone OTP Verification', icon: Smartphone },
    { id: 'cust_xai', label: '3. Explainable AI & Receipts', icon: BrainCircuit },
    { id: 'cust_voice', label: '4. Sweet AI Voice Assistant', icon: Volume2 },
  ]

  // Admin navigation tabs (Enterprise overview & 29 merchants)
  const adminTabs = [
    { id: 'quickstart', label: '1. Governance & Privacy Architecture', icon: Users },
    { id: 'otp', label: '2. Mobile Phone OTP Workflow', icon: Smartphone },
    { id: 'ai_copilot', label: '3. Admin AI Copilot & Voice', icon: Bot },
    { id: 'analyzer', label: '4. 29 Merchants & SHAP Benchmark', icon: BrainCircuit },
  ]

  const currentTabs = isCustomer ? customerTabs : adminTabs

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fadeIn">
      <div className="max-w-4xl w-full rounded-3xl bg-slate-900 border-2 border-cyan-500/60 shadow-[0_0_50px_rgba(6,182,212,0.35)] p-5 sm:p-7 space-y-5 max-h-[92vh] overflow-y-auto relative text-slate-200">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
          aria-label="Close user guide"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3.5 pb-4 border-b border-slate-800">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 text-white shadow-lg shadow-cyan-500/30">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-white tracking-tight">
                {isCustomer
                  ? `FraudLens AI — Customer Security Guide (${customerPersona.name})`
                  : 'FraudLens AI — Master Operations Manual'}
              </h2>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                isCustomer
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
              }`}>
                {isCustomer ? 'Private Account Portal' : 'v2.6 Enterprise'}
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                ₹ INR
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {isCustomer
                ? 'Your personal security guide: Private account isolation, instant phone SMS OTP, and transparent AI receipts.'
                : 'Explainable AI, Phone SMS OTP Step-Up, Autonomous Forensic Copilot & Siri/Google Voice Assistant.'}
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 pb-1 border-b border-slate-800/80">
          {currentTabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-950/60'
                    : 'bg-slate-950/60 text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-cyan-400'}`} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* ========================================================================= */}
        {/* CUSTOMER TABS (Strict Privacy - Zero other customer data visible)         */}
        {/* ========================================================================= */}

        {/* Customer Tab 1: Privacy & Security */}
        {isCustomer && activeTab === 'cust_security' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-800/50 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <ShieldCheck className="w-5 h-5" />
                <span>Strict Personal Account Privacy &amp; Data Encryption</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Welcome, <strong>{customerPersona.name}</strong>. FraudLens AI operates under bank-grade zero-trust privacy.
                Your account identifier (<code>{customerPersona.customerId}</code>), transaction histories, card tokens, and risk evaluations
                are strictly isolated. <strong>No other customer can ever see your transactions, account balance, or security records.</strong>
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-cyan-300 font-bold">
                  <Lock className="w-4 h-4" />
                  <span>Row-Level Database Isolation</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Every query executed by your session is cryptographically scoped to your user ID. Cross-tenant queries are blocked at the database kernel.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <UserCheck className="w-4 h-4" />
                  <span>Sub-4ms Pre-Authorization Protection</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Every payment intent you initiate is analyzed in real-time. Safe routine purchases approve immediately with zero interruption.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Customer Tab 2: Mobile Phone OTP */}
        {isCustomer && activeTab === 'cust_otp' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-cyan-400" />
                How Your Mobile Phone OTP Protects Your Money
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                FraudLens AI uses adaptive authentication so you are not bothered with passwords on safe routine purchases.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="text-cyan-400 font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>1. Safe Payments</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Routine groceries or known merchant payments from your usual device approve immediately in under 4ms.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-amber-950/30 border border-amber-800/50 space-y-1.5">
                <div className="text-amber-400 font-bold flex items-center gap-1.5">
                  <Smartphone className="w-4 h-4" />
                  <span>2. Phone SMS Alert</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  If an unusual high-value transaction or unfamiliar device appears, an instant 6-digit SMS OTP is sent to your phone.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-emerald-950/30 border border-emerald-800/50 space-y-1.5">
                <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  <span>3. Money Protected</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Funds remain safely locked in escrow until you verify the exact 6-digit code on your screen.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Customer Tab 3: Explainable AI & Receipts */}
        {isCustomer && activeTab === 'cust_xai' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-purple-400" />
                Transparent AI Receipts: Know Exactly Why Any Payment Was Evaluated
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Under <strong>Explainable AI &amp; SHAP</strong>, you can view the exact mathematical reasons behind any of your transactions.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-emerald-950/30 border border-emerald-800/50 space-y-1.5">
                <strong className="text-emerald-400 block font-bold">🟢 Green Protective Factors (Low Risk)</strong>
                <p className="text-[11px] text-slate-300">
                  Signals like transacting from your verified smartphone, familiar daytime hours, normal merchant category, and good account tenure pull your risk down.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-rose-950/30 border border-rose-800/50 space-y-1.5">
                <strong className="text-rose-400 block font-bold">🔴 Red Risk Factors (Triggers Alert)</strong>
                <p className="text-[11px] text-slate-300">
                  Signals like sudden midnight checkout, untrusted browser, high transaction velocity, or unusual ticket size push the risk up to protect you from theft.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Customer Tab 4: Sweet AI Voice Assistant */}
        {isCustomer && activeTab === 'cust_voice' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Volume2 className="w-4 h-4 text-cyan-400" />
                  Sweet AI Voice Assistant: Hear Your Transaction Explanations
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Enjoy warm, crystal-clear spoken voice explanations of your payments and security status.
                </p>
              </div>

              {onOpenVoiceHelp && (
                <button
                  type="button"
                  onClick={() => {
                    onClose && onClose()
                    onOpenVoiceHelp()
                  }}
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-md shadow-purple-950/50 transition flex items-center gap-1.5"
                >
                  <Bot className="w-3.5 h-3.5 animate-pulse" />
                  <span>Launch Voice Assistant</span>
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-cyan-300 font-bold">
                  <Volume2 className="w-4 h-4" />
                  <span>Listen to Spoken Receipts</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  In <strong>Explainable AI &amp; SHAP</strong>, click <strong>"Listen to AI Voice Explanation"</strong> to hear a sweet, friendly voice explaining your transaction.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-purple-300 font-bold">
                  <Mic className="w-4 h-4" />
                  <span>Speak Hands-Free Questions</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Click the microphone icon and ask: <em>"What is fraud?"</em> or <em>"Is my account safe?"</em> to receive an instant spoken answer.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* ADMIN TABS (Enterprise Governance, 29 Merchants & Persona Stress-Testing) */}
        {/* ========================================================================= */}

        {/* Tab 1: Access Architecture & Privacy Protection (Admin View) */}
        {!isCustomer && activeTab === 'quickstart' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Enterprise Data Privacy, Confidentiality &amp; Access Architecture
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                FraudLens AI strictly enforces enterprise confidentiality and row-level database isolation. <strong>Personal customer data, cardholder histories, and private credentials are never shared across tenants.</strong>
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-cyan-300 font-bold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Administrator &amp; Security Analyst Access</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Oversees platform health, 29 merchant risk scores, multi-model tournaments, and investigation case queues. 
                  Audit trails are cryptographically immutable.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <UserCheck className="w-4 h-4" />
                  <span>Customer Isolated Portal</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Individual customers only have visibility into their own transactions, personal risk score, and real-time security alerts with zero cross-tenant leakage.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Mobile Phone OTP Workflow (Admin View) */}
        {!isCustomer && activeTab === 'otp' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-cyan-400" />
                Phone SMS OTP Step-Up Authentication Workflow
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Transactions scoring between 30 and 70 risk points trigger an automatic real-time Mobile SMS OTP challenge.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-cyan-300 font-bold">
                  <Smartphone className="w-4 h-4" />
                  <span>1. Real-Time Phone SMS Dispatched</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  When a payment intent is flagged as <strong>REVIEW</strong>, an SMS alert is dispatched with a unique 6-digit code.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>2. Strict PIN Matching</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Customer enters the exact code on their phone simulator. If valid, the payment intent commits immediately.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Admin AI Copilot & Voice */}
        {!isCustomer && activeTab === 'ai_copilot' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Bot className="w-4 h-4 text-purple-400" />
                  Admin AI Copilot: Gemini, Grok, Siri Voice &amp; Attack Diagrams
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Located under <strong>Fraud Investigations</strong> and directly accessible via the <strong>AI Voice Help</strong> button anytime.
                </p>
              </div>

              {onOpenVoiceHelp && (
                <button
                  type="button"
                  onClick={() => {
                    onClose && onClose()
                    onOpenVoiceHelp()
                  }}
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-md shadow-purple-950/50 transition flex items-center gap-1.5"
                >
                  <Bot className="w-3.5 h-3.5 animate-pulse" />
                  <span>Launch Voice Copilot &amp; What is Fraud?</span>
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-cyan-300 font-bold">
                  <Bot className="w-4 h-4" />
                  <span>Google Gemini &amp; xAI Grok Switcher</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Switch between <strong>Google Gemini 1.5 Pro</strong> and <strong>xAI Grok-2 Enterprise</strong> with instant dossier re-synthesis.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-indigo-300 font-bold">
                  <Volume2 className="w-4 h-4" />
                  <span>Siri / Google Voice Spoken Briefings</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Hear natural spoken audio narration of the case, complete with animated neon soundwave visualizer.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: 29 Merchants & SHAP Benchmark (Admin View) */}
        {!isCustomer && activeTab === 'analyzer' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-cyan-400" />
                29 Master Merchants &amp; TreeSHAP Mathematical Attribution
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Every merchant profile has tailored ticket sizes, baseline transaction velocity, and historical fraud incidence across 10 categories.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <h4 className="font-bold text-slate-200 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                How to Read the SHAP Waterfall Contributions
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                <div className="p-2.5 rounded-xl bg-rose-950/30 border border-rose-900/50 text-rose-300">
                  <strong className="block font-bold mb-0.5">🔴 Red Bars (+ Pushing Risk UP)</strong>
                  Elevated transaction amount vs merchant average, untrusted device fingerprint, rapid transaction velocity, or midnight hour.
                </div>
                <div className="p-2.5 rounded-xl bg-emerald-950/30 border border-emerald-900/50 text-emerald-300">
                  <strong className="block font-bold mb-0.5">🟢 Green Bars (- Pushing Risk DOWN)</strong>
                  Trusted known device, matching residential geography, established account tenure, and zero failed logins.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer Action */}
        <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
          <div className="text-[11px] text-slate-400 font-mono">
            Tip: Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">ESC</kbd> or click below to close
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-2xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-cyan-950/50 transition uppercase tracking-wider"
          >
            Close Guide
          </button>
        </div>

      </div>
    </div>
  )
}
