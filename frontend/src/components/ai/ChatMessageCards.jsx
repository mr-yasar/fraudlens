import React, { useState } from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Copy,
  Check,
  Cpu,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

/**
 * ChatMessageCards — Structured, evidence-aware insight widgets.
 *
 * Visual Direction:
 * - Deep dark-blue background + warm ivory and cool-white highlights
 * - Soft frosted top reflections (border-t-white/30)
 * - Section 31 Compliance:
 *   - Fraud Probability (0-100%) != Risk Score (0-100)
 *   - TreeSHAP Explanation != Causality
 *   - Model Prediction != Factual Confirmation
 *   - Zero Secrets Leakage
 */

export function ProviderTelemetryBadge({ provider, model, usedRealApi }) {
  const provLower = (provider || '').toLowerCase()
  const isFailover = provLower.includes('failover')
  const isDeep = provLower.includes('3.7') || provLower.includes('deep')
  const isGrok = provLower.includes('grok')
  const isMistral = provLower.includes('mistral')

  let badgeColor = 'bg-cyan-950/90 text-cyan-200 border-cyan-500/40 shadow-sm'
  let icon = <Sparkles className="w-3 h-3 text-cyan-400" />

  if (isFailover) {
    badgeColor = 'bg-amber-950/90 text-amber-200 border-amber-500/50 shadow-sm'
    icon = <AlertTriangle className="w-3 h-3 text-amber-400" />
  } else if (isDeep) {
    badgeColor = 'bg-blue-950/90 text-blue-200 border-blue-400/50 shadow-sm'
    icon = <Cpu className="w-3 h-3 text-blue-300" />
  } else if (isGrok) {
    badgeColor = 'bg-indigo-950/90 text-indigo-200 border-indigo-400/50 shadow-sm'
    icon = <Layers className="w-3 h-3 text-indigo-300" />
  } else if (isMistral) {
    badgeColor = 'bg-violet-950/90 text-violet-200 border-violet-400/50 shadow-sm'
    icon = <Sparkles className="w-3 h-3 text-violet-300" />
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5 mt-2 pt-2 border-t border-white/10 text-[10px] font-mono">
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-semibold ${badgeColor}`}>
        {icon}
        <span>{provider || 'Google Gemini'}</span>
      </span>
      {model && (
        <span className="text-slate-300 px-1.5 py-0.5 rounded bg-[#070d1e] border border-white/10">
          model: <strong className="text-[#fefae0]">{model}</strong>
        </span>
      )}
      <span className="text-emerald-400 px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-700/60 font-bold">
        {usedRealApi ? 'Verified Real API' : 'Simulated Telemetry'}
      </span>
    </div>
  )
}

export function TransactionAnalysisCard({ transaction, onAction }) {
  if (!transaction) return null
  const isHighRisk = (transaction.risk_score || 0) >= 70 || transaction.decision === 'BLOCKED'

  return (
    <div className="my-2 p-3.5 rounded-2xl bg-[#0b142d]/95 border border-white/15 border-t-white/30 text-xs font-mono shadow-xl backdrop-blur-xl relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
        <span className="font-bold text-white flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[#fefae0]">TXN: {transaction.id || transaction.transaction_id || 'TXN-EVIDENCE'}</span>
        </span>
        <span
          className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${
            isHighRisk
              ? 'bg-rose-950/90 text-rose-300 border-rose-500/50 shadow-[0_0_8px_rgba(244,63,94,0.3)]'
              : 'bg-emerald-950/90 text-emerald-300 border-emerald-500/50'
          }`}
        >
          {transaction.decision || (isHighRisk ? 'BLOCKED' : 'APPROVED')}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300 mb-2.5">
        <div>
          <span className="text-slate-400 text-[10px] block">Amount:</span>
          <span className="text-[#fefae0] font-black text-sm">{transaction.amount || '₹84,200.00'}</span>
        </div>
        <div>
          <span className="text-slate-400 text-[10px] block">Merchant:</span>
          <span className="text-cyan-200 truncate block font-semibold">{transaction.merchant || 'Global Crypto Exchange'}</span>
        </div>
        <div>
          <span className="text-slate-400 text-[10px] block">1h Velocity:</span>
          <span className="text-amber-300 font-bold">{transaction.velocity || '4 txn/10 min'}</span>
        </div>
        <div>
          <span className="text-slate-400 text-[10px] block">Location Distance:</span>
          <span className="text-slate-200">{transaction.location || '1,420 km from usual IP'}</span>
        </div>
      </div>

      {onAction && (
        <div className="flex items-center gap-1.5 pt-2 border-t border-white/10">
          <button
            onClick={() => onAction('step_up', transaction)}
            className="flex-1 py-1 rounded-lg bg-cyan-950 hover:bg-cyan-900 border border-cyan-500/40 text-cyan-200 text-[10px] font-bold transition shadow-sm"
          >
            Trigger Step-Up OTP
          </button>
          <button
            onClick={() => onAction('block', transaction)}
            className="py-1 px-3 rounded-lg bg-rose-950 hover:bg-rose-900 border border-rose-500/50 text-rose-200 text-[10px] font-bold transition shadow-sm"
          >
            Block
          </button>
        </div>
      )}
    </div>
  )
}

export function RiskScoreCard({ riskData }) {
  const score = riskData?.riskScore ?? 94
  const probability = riskData?.fraudProbability ?? 91.8
  const tier = riskData?.riskTier || (score >= 70 ? 'CRITICAL' : score >= 30 ? 'MEDIUM' : 'LOW')

  return (
    <div className="my-2 p-3.5 rounded-2xl bg-gradient-to-r from-[#0b142d] via-[#0d1838] to-[#070c1e] border border-white/15 border-t-white/30 text-xs font-mono shadow-xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
        <span className="text-[#fefae0] font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          Mandatory Dual Metric Telemetry (Section 31)
        </span>
        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-rose-950 text-rose-300 border border-rose-500/50">
          TIER: {tier}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-2">
        <div className="p-2.5 rounded-xl bg-[#070c1e]/90 border border-white/10">
          <span className="text-[10px] text-slate-400 block mb-0.5">ML Fraud Probability</span>
          <div className="text-xl font-black text-rose-400">{probability}%</div>
          <p className="text-[9px] text-slate-400 mt-1 leading-tight">
            XGBoost model posterior statistical likelihood.
          </p>
        </div>

        <div className="p-2.5 rounded-xl bg-[#070c1e]/90 border border-white/10">
          <span className="text-[10px] text-slate-400 block mb-0.5">Independent Risk Score</span>
          <div className="text-xl font-black text-[#fefae0]">{score} <span className="text-xs text-slate-400 font-normal">/ 100</span></div>
          <p className="text-[9px] text-slate-400 mt-1 leading-tight">
            Independent 0-100 regulatory evaluation index.
          </p>
        </div>
      </div>

      {riskData?.topFactors && (
        <div className="space-y-1 pt-1.5 border-t border-white/10">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Top Risk Drivers:</div>
          {riskData.topFactors.map((f, i) => (
            <div key={i} className="text-[10px] text-slate-300 flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-rose-400 shrink-0" />
              <span>{f}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function ShapWaterfallCard({ features = [], baseValue = 0.12, outputValue = 0.94 }) {
  const displayFeatures = features.length > 0 ? features : [
    { name: 'distance_from_home', shapValue: 0.44, value: '8,420 km' },
    { name: 'amt_deviation', shapValue: 0.39, value: '+420%' },
    { name: 'trans_velocity_1h', shapValue: 0.22, value: '8 tx/hr' },
    { name: 'hour_risk_mult', shapValue: 0.08, value: '03:14 AM' },
    { name: 'device_trust_score', shapValue: -0.21, value: 'New Fingerprint' },
  ]

  return (
    <div className="my-2 p-3.5 rounded-2xl bg-[#0b142d]/95 border border-white/15 border-t-white/30 text-xs font-mono shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-white/10">
        <span className="text-cyan-300 font-bold flex items-center gap-1.5 text-[11px]">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[#fefae0]">TreeSHAP Attribution Decomposition</span>
        </span>
        <span className="text-[10px] text-slate-400 font-mono">
          Base: {baseValue} &rarr; Score: <strong className="text-rose-400">{outputValue}</strong>
        </span>
      </div>

      <div className="space-y-1.5">
        {displayFeatures.map((item, idx) => {
          const isPositive = (item.shapValue || 0) >= 0
          return (
            <div
              key={idx}
              className="flex items-center justify-between p-2 rounded-lg bg-[#070c1e]/80 border border-white/10 text-[10px]"
            >
              <div className="flex items-center gap-1.5 truncate max-w-[210px]">
                {isPositive ? (
                  <ArrowUpRight className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                ) : (
                  <ArrowDownRight className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                )}
                <span className="text-slate-200 truncate font-semibold" title={item.name}>
                  {item.name}
                </span>
                {item.value !== undefined && (
                  <span className="text-slate-400 text-[9px]">({item.value})</span>
                )}
              </div>
              <span
                className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                  isPositive ? 'text-rose-300 bg-rose-950/80' : 'text-emerald-300 bg-emerald-950/80'
                }`}
              >
                {isPositive ? `+${item.shapValue}` : item.shapValue}
              </span>
            </div>
          )
        })}
      </div>
      <p className="text-[9px] text-slate-400 mt-2 italic">
        *Mandate: TreeSHAP indicates feature influence direction; does not establish standalone legal causality.
      </p>
    </div>
  )
}

export function SarReportDraftCard({ sarData }) {
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(sarData?.narrative || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="my-2 p-3.5 rounded-2xl bg-[#0b142d]/95 border border-white/15 border-t-white/30 text-xs font-mono shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
        <span className="font-bold text-[#fefae0] flex items-center gap-1.5 text-xs">
          <FileText className="w-4 h-4 text-cyan-400" />
          <span>FinCEN SAR Narrative Draft</span>
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#070c1e] hover:bg-slate-800 text-[10px] text-cyan-300 border border-white/10 transition"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy Draft'}</span>
        </button>
      </div>

      <div className="space-y-1.5 text-[11px] text-slate-300 mb-2">
        <div>
          <span className="text-slate-400">Subject:</span>{' '}
          <strong className="text-white">{sarData?.subject || 'Target Account'}</strong>
        </div>
        <div>
          <span className="text-slate-400">Suspect IP:</span>{' '}
          <span className="text-amber-300">{sarData?.suspectIp || '185.220.101.5 (Bucharest, RO)'}</span>
        </div>
        <div>
          <span className="text-slate-400">Amount:</span>{' '}
          <span className="text-[#fefae0] font-bold">{sarData?.amount || '$3,850.00'}</span>
        </div>
      </div>

      <div className={`p-2.5 rounded-xl bg-[#070c1e] border border-white/10 text-[10px] text-slate-200 leading-relaxed font-sans ${expanded ? '' : 'line-clamp-4'}`}>
        {sarData?.narrative || 'Structured SAR Narrative Draft pending review.'}
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-2 text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono font-bold"
      >
        <span>{expanded ? 'Collapse Narrative' : 'Expand Full Narrative'}</span>
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
    </div>
  )
}
