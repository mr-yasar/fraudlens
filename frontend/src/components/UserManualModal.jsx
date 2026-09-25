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
} from 'lucide-react'

export default function UserManualModal({ isOpen, onClose, onOpenVoiceHelp }) {
  const [activeTab, setActiveTab] = useState('quickstart') // 'quickstart' | 'otp' | 'ai_copilot' | 'analyzer'

  if (!isOpen) return null

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
                FraudLens AI — Master Operations Manual
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                v2.6 Enterprise
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                ₹ INR
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Explainable AI, Phone SMS OTP Step-Up, Autonomous Forensic Copilot &amp; Siri/Google Voice Assistant.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 pb-1 border-b border-slate-800/80">
          {[
            { id: 'quickstart', label: '1. Quick Start & Roles', icon: Users },
            { id: 'otp', label: '2. Mobile Phone OTP Workflow', icon: Smartphone },
            { id: 'ai_copilot', label: '3. Admin AI Copilot & Voice', icon: Bot },
            { id: 'analyzer', label: '4. 29 Merchants & SHAP', icon: BrainCircuit },
          ].map((tab) => {
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

        {/* Tab 1: Access Architecture & Privacy Protection */}
        {activeTab === 'quickstart' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Data Privacy, Confidentiality &amp; Access Architecture
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                FraudLens AI strictly enforces enterprise confidentiality and row-level database isolation. <strong>Personal customer data, cardholder histories, and private credentials are never shared or accessible to unauthorized parties.</strong>
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs">
              {/* Customer Portal Space */}
              <div className="p-4 rounded-2xl bg-cyan-950/30 border border-cyan-800/50 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-cyan-300 flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-cyan-400" />
                    Customer Banking Portal
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-900/60 text-cyan-200 border border-cyan-700">
                    ISOLATED PRIVACY
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950/80 border border-cyan-900/40 text-[11px] space-y-1.5">
                  <div className="text-slate-300 font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Private Customer Data Scope</span>
                  </div>
                  <p className="text-slate-400 leading-relaxed">
                    Cardholders can <strong>only</strong> view their own payment transactions, personal spend velocity, and step-up security approvals. Access to any other customer's profile is strictly prohibited by database query filtering.
                  </p>
                </div>
                <ul className="text-[11px] text-slate-400 space-y-1 pl-1">
                  <li>• Encrypted token authentication with session-bound tokens</li>
                  <li>• Masked card numbers &amp; hashed customer identifiers</li>
                  <li>• Direct real-time SMS push notifications for suspicious activity</li>
                </ul>
              </div>

              {/* Admin Portal Space */}
              <div className="p-4 rounded-2xl bg-purple-950/30 border border-purple-800/50 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-purple-300 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-purple-400" />
                    Security Officer &amp; Admin Suite
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-900/60 text-purple-200 border border-purple-700">
                    FRAUD OPERATIONS
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950/80 border border-purple-900/40 text-[11px] space-y-1.5">
                  <div className="text-slate-300 font-semibold flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
                    <span>Merchant &amp; Attack Surveillance</span>
                  </div>
                  <p className="text-slate-400 leading-relaxed">
                    Security personnel monitor high-level merchant risk across all 29 master merchants, review explainable AI attributions, and adjudicate cases without exposing private customer credentials.
                  </p>
                </div>
                <ul className="text-[11px] text-slate-400 space-y-1 pl-1">
                  <li>• Multi-model AI Copilot (Gemini 1.5 Pro &amp; xAI Grok-2)</li>
                  <li>• Attack architecture diagrams &amp; Siri/Google voice briefings</li>
                  <li>• Regulatory Suspicious Activity Report (SAR) auto-drafting</li>
                </ul>
              </div>
            </div>

            {/* Privacy Compliance Banner */}
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <h4 className="font-bold text-slate-200 flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-400" />
                Zero Data Leakage &amp; Regulatory Compliance
              </h4>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                In compliance with global financial data protection standards (RBI Digital Payment Guidelines, PCI-DSS, and DPDP), FraudLens AI isolates telemetry at the service layer. No sensitive personal identifiable information (PII) is displayed in operational guides or shared across customer accounts.
              </p>
            </div>
          </div>
        )}

        {/* Tab 2: Mobile Phone OTP Workflow */}
        {activeTab === 'otp' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-cyan-400" />
                Live Mobile Phone SMS &amp; Step-Up OTP Verification
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                When an anomalous or high-risk transaction is submitted through the Payment Gateway, FraudLens triggers an interactive multi-factor challenge.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-300 font-bold text-xs">
                  1
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Realistic Smartphone SMS Notification</h4>
                  <p className="text-[11px] text-slate-400">
                    A phone push notification banner slides into view showing the real 6-digit security code (e.g. <span className="font-mono text-cyan-300">849201</span>), merchant name, and transaction amount in ₹ INR.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-300 font-bold text-xs">
                  2
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Interactive 6-Digit PIN Match</h4>
                  <p className="text-[11px] text-slate-400">
                    Enter the code into the auto-advancing verification boxes. The system verifies the code with strict matching and a 5-minute security countdown.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-300 font-bold text-xs">
                  3
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Dual Adjudication Outcomes</h4>
                  <p className="text-[11px] text-slate-400">
                    Click <strong>"Verify &amp; Authorize"</strong> to confirm the purchase and log the approval. Or click <strong>"Reject &amp; Freeze Account"</strong> if you suspect unauthorized access.
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Demo Pro-Tip */}
            <div className="p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-800/60 text-xs text-cyan-200 flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 text-cyan-300 shrink-0 mt-0.5" />
              <div>
                <strong>How to test this live:</strong> Go to <strong>Payment Gateway (Pre-Auth)</strong>, select <em>CircuitBay Electronics</em> or <em>Aurelia Gold House</em>, enter ₹75,000, and click <em>Pay &amp; Verify Risk Decision</em>.
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Admin AI Copilot & Voice */}
        {activeTab === 'ai_copilot' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Bot className="w-4 h-4 text-purple-400" />
                  Admin AI Copilot: Gemini, Grok, Siri Voice &amp; Attack Diagrams
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Located in Admin Mode under <strong>Fraud Investigations</strong> and directly accessible via the <strong>AI Voice Help</strong> button on any page.
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
              {/* Feature 1 */}
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-cyan-300 font-bold">
                  <Bot className="w-4 h-4" />
                  <span>Google Gemini &amp; xAI Grok Switcher</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Switch between <strong>Google Gemini 1.5 Pro</strong> (contextual root-cause attribution) and <strong>xAI Grok-2 Enterprise</strong> (adversarial botnet reasoning) with instant dossier re-synthesis.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-indigo-300 font-bold">
                  <Volume2 className="w-4 h-4" />
                  <span>Siri / Google Voice Spoken Briefings</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Click <strong>"Listen to Briefing"</strong> to hear natural spoken audio narration of the case, complete with animated neon soundwave visualizer and voice selection.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-purple-300 font-bold">
                  <Mic className="w-4 h-4" />
                  <span>Hands-Free Microphone Voice Commands</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Speak into your mic: <em>"Summarize case"</em>, <em>"Attack diagram"</em>, or <em>"Confirm fraud and freeze"</em> to operate case adjudications hands-free.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <GitBranch className="w-4 h-4" />
                  <span>4-Stage Attack Architecture Diagram</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Interactive Kill-Chain diagram mapping: <strong>Threat Origin &rarr; Target Intent &rarr; AI Gatekeeper &rarr; Outcome</strong>, with copyable Mermaid syntax for academic viva slides.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: 29 Merchants & SHAP */}
        {activeTab === 'analyzer' && (
          <div className="space-y-4 animate-fadeIn">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-cyan-400" />
                29 Master Merchants &amp; TreeSHAP Mathematical Attribution
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Every merchant profile has tailored ticket sizes, baseline transaction velocity, and historical fraud incidence.
              </p>
            </div>

            {/* Presets */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-emerald-950/30 border border-emerald-800/50 space-y-1">
                <strong className="text-emerald-400 block font-bold">Normal Household Purchase</strong>
                <p className="text-[11px] text-slate-400">
                  NovaMart Fresh (M001) for ₹1,250. Known mobile device, normal 2 PM hour, baseline velocity. Result: <strong>ALLOW</strong>.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-amber-950/30 border border-amber-800/50 space-y-1">
                <strong className="text-amber-400 block font-bold">Velocity Spike Anomaly</strong>
                <p className="text-[11px] text-slate-400">
                  CircuitBay Electronics (M002) for ₹45,000 at 3 AM with 8 txs in 1 hour. Result: <strong>REVIEW (Step-Up OTP)</strong>.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-rose-950/30 border border-rose-800/50 space-y-1">
                <strong className="text-rose-400 block font-bold">High-Value Account Takeover</strong>
                <p className="text-[11px] text-slate-400">
                  Aurelia Gold House (M004) for ₹85,000 with location jump and 3 failed logins. Result: <strong>BLOCK</strong>.
                </p>
              </div>
            </div>

            {/* TreeSHAP Explanation Bar Guide */}
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
            Close Operations Manual
          </button>
        </div>

      </div>
    </div>
  )
}
