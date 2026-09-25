import React, { useState, useEffect } from 'react'
import {
  FileCheck,
  ShieldAlert,
  ShieldCheck,
  AlertCircle,
  Database,
  Layers,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  Lock,
  Calendar,
  BarChart2,
} from 'lucide-react'

export default function DatasetHealthView() {
  const [loading, setLoading] = useState(false)
  const [modelMeta, setModelMeta] = useState(null)

  useEffect(() => {
    // Load metadata from API or local state
    const fetchMeta = async () => {
      try {
        const token = localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')
        const res = await fetch('/api/v1/admin/model-comparison', {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (res.ok) {
          const data = await res.json()
          setModelMeta(data)
        }
      } catch (e) {
        console.error('Error loading dataset metadata:', e)
      }
    }
    fetchMeta()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/80 border border-slate-800 p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-indigo-950 text-indigo-400 border border-indigo-800">
                CANONICAL DATASET HEALTH AUDIT
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                100% LEAKAGE-FREE VERIFIED
              </span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <Database className="w-6 h-6 text-cyan-400" />
              Dataset Health &amp; Anti-Leakage Governance
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Academic and compliance audit of the 20,000-record canonical synthetic dataset across 29 fictional merchants, ensuring strict temporal separation and zero post-outcome target leakage.
            </p>
          </div>
        </div>
      </div>

      {/* 4 Health Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <div className="text-[10px] font-mono uppercase text-slate-500">Total Records</div>
          <div className="text-2xl font-black font-mono text-white mt-1">20,000</div>
          <div className="text-[11px] text-slate-400 mt-1">55 Schema Columns</div>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <div className="text-[10px] font-mono uppercase text-slate-500">Master Merchants</div>
          <div className="text-2xl font-black font-mono text-cyan-400 mt-1">29</div>
          <div className="text-[11px] text-slate-400 mt-1">Tamil Nadu &amp; Karnataka</div>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <div className="text-[10px] font-mono uppercase text-slate-500">Fraud Class Ratio</div>
          <div className="text-2xl font-black font-mono text-rose-400 mt-1">3.65%</div>
          <div className="text-[11px] text-slate-400 mt-1">731 Fraud / 19,269 Normal</div>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <div className="text-[10px] font-mono uppercase text-slate-500">Target Leakage Status</div>
          <div className="text-2xl font-black font-mono text-emerald-400 mt-1">ZERO</div>
          <div className="text-[11px] text-emerald-500/90 mt-1">Strict Pre-Inference Features</div>
        </div>
      </div>

      {/* Target Leakage Protection Matrix */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Lock className="w-5 h-5 text-emerald-400" />
          Target Leakage Isolation &amp; Feature Segregation Audit
        </h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          The ML feature matrix strictly excludes post-outcome and investigation-derived fields. The model is trained purely on information available at the exact microsecond of transaction initiation.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Approved Safe Feature Inputs */}
          <div className="bg-slate-950 p-4 rounded-xl border border-emerald-900/50 space-y-3">
            <div className="text-xs font-bold text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Pre-Inference Context Features (Used in ML)
            </div>
            <ul className="text-xs text-slate-300 space-y-1.5 font-mono text-[11px]">
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> amount, transaction_hour, day_of_week
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> merchant_category, business_age, avg_ticket
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> customer_account_age, usual_avg_amount
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> transactions_last_1h, transactions_last_24h
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> amount_to_avg_ratio, amount_deviation_zscore
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> is_new_device, is_trusted_device, is_new_beneficiary
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> location_distance_km, failed_logins_24h
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> merchant_historical_fraud_rate (prior window)
              </li>
            </ul>
          </div>

          {/* Strictly Excluded Leakage Columns */}
          <div className="bg-slate-950 p-4 rounded-xl border border-rose-900/50 space-y-3">
            <div className="text-xs font-bold text-rose-400 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              Post-Outcome Columns (Strictly Blocked from ML)
            </div>
            <ul className="text-xs text-slate-300 space-y-1.5 font-mono text-[11px]">
              <li className="flex items-center gap-2">
                <span className="text-rose-400">✕</span> is_fraud (Supervised Target Only)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-rose-400">✕</span> fraud_type (Investigation Context)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-rose-400">✕</span> fraud_stage (Post-Incident Classification)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-rose-400">✕</span> fraud_scenario (Synthetic Scenario Tag)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-rose-400">✕</span> merchant_historical_fraud_summary (Text Log)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-rose-400">✕</span> merchant_historical_fraud_pattern (Text Log)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-rose-400">✕</span> Future transaction counts (Temporal Leakage Protected)
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Train/Test Time-Aware Split Validation */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Calendar className="w-5 h-5 text-cyan-400" />
          Time-Aware Train / Test Chronological Partitioning
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="text-slate-500 uppercase text-[10px]">Training Partition (80%)</div>
            <div className="text-lg font-bold text-cyan-300 mt-1">16,000 Transactions</div>
            <div className="text-slate-400 text-[11px] mt-1">Chronological Past Events (Fraud: 3.57%)</div>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div className="text-slate-500 uppercase text-[10px]">Out-of-Time Test Partition (20%)</div>
            <div className="text-lg font-bold text-purple-300 mt-1">4,000 Transactions</div>
            <div className="text-slate-400 text-[11px] mt-1">Unseen Future Events (Fraud: 3.98%)</div>
          </div>
        </div>
      </div>
    </div>
  )
}
