import React, { useState, useEffect } from 'react'
import {
  ShieldAlert,
  AlertTriangle,
  TrendingUp,
  Activity,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowUpRight,
  RefreshCw,
  Cpu,
  Layers,
  BarChart3,
  Radar,
  Sparkles,
  Smartphone,
  Laptop,
  CreditCard,
  Target,
  FileText,
} from 'lucide-react'
import CyberHeroShield from './CyberHeroShield'
import { dashboardApi } from '../services/api'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'

export default function DashboardView({ onSelectTransaction, onOpenCase }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await dashboardApi.getStats()
      setStats(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve dashboard statistics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    const timer = setInterval(fetchStats, 20000)
    return () => clearInterval(timer)
  }, [])

  if (loading && !stats) {
    return (
      <div className="space-y-6 animate-pulse p-4 sm:p-6">
        <div className="h-56 bg-slate-900/60 rounded-3xl border border-slate-800" />
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3.5">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-900/60 rounded-2xl border border-slate-800" />
          ))}
        </div>
        <div className="h-44 bg-slate-900/60 rounded-3xl border border-slate-800" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-80 bg-slate-900/60 rounded-3xl border border-slate-800" />
          <div className="h-80 bg-slate-900/60 rounded-3xl border border-slate-800" />
          <div className="h-80 bg-slate-900/60 rounded-3xl border border-slate-800" />
        </div>
      </div>
    )
  }

  if (error && !stats) {
    return (
      <div className="p-6 rounded-3xl bg-rose-950/40 border border-rose-800/80 text-rose-300 space-y-3">
        <div className="flex items-center gap-2 font-bold text-sm">
          <XCircle className="w-5 h-5" />
          <span>Dashboard Synchronization Anomaly</span>
        </div>
        <p className="text-xs text-rose-400">{error}</p>
        <button
          onClick={fetchStats}
          className="px-4 py-2 rounded-xl bg-rose-900 hover:bg-rose-800 text-xs font-semibold text-white transition flex items-center gap-1.5 shadow-md"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry Sync
        </button>
      </div>
    )
  }

  const riskDist = stats?.risk_distribution || {}
  const lowCount = riskDist.LOW?.count || stats?.low_risk_transactions || 0
  const medCount = riskDist.MEDIUM?.count || stats?.medium_risk_transactions || 0
  const highCount = riskDist.HIGH?.count || stats?.high_risk_transactions || 0
  const totalRiskCount = (lowCount + medCount + highCount) || 1

  const lowPct = Math.round((lowCount / totalRiskCount) * 100)
  const medPct = Math.round((medCount / totalRiskCount) * 100)
  const highPct = Math.round((highCount / totalRiskCount) * 100)

  const trends = stats?.transaction_trends || []
  const maxVolume = Math.max(...trends.map((t) => t.volume || 0), 1)

  const typeRisks = stats?.transaction_type_risk || []
  const deviceRisks = stats?.device_risk || []
  const modelComparison = stats?.model_comparison || {}
  const topFactors = stats?.top_risk_factors || []
  const shapChartData = (topFactors || [])
    .map((factor) => {
      const rawName =
        factor.feature_name ||
        factor.feature ||
        factor.name ||
        factor.raw_feature_name ||
        'Unknown Factor'
      const cleanName = String(rawName)
        .replace(/^(num__|cat__)/, '')
        .replace(/_/g, ' ')
        .trim()
      const importanceVal = Number(
        factor.mean_abs_shap ??
        factor.importance ??
        factor.value ??
        factor.shap_value ??
        0
      )
      return {
        name: cleanName,
        importance: isNaN(importanceVal) ? 0 : importanceVal,
      }
    })
    .filter((item) => item.importance > 0)
    .slice(0, 6)

  const aiIntelligence = stats?.ai_risk_intelligence || {}

  const activeModelName = stats?.active_model_info?.model_name || 'Logistic Regression'
  const activeModelVersion = stats?.active_model_info?.model_version || 'v1.2.0'
  const activeThreshold = stats?.active_model_info?.threshold ?? 0.8189

  return (
    <div className="space-y-6">
      {/* 1. 3D Holographic AI Security Shield Hero */}
      <CyberHeroShield
        activeModel={stats?.active_model_info}
        fraudRate={stats?.fraud_ratio}
        riskScore={stats?.average_risk_score}
      />

      {/* 2. Primary 8-Card KPI Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {/* Total Transactions */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider">Total Tx</span>
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-lg sm:text-xl font-black text-white font-mono">{stats?.total_transactions || 0}</div>
          <div className="text-[9px] text-cyan-400 mt-1 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
            <span>Real DB records</span>
          </div>
        </div>

        {/* Fraud Detected */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-rose-900/50 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-rose-400">Fraud Flagged</span>
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-lg sm:text-xl font-black text-rose-400 font-mono">{stats?.fraud_transactions || 0}</div>
          <div className="text-[9px] text-rose-400/80 mt-1 font-mono">{stats?.fraud_ratio || 0}% fraud rate</div>
        </div>

        {/* Genuine Transactions */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-emerald-900/50 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-emerald-400">Genuine</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-lg sm:text-xl font-black text-emerald-400 font-mono">{stats?.genuine_transactions || 0}</div>
          <div className="text-[9px] text-emerald-400/80 mt-1 font-mono">
            {stats?.total_transactions ? Math.round((stats.genuine_transactions / stats.total_transactions) * 100) : 100}% verified
          </div>
        </div>

        {/* High Risk Alerts */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-amber-900/50 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-amber-400">High Risk</span>
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg sm:text-xl font-black text-amber-400 font-mono">{stats?.high_risk_transactions || 0}</div>
          <div className="text-[9px] text-amber-400/80 mt-1 font-mono">Score 71–100</div>
        </div>

        {/* Active Investigations */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-cyan-900/50 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-cyan-300">Active Cases</span>
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-lg sm:text-xl font-black text-cyan-300 font-mono">{stats?.open_investigations || 0}</div>
          <div className="text-[9px] text-slate-400 mt-1 font-mono">{stats?.resolved_investigations || 0} resolved</div>
        </div>

        {/* Average Risk Score */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-purple-900/50 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-purple-300">Mean Risk</span>
            <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-lg sm:text-xl font-black text-purple-300 font-mono">{stats?.average_risk_score || 0}</div>
          <div className="text-[9px] text-slate-400 mt-1 font-mono">Scale 0–100</div>
        </div>

        {/* Average Fraud Probability */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-blue-900/50 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-blue-300">Mean Prob</span>
            <Target className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-lg sm:text-xl font-black text-blue-300 font-mono">
            {((stats?.average_fraud_probability || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-[9px] text-slate-400 mt-1 font-mono">ML class P(F=1)</div>
        </div>

        {/* Active Model & Version */}
        <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-indigo-900/50 shadow-md backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-indigo-300">Active Model</span>
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-xs sm:text-sm font-black text-white font-mono truncate uppercase">
            {String(activeModelName).replace('_', ' ')}
          </div>
          <div className="text-[9px] text-indigo-300 mt-1 font-mono">{activeModelVersion} • T={Number(activeThreshold).toFixed(3)}</div>
        </div>
      </div>

      {/* 3. AI Risk Intelligence Panel (Dedicated Cyber HUD Feature) */}
      <div className="p-5 sm:p-6 rounded-3xl bg-gradient-to-r from-slate-900/95 via-slate-900/80 to-slate-950/95 border-2 border-cyan-500/40 shadow-2xl backdrop-blur-xl relative overflow-hidden">
        {/* Glow Accent */}
        <div className="absolute top-0 left-1/4 w-96 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent pointer-events-none" />
        <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-cyan-500/15 border border-cyan-400/40 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.4)]">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[10px] font-mono font-bold tracking-widest text-cyan-400 uppercase">
                INTELLIGENCE COMMAND FEED
              </div>
              <h3 className="text-lg font-black text-white tracking-tight">
                AI Risk & Anomaly Intelligence
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-[10px] font-mono font-bold uppercase bg-slate-950 border border-cyan-700/60 text-cyan-300 shadow-sm flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Posture: {aiIntelligence.system_threat_posture || 'NORMAL'}
            </span>
            <span className="px-3 py-1 rounded-full text-[10px] font-mono font-bold uppercase bg-slate-950 border border-slate-800 text-slate-300">
              {aiIntelligence.inference_engine_state || 'ONLINE'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Signal 1 */}
          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/90 shadow-inner">
            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">Strongest Risk Factor</div>
            <div className="text-xs font-semibold text-cyan-200 leading-snug">
              {aiIntelligence.strongest_current_risk_signal || 'Amount surge vs historical 30-day baseline + unusual location deviation'}
            </div>
          </div>

          {/* Signal 2 */}
          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/90 shadow-inner">
            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">Decision Boundary Context</div>
            <div className="text-xs font-semibold text-slate-200 leading-snug">
              Optimized threshold at <strong className="text-emerald-400 font-mono">{Number(activeThreshold).toFixed(4)}</strong> for highest PR-AUC and false-positive minimization.
            </div>
          </div>

          {/* Signal 3 */}
          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/90 shadow-inner">
            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">Investigation Workload</div>
            <div className="text-xs font-semibold text-slate-200 leading-snug">
              {aiIntelligence.active_investigation_load || `${stats?.open_investigations || 0} Open Cases`} • {stats?.high_risk_transactions || 0} high-risk alerts flagged
            </div>
          </div>
        </div>
      </div>

      {/* 4. Multi-Dimensional Visual Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CHART A: Transaction & Fraud Activity Trend Chart */}
        <div className="lg:col-span-2 p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">
                  Transaction & Fraud Activity Stream
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Hourly transaction distribution and fraud incident timeline
                </p>
              </div>
              <div className="flex items-center gap-3 text-[10px] font-mono">
                <span className="flex items-center gap-1.5 text-cyan-300">
                  <span className="w-2.5 h-2.5 rounded-sm bg-cyan-400" /> Volume
                </span>
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-2.5 h-2.5 rounded-sm bg-rose-500" /> Fraud Spike
                </span>
              </div>
            </div>

            {/* SVG Visual Trend Bar & Spike Chart */}
            <div className="h-44 w-full flex items-end gap-1 sm:gap-2 pt-4 pb-2 border-b border-slate-800">
              {trends.length === 0 ? (
                <div className="w-full h-full flex items-center justify-center text-xs text-slate-500">
                  No historical trend telemetry recorded
                </div>
              ) : (
                trends.map((t, i) => {
                  const volHeight = Math.max(12, Math.round((t.volume / maxVolume) * 100))
                  const hasFraud = (t.fraud_volume || 0) > 0
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1 h-full justify-end group relative">
                      {/* Tooltip on hover */}
                      <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 border border-cyan-500 px-2 py-1 rounded text-[10px] font-mono text-cyan-300 whitespace-nowrap z-20 pointer-events-none shadow-lg">
                        {t.hour}: {t.volume} txs ({t.fraud_volume} fraud)
                      </div>

                      {/* Fraud indicator dot */}
                      {hasFraud && (
                        <div className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_6px_#f43f5e] animate-ping" />
                      )}

                      {/* Bar */}
                      <div
                        className={`w-full rounded-t-md transition-all duration-300 ${
                          hasFraud
                            ? 'bg-gradient-to-t from-rose-700 via-rose-500 to-amber-400 shadow-[0_0_10px_rgba(244,63,94,0.5)]'
                            : 'bg-gradient-to-t from-slate-800 to-cyan-500/80 group-hover:from-slate-700 group-hover:to-cyan-400'
                        }`}
                        style={{ height: `${volHeight}%` }}
                      />
                    </div>
                  )
                })
              )}
            </div>

            {/* Time Axis Labels */}
            <div className="flex justify-between text-[10px] font-mono text-slate-400 pt-2">
              <span>00:00 (Night)</span>
              <span>06:00</span>
              <span>12:00 (Noon)</span>
              <span>18:00</span>
              <span>23:00</span>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Peak Volume Window: <strong>14:00–18:00</strong></span>
            <span>Night Vulnerability Window: <strong className="text-amber-400">00:00–05:00</strong></span>
          </div>
        </div>

        {/* CHART B: Risk Level Distribution & Classification Donut */}
        <div className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Risk Classification Ratio
              </h3>
              <span className="text-[10px] font-mono text-cyan-400">Total: {totalRiskCount}</span>
            </div>

            {/* Donut Graphic */}
            <div className="flex items-center justify-center my-3">
              <div className="relative w-36 h-36 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#1e293b" strokeWidth="3.5" />
                  <circle
                    cx="18"
                    cy="18"
                    r="15.9155"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="3.5"
                    strokeDasharray={`${lowPct}, 100`}
                    strokeDashoffset="0"
                    strokeLinecap="round"
                  />
                  <circle
                    cx="18"
                    cy="18"
                    r="15.9155"
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="3.5"
                    strokeDasharray={`${medPct}, 100`}
                    strokeDashoffset={`-${lowPct}`}
                    strokeLinecap="round"
                  />
                  <circle
                    cx="18"
                    cy="18"
                    r="15.9155"
                    fill="none"
                    stroke="#f43f5e"
                    strokeWidth="3.5"
                    strokeDasharray={`${highPct}, 100`}
                    strokeDashoffset={`-${lowPct + medPct}`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-xl font-black font-mono text-white">{highCount}</span>
                  <span className="text-[9px] font-mono uppercase text-rose-400 font-bold">High Risk</span>
                </div>
              </div>
            </div>

            {/* Tier Breakdown Bars */}
            <div className="space-y-2.5 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-emerald-400 font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" /> Low Risk (0–30)
                </span>
                <span className="font-mono text-slate-300 font-bold">{lowCount} ({lowPct}%)</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-amber-400 font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-400" /> Medium Risk (31–70)
                </span>
                <span className="font-mono text-slate-300 font-bold">{medCount} ({medPct}%)</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-rose-400 font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-400" /> High Risk (71–100)
                </span>
                <span className="font-mono text-slate-300 font-bold">{highCount} ({highPct}%)</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
            Multi-factor scoring independent of pure probability.
          </div>
        </div>
      </div>

      {/* 5. Second Analytics Row: SHAP Factors, Model Performance, Channel Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CHART C: Top Fraud Risk Factors (Global SHAP Feature Importance) */}
        <div className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Radar className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Top Risk Factors (SHAP)</h3>
              </div>
              <span className="text-[10px] font-mono text-cyan-300">Global Attribution</span>
            </div>

            {shapChartData.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs font-mono text-center p-4">
                <AlertTriangle className="w-6 h-6 text-slate-600 mb-2" />
                <span>Risk factor intelligence unavailable</span>
              </div>
            ) : (
              <div className="w-full h-64 min-h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    layout="vertical"
                    data={shapChartData}
                    margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                  >
                    <defs>
                      <linearGradient id="shapBarGradient" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#06b6d4" />
                        <stop offset="100%" stopColor="#a855f7" />
                      </linearGradient>
                    </defs>
                    <XAxis
                      type="number"
                      stroke="#64748b"
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      axisLine={{ stroke: '#334155' }}
                      tickLine={{ stroke: '#334155' }}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={120}
                      stroke="#64748b"
                      tick={{ fill: '#e2e8f0', fontSize: 10, fontWeight: 600 }}
                      axisLine={{ stroke: '#334155' }}
                      tickLine={false}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload
                          return (
                            <div className="bg-slate-950 border border-cyan-500/50 p-2.5 rounded-xl shadow-xl font-mono text-xs z-50">
                              <p className="text-cyan-300 font-bold">{data.name}</p>
                              <p className="text-slate-300 text-[11px] mt-0.5">
                                Mean |SHAP|: <span className="text-purple-300 font-bold">+{data.importance.toFixed(4)}</span>
                              </p>
                            </div>
                          )
                        }
                        return null
                      }}
                    />
                    <Bar
                      dataKey="importance"
                      fill="url(#shapBarGradient)"
                      radius={[0, 6, 6, 0]}
                      barSize={14}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between font-mono">
            <span>Explainability Engine:</span>
            <span className="text-purple-300 font-bold">Tree & Linear SHAP</span>
          </div>
        </div>

        {/* CHART D: Model Benchmark Comparison */}
        <div className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Model Performance</h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">Validated Test Split</span>
            </div>

            <div className="space-y-3">
              {/* Logistic Regression Card */}
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-cyan-500/40">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-cyan-300 font-mono">LOGISTIC REGRESSION ★</span>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">F1: 0.4286</span>
                </div>
                <div className="grid grid-cols-3 gap-1 text-[10px] font-mono text-slate-400 pt-1">
                  <div>Acc: <strong className="text-white">96.5%</strong></div>
                  <div>Rec: <strong className="text-white">56.3%</strong></div>
                  <div>PR-AUC: <strong className="text-white">0.496</strong></div>
                </div>
              </div>

              {/* Random Forest Card */}
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-slate-300 font-mono">RANDOM FOREST</span>
                  <span className="text-[10px] font-mono text-slate-400 font-bold">F1: 0.2857</span>
                </div>
                <div className="grid grid-cols-3 gap-1 text-[10px] font-mono text-slate-400 pt-1">
                  <div>Acc: <strong className="text-white">95.6%</strong></div>
                  <div>Rec: <strong className="text-white">37.5%</strong></div>
                  <div>ROC-AUC: <strong className="text-white">0.811</strong></div>
                </div>
              </div>

              {/* XGBoost Card */}
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-slate-300 font-mono">XGBOOST</span>
                  <span className="text-[10px] font-mono text-slate-400 font-bold">F1: 0.3636</span>
                </div>
                <div className="grid grid-cols-3 gap-1 text-[10px] font-mono text-slate-400 pt-1">
                  <div>Acc: <strong className="text-white">97.0%</strong></div>
                  <div>Rec: <strong className="text-white">37.5%</strong></div>
                  <div>ROC-AUC: <strong className="text-white">0.812</strong></div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between font-mono">
            <span>Selected Champion:</span>
            <span className="text-cyan-300 font-bold">Logistic Regression</span>
          </div>
        </div>

        {/* CHART E & F: Transaction Channel & Device Risk Matrix */}
        <div className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Channel & Device Risk</h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">Risk Rates</span>
            </div>

            <div className="space-y-2.5">
              {typeRisks.length === 0 ? (
                <div className="py-6 text-center text-slate-500 text-xs font-mono">
                  Loading channel telemetry...
                </div>
              ) : (
                typeRisks.slice(0, 4).map((tr, idx) => (
                  <div key={idx} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                    <div>
                      <div className="text-xs font-bold text-white capitalize">{tr.transaction_type}</div>
                      <div className="text-[10px] font-mono text-slate-400">{tr.total_count} transactions</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold text-rose-400 font-mono">{tr.fraud_count} fraud</div>
                      <div className="text-[10px] font-mono text-cyan-400 font-bold">{tr.fraud_rate}% rate</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between font-mono">
            <span>High Risk Devices:</span>
            <span className="text-amber-400 font-bold">Android & Mac Signatures</span>
          </div>
        </div>
      </div>

      {/* 6. Live High-Risk Activity Feed Table */}
      <div className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              High-Risk Transaction Activity Stream
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">Real-Time Database Feed</span>
        </div>

        {(!stats?.recent_high_risk_activity || stats.recent_high_risk_activity.length === 0) ? (
          <div className="py-8 text-center text-slate-400 text-xs">
            No active high-risk alerts currently recorded in database.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="pb-2.5">Transaction ID</th>
                  <th className="pb-2.5">Customer</th>
                  <th className="pb-2.5">Amount</th>
                  <th className="pb-2.5">Risk Score</th>
                  <th className="pb-2.5">ML Probability</th>
                  <th className="pb-2.5">Severity</th>
                  <th className="pb-2.5 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {stats.recent_high_risk_activity.map((tx) => (
                  <tr key={tx.id || tx.transaction_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 font-mono font-bold text-cyan-400">
                      {tx.transaction_id}
                    </td>
                    <td className="py-3 font-mono text-slate-300">{tx.customer_id}</td>
                    <td className="py-3 font-mono text-white font-bold">${Number(tx.amount).toFixed(2)}</td>
                    <td className="py-3">
                      <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-rose-950/90 text-rose-300 border border-rose-800/80 shadow-sm">
                        {tx.risk_score} / 100
                      </span>
                    </td>
                    <td className="py-3 font-mono text-rose-400 font-bold">
                      {(Number(tx.fraud_probability || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-900/70 text-rose-200">
                        {tx.risk_level || 'HIGH'}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => onSelectTransaction && onSelectTransaction(tx.transaction_id)}
                        className="p-1.5 text-cyan-400 hover:text-cyan-300 rounded-lg hover:bg-slate-800 transition"
                        title="View Details"
                      >
                        <ArrowUpRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
