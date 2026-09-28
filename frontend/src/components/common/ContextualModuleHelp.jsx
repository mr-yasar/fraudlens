import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Info, X, ShieldCheck, Zap, Sparkles } from 'lucide-react'

const CONTEXTUAL_HELP_DATA = {
  analyzer: {
    title: 'Transaction Risk Analyzer',
    badge: 'AI ML INFERENCE',
    summary: 'Evaluate prospective or simulated transactions in real time with TreeSHAP explainability.',
    points: [
      'Simulate any payment amount, merchant, and transfer channel.',
      'Calibrates risk against your personalized customer baseline.',
      'Computes a transparent 0–100 risk score and Low/Medium/High classification.',
      'TreeSHAP feature attributions show the exact factors driving the score.',
    ],
  },
  dashboard: {
    title: 'Executive Overview',
    badge: 'LIVE TELEMETRY',
    summary: 'High-level operational overview of account trust, active devices, and recent transactions.',
    points: [
      'Monitor real-time trust score and automated risk threshold status.',
      'View registered hardware devices and active session posture.',
      'Inspect recent financial activity and instant verification outcomes.',
      '1-click shortcuts to jump into deeper fraud investigations.',
    ],
  },
  payment: {
    title: 'Payment Gateway',
    badge: 'PRE-AUTH SHIELD',
    summary: 'Interactive financial checkout gateway with sub-millisecond AI pre-authorization.',
    points: [
      'Authorize real-time payments across 30 verified merchant profiles.',
      'Safe habitual transactions are auto-approved with zero friction.',
      'Anomalies trigger an instant cryptographic step-up verification challenge.',
      'Live risk signals update dynamically as transaction parameters change.',
    ],
  },
  'fleet-security': {
    title: 'Fleet & Device Security',
    badge: 'HARDWARE TRUST',
    summary: 'Hardware trust management for laptops, smartphones, biometric passkeys, and active sessions.',
    points: [
      'Inspect hardware device fingerprints, operating systems, and IP locations.',
      'Manage biometric passkeys (Apple Touch ID, Face ID, Windows Hello).',
      'Trust new verified devices with 1-click cryptographic binding.',
      'Instantly revoke lost hardware or terminate remote browser sessions.',
    ],
  },
  'live-monitor': {
    title: 'Live Radar & Cases',
    badge: 'GEOSPATIAL RADAR',
    summary: 'Live global transaction stream and forensic case investigation hub.',
    points: [
      'Track live financial transaction traffic across global locations in real time.',
      'Flagged cross-border spikes and velocity surges highlight instantly.',
      'Open full forensic investigation cases on suspicious patterns.',
      'Record investigator notes, assign statuses, and trigger mitigation.',
    ],
  },
  investigations: {
    title: 'Investigation Hub',
    badge: 'CASE MANAGEMENT',
    summary: 'Dedicated forensic workspace for resolving high-risk fraud cases.',
    points: [
      'Review queued transactions flagged by ML models or policy triggers.',
      'Examine complete device hashes, IP subnets, and prior sequences.',
      'Transition case status from Open to Investigating or Resolved.',
      'Generates immutable compliance records for banking audits.',
    ],
  },
  'executive-transactions': {
    title: 'Transactions & Scenarios',
    badge: 'ADAPTIVE ENGINE',
    summary: 'Live execution arena for testing standardized multi-signal enterprise scenarios.',
    points: [
      'Test normal spending, sudden location hops, and velocity surges in 1 click.',
      'Watch the risk engine request cryptographic OTP step-up challenges.',
      'View signed transaction records stored in your private encrypted partition.',
      'Zero data leakage guaranteed between different customer partitions.',
    ],
  },
  transactions: {
    title: 'Transaction History',
    badge: 'FINANCIAL LEDGER',
    summary: 'Complete historical database containing all verified past transactions.',
    points: [
      'Browse through all 1,500+ verified historical transaction records.',
      'Filter by risk level, prediction outcome, date, or merchant category.',
      'Search instantly by transaction ID, customer, or amount.',
      'Inspect deep timestamps, currency amounts, and fraud probabilities.',
    ],
  },
  'security-center': {
    title: 'Security Center',
    badge: 'ENCLAVE VAULT',
    summary: 'Personal cybersecurity headquarters managing enclave keys and threat mitigation.',
    points: [
      'Monitor multi-factor security posture and hardware key protection.',
      'Verify that cryptographic challenges and biometric gates are armed.',
      'Trigger instant account lockdown if suspicious activity is detected.',
      'Continuous 24/7 bank-grade protection with zero data leakage.',
    ],
  },
  'security-alerts': {
    title: 'Security Alerts',
    badge: 'INCIDENT RESPONSE',
    summary: 'Centralized alerting feed ranking real-time security events by severity.',
    points: [
      'Instant warnings for unauthorized logins, velocity spikes, and anomalies.',
      'Clear explanations indicate exactly why each alert was generated.',
      'Acknowledge alerts and jump directly into the linked transaction or device.',
      'Filter by Critical, Warning, or Info to prioritize threats.',
    ],
  },
  'audit-trail': {
    title: 'Compliance Audit Trail',
    badge: 'IMMUTABLE LOGS',
    summary: 'Tamper-proof permanent record of all logins, payments, and policy changes.',
    points: [
      'Every system action is timestamped and cryptographically logged.',
      'Secured by SHA-256 hashes for legal non-repudiation.',
      'Meets international banking compliance and ISO 27001 standards.',
      'Filter logs by action type or search for specific event references.',
    ],
  },
  'audit-logs': {
    title: 'Compliance Audit Trail',
    badge: 'IMMUTABLE LOGS',
    summary: 'Tamper-proof permanent record of all logins, payments, and policy changes.',
    points: [
      'Every system action is timestamped and cryptographically logged.',
      'Secured by SHA-256 hashes for legal non-repudiation.',
      'Meets international banking compliance and ISO 27001 standards.',
      'Filter logs by action type or search for specific event references.',
    ],
  },
  'ai-copilot': {
    title: 'AI Security Assistant',
    badge: 'FINTECH AGENT',
    summary: 'Specialized generative AI assistant for conversational fraud analysis and advice.',
    points: [
      'Ask any question in plain English about transactions or security status.',
      'Explains complex risk signals, merchant risks, and security policies clearly.',
      'Optional natural voice audio synthesis for hands-free listening.',
      'Provides actionable recommendations to strengthen your account defense.',
    ],
  },
  merchants: {
    title: 'Merchant Intelligence',
    badge: 'COMMERCE INTEL',
    summary: 'Comprehensive directory of 30 verified master merchant profiles.',
    points: [
      'Inspect master merchants across retail, travel, tech, and bullion.',
      'Check historical fraud rates, ticket averages, and MCC risk tiers.',
      'Understand how merchant category and location impact fraud risk.',
      'Protects you from high-risk or fraudulent billing entities.',
    ],
  },
  'explainable-ai': {
    title: 'Explainable AI & SHAP',
    badge: 'INTERPRETABILITY',
    summary: 'Mathematical feature attribution demonstrating global model weights and decisions.',
    points: [
      'Eliminates black-box mysteries using game-theoretic SHAP mathematics.',
      'Shows which features have the strongest global impact on fraud detection.',
      'Interactive waterfall charts dissect individual decision factors.',
      'Guarantees that AI decisions are transparent, fair, and compliant.',
    ],
  },
  'model-lab': {
    title: 'Model Lab & Registry',
    badge: 'ML GOVERNANCE',
    summary: 'Benchmarking studio comparing LightGBM, XGBoost, and CatBoost models.',
    points: [
      'Compare performance metrics, ROC-AUC curves, and inference latencies.',
      'Test decision sensitivity across customized risk thresholds.',
      'Promote newly calibrated models to active production safely.',
      'Maintains a reliable, razor-sharp fraud prediction engine.',
    ],
  },
  'dataset-health': {
    title: 'Dataset Health',
    badge: 'DATA INTEGRITY',
    summary: 'Real-time telemetry on dataset hygiene, partition boundaries, and class balance.',
    points: [
      'Inspect missing values, duplicates, and feature distribution skewness.',
      'Verifies zero data leakage between customer partitions.',
      'Confirms the dataset maintains pure 0.2% anomaly calibration.',
      'Ensures models are trained on pristine, untainted records.',
    ],
  },
  settings: {
    title: 'Platform Settings',
    badge: 'CONFIG MATRIX',
    summary: 'Personal and system configuration for fraud thresholds and preferences.',
    points: [
      'Adjust sensitivity thresholds for automated step-up challenges.',
      'Configure notification channels and webhook integrations.',
      'Customize themes, audio synthesizer volume, and display formats.',
      'Export system configuration snapshots for audit records.',
    ],
  },
}

export default function ContextualModuleHelp({ moduleKey = 'analyzer', className = '' }) {
  const [isOpen, setIsOpen] = useState(false)
  const data = CONTEXTUAL_HELP_DATA[moduleKey] || CONTEXTUAL_HELP_DATA.analyzer

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape' && isOpen) setIsOpen(false)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen])

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  const modalContent = isOpen ? (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={`module-help-title-${moduleKey}`}
      className="fixed inset-0 z-[99999] flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md transition-all duration-300 animate-fade-in"
      onClick={() => setIsOpen(false)}
      onTouchEnd={(e) => {
        if (e.target === e.currentTarget) setIsOpen(false)
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        onTouchEnd={(e) => e.stopPropagation()}
        className="relative w-full max-w-md max-h-[85vh] overflow-y-auto rounded-2xl bg-slate-900/95 border border-slate-700/80 p-5 sm:p-6 shadow-[0_25px_60px_rgba(0,0,0,0.9),0_0_30px_rgba(6,182,212,0.25)] text-left animate-scale-in space-y-4 text-slate-100"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700/60 font-bold uppercase">
                {data.badge}
              </span>
              <span className="text-[10px] font-mono text-slate-400">CONTEXTUAL GUIDE</span>
            </div>
            <h4 id={`module-help-title-${moduleKey}`} className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0" />
              <span>{data.title}</span>
            </h4>
          </div>

          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            aria-label="Close module info popup"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Summary */}
        <p className="text-xs sm:text-sm text-slate-300 font-medium leading-relaxed">
          {data.summary}
        </p>

        {/* Key Points */}
        <div className="space-y-2 pt-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold flex items-center gap-1">
            <Zap className="w-3 h-3 text-cyan-400" />
            WHAT YOU CAN DO &amp; CONTROLS:
          </div>
          <div className="space-y-2 text-xs sm:text-sm text-slate-300 leading-snug">
            {data.points.map((pt, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                <span>{pt}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
          <span className="text-[10px] font-mono text-slate-400">FraudLens AI Contextual Help</span>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition cursor-pointer shadow-md"
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  ) : null

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      {/* Contextual Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="p-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-cyan-300 border border-slate-700/80 hover:border-cyan-500/60 transition shadow-sm flex items-center gap-1 group cursor-pointer"
        title={`What this ${data.title} module does`}
        aria-label={`Open help for ${data.title}`}
      >
        <span className="w-3.5 h-3.5 rounded-full bg-cyan-950 border border-cyan-500/60 text-cyan-300 text-[10px] font-mono font-bold flex items-center justify-center group-hover:scale-110 transition-transform">
          i
        </span>
        <span className="text-[11px] font-mono text-slate-300 group-hover:text-white hidden sm:inline">
          Module Info
        </span>
      </button>

      {/* Render Modal into Portal */}
      {typeof document !== 'undefined' && modalContent && createPortal(modalContent, document.body)}
    </div>
  )
}
