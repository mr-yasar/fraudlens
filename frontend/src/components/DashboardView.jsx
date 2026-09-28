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
  Zap,
  Lock,
  Building2,
  Info,
} from 'lucide-react'
import CyberHeroShield from './CyberHeroShield'
import { dashboardApi, alertsApi } from '../services/api'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import { getCustomerPersona } from '../utils/customerHelper'
import CustomerDashboardView from './CustomerDashboardView'
import GlobalCenterModal from './common/GlobalCenterModal'
import ContextualModuleHelp from './common/ContextualModuleHelp'
import { formatINR } from '../utils/formatters'

export default function DashboardView({ onSelectTransaction, onOpenCase, onOpenPayment, user, isAdmin }) {
  const customerPersona = getCustomerPersona(user)
  const isCustomer = customerPersona.isCustomer

  // DEDICATED CUSTOMER DASHBOARD
  if (isCustomer) {
    return (
      <CustomerDashboardView
        user={user}
        customerPersona={customerPersona}
        onSelectTransaction={onSelectTransaction}
        onOpenPayment={onOpenPayment}
        onOpenCase={onOpenCase}
      />
    )
  }

  // ADMIN DASHBOARD
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [alertsLoading, setAlertsLoading] = useState(false)
  const [acknowledgingId, setAcknowledgingId] = useState(null)

  // Centered Modal Inspection States (Feature: CLICK -> CENTERED MODAL -> FULL CONTENT)
  const [activeModal, setActiveModal] = useState(null)
  // activeModal can be: { type: 'METRIC', data: ... } | { type: 'ALERT', data: ... } | { type: 'TX', data: ... } | { type: 'SHAP', data: ... } | { type: 'MODEL', data: ... } | { type: 'CHANNEL', data: ... }

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

  const fetchAlerts = async () => {
    setAlertsLoading(true)
    try {
      const data = await alertsApi.list({ unacknowledged_only: false, limit: 8 })
      setAlerts(data || [])
    } catch {
      // Non-blocking for alerts
    } finally {
      setAlertsLoading(false)
    }
  }

  const handleAcknowledgeAlert = async (alertId) => {
    setAcknowledgingId(alertId)
    try {
      await alertsApi.acknowledge(alertId)
      fetchAlerts()
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
    } finally {
      setAcknowledgingId(null)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchAlerts()
    const timer = setInterval(() => {
      fetchStats()
      fetchAlerts()
    }, 20000)
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

      {/* Real-Time Evaluation Personas Banner */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/70 border border-cyan-800/50 shadow-xl relative overflow-hidden">
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 border-b border-slate-800/80 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
                  <Zap className="w-3 h-3 text-cyan-400 animate-pulse" />
                  ADMIN MULTI-CUSTOMER AUDIT
                </span>
                <span className="text-[10px] font-mono text-slate-400">All 3 Canonical Personas Active</span>
              </div>
              <div className="flex items-center gap-3 mt-1">
                <h2 className="text-base sm:text-lg font-bold text-white">
                  Real-Time Evaluation Personas &amp; Behavioral Profiles
                </h2>
                <ContextualModuleHelp moduleKey="dashboard" />
              </div>
            </div>
            <button
              onClick={() => onOpenPayment && onOpenPayment('scenario_monisha_safe')}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-950/40 transition shrink-0"
            >
              <CreditCard className="w-3.5 h-3.5" />
              <span>Open Pre-Auth Gateway</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Persona 1: Monisha */}
            <div
              onClick={() =>
                setActiveModal({
                  type: 'PERSONA',
                  title: 'Monisha (CUST_MONISHA_001) Profile',
                  badge: '3.0% FRAUD RATE • SAFE ALLOW',
                  badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800',
                  icon: CheckCircle2,
                  data: {
                    name: 'Monisha',
                    id: 'CUST_MONISHA_001',
                    fraudRate: '3.0%',
                    tenure: '420 Days',
                    balance: '₹15,00,000.00',
                    location: 'Chennai, Tamil Nadu',
                    usualMerchants: 'NovaMart Fresh, Blue Tokai Coffee, Swiggy',
                    policy: 'Zero-Friction Auto-Approved (No OTP)',
                  },
                })
              }
              className="p-3.5 rounded-xl bg-slate-900/80 border border-emerald-800/50 hover:border-emerald-500/60 transition flex flex-col justify-between cursor-pointer group shadow"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-white group-hover:text-emerald-300 transition">
                    Monisha (CUST_MONISHA_001)
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                    3.0% FRAUD
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed mb-2">
                  Habitual grocery &amp; utility profile in Chennai. Clean baseline &rarr; Pre-Auth evaluates and issues <strong className="text-emerald-400">ALLOW (Auto-Approved)</strong>.
                </p>
              </div>
              <div className="w-full mt-2 py-1.5 px-2.5 rounded-lg bg-emerald-950/70 hover:bg-emerald-900/80 border border-emerald-800/80 text-emerald-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition">
                <span>Inspect Persona Telemetry</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Persona 2: Mohana */}
            <div
              onClick={() =>
                setActiveModal({
                  type: 'PERSONA',
                  title: 'Mohana (CUST_MOHANA_002) Profile',
                  badge: '12.0% FRAUD RATE • STEP-UP OTP',
                  badgeColor: 'bg-amber-950 text-amber-300 border-amber-800',
                  icon: AlertTriangle,
                  data: {
                    name: 'Mohana',
                    id: 'CUST_MOHANA_002',
                    fraudRate: '12.0%',
                    tenure: '180 Days',
                    balance: '₹15,00,000.00',
                    location: 'Salem / Coimbatore, Tamil Nadu',
                    usualMerchants: 'CircuitBay Electronics, GameZone Digital',
                    policy: 'Step-Up OTP Verification on Velocity / Device Spikes',
                  },
                })
              }
              className="p-3.5 rounded-xl bg-slate-900/80 border border-amber-800/50 hover:border-amber-500/60 transition flex flex-col justify-between cursor-pointer group shadow"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-white group-hover:text-amber-300 transition">
                    Mohana (CUST_MOHANA_002)
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-300 border border-amber-800">
                    12.0% FRAUD
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed mb-2">
                  Unfamiliar device &amp; cross-city Salem purchase. Elevated anomaly &rarr; FraudLens requests <strong className="text-amber-400">REVIEW (Step-Up OTP)</strong>.
                </p>
              </div>
              <div className="w-full mt-2 py-1.5 px-2.5 rounded-lg bg-amber-950/70 hover:bg-amber-900/80 border border-amber-800/80 text-amber-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition">
                <span>Inspect Persona Telemetry</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Persona 3: Sowmiya */}
            <div
              onClick={() =>
                setActiveModal({
                  type: 'PERSONA',
                  title: 'Sowmiya (CUST_SOWMIYA_003) Profile',
                  badge: '26.0% FRAUD RATE • CRITICAL BLOCK',
                  badgeColor: 'bg-rose-950 text-rose-300 border-rose-800',
                  icon: ShieldAlert,
                  data: {
                    name: 'Sowmiya',
                    id: 'CUST_SOWMIYA_003',
                    fraudRate: '26.0%',
                    tenure: '90 Days',
                    balance: '₹15,00,000.00',
                    location: 'Lagos / Foreign Proxy / Dubai',
                    usualMerchants: 'Aurelia Gold House, CryptoXchange Global',
                    policy: 'Instant Pre-Auth Block on Botnet / ATO Incursion',
                  },
                })
              }
              className="p-3.5 rounded-xl bg-slate-900/80 border border-rose-800/50 hover:border-rose-500/60 transition flex flex-col justify-between cursor-pointer group shadow"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-white group-hover:text-rose-300 transition">
                    Sowmiya (CUST_SOWMIYA_003)
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-800">
                    26.0% FRAUD
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed mb-2">
                  Botnet emulator ATO attack at 2:30 AM via foreign proxy IP. Critical threat &rarr; Instant Pre-Auth <strong className="text-rose-400">BLOCK (Zero Funds Lost)</strong>.
                </p>
              </div>
              <div className="w-full mt-2 py-1.5 px-2.5 rounded-lg bg-rose-950/70 hover:bg-rose-900/80 border border-rose-800/80 text-rose-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition">
                <span>Inspect Persona Telemetry</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Primary 8-Card KPI Metrics Grid (Interactive Centered Modals on Click) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {/* Total Transactions */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'METRIC',
              title: 'Total Transactions Ledger',
              badge: `${stats?.total_transactions || 0} RECORDS`,
              icon: Activity,
              subtitle: 'Comprehensive ledger count of all transactions evaluated in database',
              data: {
                totalCount: stats?.total_transactions || 0,
                genuineCount: stats?.genuine_transactions || 0,
                fraudCount: stats?.fraud_transactions || 0,
                fraudRatio: `${stats?.fraud_ratio || 0}%`,
                databaseStatus: 'Verified SQL Database Connection',
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-cyan-500/60 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider">Total Tx</span>
            <Activity className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-lg sm:text-xl font-black text-white font-mono">{stats?.total_transactions || 0}</div>
          <div className="text-[9px] text-cyan-400 mt-1 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
            <span>Click to inspect</span>
          </div>
        </div>

        {/* Fraud Flagged */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'METRIC',
              title: 'Fraud Incidents Breakdown',
              badge: `${stats?.fraud_transactions || 0} THREATS`,
              badgeColor: 'bg-rose-950 text-rose-300 border-rose-800',
              icon: AlertTriangle,
              subtitle: 'Transactions confirmed as anomalous or malicious by the AI risk pipeline',
              data: {
                fraudCount: stats?.fraud_transactions || 0,
                fraudRatio: `${stats?.fraud_ratio || 0}%`,
                highRiskCount: stats?.high_risk_transactions || 0,
                openCases: stats?.open_investigations || 0,
                meanScore: `${stats?.average_risk_score || 0} / 100`,
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-rose-900/50 hover:border-rose-500 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-rose-400">Fraud Flagged</span>
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-lg sm:text-xl font-black text-rose-400 font-mono">{stats?.fraud_transactions || 0}</div>
          <div className="text-[9px] text-rose-400/80 mt-1 font-mono">{stats?.fraud_ratio || 0}% fraud rate</div>
        </div>

        {/* Genuine Transactions */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'METRIC',
              title: 'Genuine Legitimate Transfers',
              badge: `${stats?.genuine_transactions || 0} CLEAN`,
              badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800',
              icon: CheckCircle2,
              subtitle: 'Transactions cleared with low risk score and auto-authorized with zero friction',
              data: {
                genuineCount: stats?.genuine_transactions || 0,
                cleanRatio: `${stats?.total_transactions ? Math.round((stats.genuine_transactions / stats.total_transactions) * 100) : 100}%`,
                lowRiskCount: stats?.low_risk_transactions || 0,
                approvalLatency: '< 120ms',
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-emerald-900/50 hover:border-emerald-500 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-emerald-400">Genuine</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-lg sm:text-xl font-black text-emerald-400 font-mono">{stats?.genuine_transactions || 0}</div>
          <div className="text-[9px] text-emerald-400/80 mt-1 font-mono">
            {stats?.total_transactions ? Math.round((stats.genuine_transactions / stats.total_transactions) * 100) : 100}% verified
          </div>
        </div>

        {/* High Risk Alerts */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'METRIC',
              title: 'High Risk Incident Telemetry',
              badge: 'SCORE 71-100',
              badgeColor: 'bg-amber-950 text-amber-300 border-amber-800',
              icon: ShieldAlert,
              subtitle: 'Transactions scoring in the upper critical quartile requiring manual review or hard block',
              data: {
                highRiskCount: stats?.high_risk_transactions || 0,
                openCases: stats?.open_investigations || 0,
                posture: aiIntelligence.system_threat_posture || 'NORMAL',
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-amber-900/50 hover:border-amber-500 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-amber-400">High Risk</span>
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-lg sm:text-xl font-black text-amber-400 font-mono">{stats?.high_risk_transactions || 0}</div>
          <div className="text-[9px] text-amber-400/80 mt-1 font-mono">Score 71–100</div>
        </div>

        {/* Active Investigations */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'METRIC',
              title: 'Active Case Management',
              badge: `${stats?.open_investigations || 0} OPEN`,
              icon: Clock,
              subtitle: 'Formal compliance and security investigation dossiers held in pipeline',
              data: {
                openCases: stats?.open_investigations || 0,
                resolvedCases: stats?.resolved_investigations || 0,
                assignedAnalysts: 'Tier-1 Security Response Team',
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-cyan-900/50 hover:border-cyan-500 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-cyan-300">Active Cases</span>
            <Clock className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-lg sm:text-xl font-black text-cyan-300 font-mono">{stats?.open_investigations || 0}</div>
          <div className="text-[9px] text-slate-400 mt-1 font-mono">{stats?.resolved_investigations || 0} resolved</div>
        </div>

        {/* Average Risk Score */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'METRIC',
              title: 'Multi-Factor Risk Distribution',
              badge: `MEAN: ${stats?.average_risk_score || 0}`,
              icon: TrendingUp,
              subtitle: '0-100 Composite risk metric factoring SHAP, rules, velocity, and device novelty',
              data: {
                meanScore: `${stats?.average_risk_score || 0} / 100`,
                lowTier: `${lowCount} txs (0-30)`,
                medTier: `${medCount} txs (31-70)`,
                highTier: `${highCount} txs (71-100)`,
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-purple-900/50 hover:border-purple-500 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-purple-300">Mean Risk</span>
            <TrendingUp className="w-3.5 h-3.5 text-purple-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-lg sm:text-xl font-black text-purple-300 font-mono">{stats?.average_risk_score || 0}</div>
          <div className="text-[9px] text-slate-400 mt-1 font-mono">Scale 0–100</div>
        </div>

        {/* Average Fraud Probability */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'METRIC',
              title: 'ML Classification Probability Mean',
              badge: `${((stats?.average_fraud_probability || 0) * 100).toFixed(1)}% P(F=1)`,
              icon: Target,
              subtitle: 'Raw statistical output from the champion machine learning inference model',
              data: {
                meanProb: `${((stats?.average_fraud_probability || 0) * 100).toFixed(2)}%`,
                activeModel: activeModelName,
                modelVersion: activeModelVersion,
                decisionThreshold: Number(activeThreshold).toFixed(4),
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-blue-900/50 hover:border-blue-500 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-blue-300">Mean Prob</span>
            <Target className="w-3.5 h-3.5 text-blue-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-lg sm:text-xl font-black text-blue-300 font-mono">
            {((stats?.average_fraud_probability || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-[9px] text-slate-400 mt-1 font-mono">ML class P(F=1)</div>
        </div>

        {/* Active Model & Version */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'MODEL',
              title: 'Champion Model Deployment & Metrics',
              badge: activeModelVersion,
              icon: Cpu,
              subtitle: 'Production inference model metadata, calibration threshold, and validation metrics',
              data: {
                modelName: activeModelName,
                modelVersion: activeModelVersion,
                threshold: Number(activeThreshold).toFixed(4),
                f1Score: '0.4286',
                precisionAuc: '0.496',
                accuracy: '96.5%',
                recall: '56.3%',
              },
            })
          }
          className="p-3.5 rounded-2xl bg-slate-900/70 border border-indigo-900/50 hover:border-indigo-500 shadow-md backdrop-blur-md flex flex-col justify-between cursor-pointer group transition hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-indigo-300">Active Model</span>
            <Cpu className="w-3.5 h-3.5 text-indigo-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-xs sm:text-sm font-black text-white font-mono truncate uppercase">
            {String(activeModelName).replace('_', ' ')}
          </div>
          <div className="text-[9px] text-indigo-300 mt-1 font-mono">{activeModelVersion} • T={Number(activeThreshold).toFixed(3)}</div>
        </div>
      </div>

      {/* 3. AI Risk Intelligence Panel */}
      <div className="p-5 sm:p-6 rounded-3xl bg-gradient-to-r from-slate-900/95 via-slate-900/80 to-slate-950/95 border-2 border-cyan-500/40 shadow-2xl backdrop-blur-xl relative overflow-hidden">
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
                AI Risk &amp; Anomaly Intelligence
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
                  Transaction &amp; Fraud Activity Stream
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
                      <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 border border-cyan-500 px-2 py-1 rounded text-[10px] font-mono text-cyan-300 whitespace-nowrap z-20 pointer-events-none shadow-lg">
                        {t.hour}: {t.volume} txs ({t.fraud_volume} fraud)
                      </div>
                      {hasFraud && (
                        <div className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_6px_#f43f5e] animate-ping" />
                      )}
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
        <div
          onClick={() =>
            setActiveModal({
              type: 'DONUT',
              title: 'Risk Tier Classification Matrix',
              badge: `${totalRiskCount} ASSESSED`,
              icon: Target,
              subtitle: 'Comprehensive breakdown of Low, Medium, and High risk classifications',
              data: {
                totalAssessed: totalRiskCount,
                lowCount,
                lowPct,
                medCount,
                medPct,
                highCount,
                highPct,
              },
            })
          }
          className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 shadow-xl backdrop-blur-md flex flex-col justify-between cursor-pointer group transition"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider group-hover:text-cyan-300 transition">
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

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-cyan-400 flex items-center justify-between">
            <span>Click for deep-dive classification</span>
            <span>&rarr;</span>
          </div>
        </div>
      </div>

      {/* 5. Second Analytics Row: SHAP Factors, Model Performance, Channel Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CHART C: Top Fraud Risk Factors (Global SHAP Feature Importance) */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'SHAP',
              title: 'Explainable AI Feature Attributions (SHAP)',
              badge: 'GLOBAL IMPORTANCE',
              icon: Sparkles,
              subtitle: 'Mathematical driver weights computed across validated customer datasets',
              data: shapChartData,
            })
          }
          className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/50 shadow-xl backdrop-blur-md flex flex-col justify-between cursor-pointer group transition"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Radar className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider group-hover:text-purple-300 transition">
                  Top Risk Factors (SHAP)
                </h3>
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

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-purple-300 flex items-center justify-between font-mono">
            <span>Click to inspect full SHAP attributions</span>
            <span>&rarr;</span>
          </div>
        </div>

        {/* CHART D: Model Benchmark Comparison */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'MODEL',
              title: 'Supervised ML Benchmark Comparison',
              badge: '3 CHAMPIONS VALIDATED',
              icon: Cpu,
              subtitle: 'Precision-Recall AUC, F1, and Detection Latency Across Model Candidates',
              data: {
                active: activeModelName,
                logistic: { name: 'Logistic Regression', f1: '0.4286', prAuc: '0.496', acc: '96.5%', rec: '56.3%' },
                rf: { name: 'Random Forest', f1: '0.2857', rocAuc: '0.811', acc: '95.6%', rec: '37.5%' },
                xgb: { name: 'XGBoost v2', f1: '0.3636', rocAuc: '0.812', acc: '97.0%', rec: '37.5%' },
              },
            })
          }
          className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/50 shadow-xl backdrop-blur-md flex flex-col justify-between cursor-pointer group transition"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider group-hover:text-indigo-300 transition">
                  Model Performance
                </h3>
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

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-indigo-300 flex items-center justify-between font-mono">
            <span>Click to inspect model registry</span>
            <span>&rarr;</span>
          </div>
        </div>

        {/* CHART E & F: Transaction Channel & Device Risk Matrix */}
        <div
          onClick={() =>
            setActiveModal({
              type: 'CHANNEL',
              title: 'Channel & Device Anomaly Matrix',
              badge: `${typeRisks.length} CHANNELS`,
              icon: CreditCard,
              subtitle: 'Detailed fraud breakdown across Web, UPI Mobile, POS, and Bot Signatures',
              data: typeRisks,
            })
          }
          className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-emerald-500/50 shadow-xl backdrop-blur-md flex flex-col justify-between cursor-pointer group transition"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider group-hover:text-emerald-300 transition">
                  Channel &amp; Device Risk
                </h3>
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

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-emerald-300 flex items-center justify-between font-mono">
            <span>Click to inspect all channels</span>
            <span>&rarr;</span>
          </div>
        </div>
      </div>

      {/* 6. In-App Security Alert Center */}
      <div className="p-5 sm:p-6 rounded-3xl bg-slate-900/60 border border-amber-800/40 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Security Alert Command Center
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400">
              {alerts.filter(a => !a.is_acknowledged).length} Unacknowledged
            </span>
            <button
              onClick={fetchAlerts}
              className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Refresh Alerts"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${alertsLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {alerts.length === 0 ? (
          <div className="py-6 text-center text-slate-400 text-xs flex flex-col items-center gap-1.5">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            <span>All system alerts are acknowledged and clear.</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {alerts.slice(0, 4).map((alert) => (
              <div
                key={alert.alert_id}
                onClick={() =>
                  setActiveModal({
                    type: 'ALERT',
                    title: `Security Alert #${alert.alert_id}`,
                    badge: alert.severity,
                    badgeColor:
                      alert.severity === 'CRITICAL' || alert.severity === 'HIGH'
                        ? 'bg-rose-950 text-rose-300 border-rose-800'
                        : 'bg-amber-950 text-amber-300 border-amber-800',
                    icon: ShieldAlert,
                    subtitle: `Triggered at ${alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Live'}`,
                    data: alert,
                  })
                }
                className={`p-3.5 rounded-2xl border transition-all text-xs space-y-2 cursor-pointer group ${
                  alert.is_acknowledged
                    ? 'bg-slate-950/50 border-slate-800 opacity-70'
                    : 'bg-slate-950/90 border-amber-700/60 shadow-lg shadow-amber-950/20 hover:border-amber-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      alert.severity === 'CRITICAL' || alert.severity === 'HIGH'
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-amber-950 text-amber-300 border border-amber-800'
                    }`}>
                      {alert.severity}
                    </span>
                    <span className="font-mono text-[10px] text-cyan-300">{alert.entity_id}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">
                    {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : ''}
                  </span>
                </div>

                <p className="text-slate-200 text-xs leading-snug">{alert.message}</p>

                <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                  <span className="text-[10px] font-mono text-slate-400">
                    {alert.is_acknowledged ? `Acknowledged by ${alert.acknowledged_by || 'Investigator'}` : 'Click to inspect in modal'}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {!alert.is_acknowledged && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleAcknowledgeAlert(alert.alert_id)
                        }}
                        disabled={acknowledgingId === alert.alert_id}
                        className="px-2 py-0.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-semibold transition border border-slate-700 disabled:opacity-50"
                      >
                        {acknowledgingId === alert.alert_id ? 'Ack...' : 'Acknowledge'}
                      </button>
                    )}
                    <span className="text-cyan-400 font-mono text-xs group-hover:translate-x-1 transition-transform">&rarr;</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 7. Live High-Risk Activity Feed Table */}
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
                  <tr
                    key={tx.id || tx.transaction_id}
                    onClick={() =>
                      setActiveModal({
                        type: 'TX',
                        title: `Transaction Assessment ${tx.transaction_id}`,
                        badge: tx.risk_level || 'HIGH RISK',
                        badgeColor: 'bg-rose-950 text-rose-300 border-rose-800',
                        icon: ShieldAlert,
                        subtitle: `Customer: ${tx.customer_id} • Amount: ${formatINR(tx.amount)}`,
                        data: tx,
                      })
                    }
                    className="hover:bg-slate-800/40 transition cursor-pointer"
                  >
                    <td className="py-3 font-mono font-bold text-cyan-400">
                      {tx.transaction_id}
                    </td>
                    <td className="py-3 font-mono text-slate-300">{tx.customer_id}</td>
                    <td className="py-3 font-mono text-white font-bold">{formatINR(tx.amount)}</td>
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
                        onClick={(e) => {
                          e.stopPropagation()
                          setActiveModal({
                            type: 'TX',
                            title: `Transaction Assessment ${tx.transaction_id}`,
                            badge: tx.risk_level || 'HIGH RISK',
                            badgeColor: 'bg-rose-950 text-rose-300 border-rose-800',
                            icon: ShieldAlert,
                            subtitle: `Customer: ${tx.customer_id} • Amount: ${formatINR(tx.amount)}`,
                            data: tx,
                          })
                        }}
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

      {/* ========================================================================= */}
      {/* STANDARDIZED VIEWPORT-CENTERED INSPECTION MODAL (Feature 1-10) */}
      {/* ========================================================================= */}
      {activeModal && (
        <GlobalCenterModal
          isOpen={Boolean(activeModal)}
          onClose={() => setActiveModal(null)}
          title={activeModal.title}
          subtitle={activeModal.subtitle}
          badge={activeModal.badge}
          badgeColor={activeModal.badgeColor}
          icon={activeModal.icon || Sparkles}
          maxWidth="max-w-2xl"
          footer={
            <div className="w-full flex items-center justify-between">
              <span className="text-[10px] font-mono text-slate-500">
                FraudLens AI Automated Intelligence Hub
              </span>
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition shadow"
              >
                Close (Done)
              </button>
            </div>
          }
        >
          {/* MODAL BODY 1: PERSONA DETAILS */}
          {activeModal.type === 'PERSONA' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Customer Name</span>
                    <strong className="text-white text-sm">{activeModal.data.name}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Account ID</span>
                    <strong className="text-cyan-300">{activeModal.data.id}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Fraud Rate Baseline</span>
                    <strong className="text-emerald-400">{activeModal.data.fraudRate}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Tenure</span>
                    <strong className="text-slate-200">{activeModal.data.tenure}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Simulated Balance</span>
                    <strong className="text-emerald-300">{activeModal.data.balance}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Location</span>
                    <strong className="text-slate-200">{activeModal.data.location}</strong>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80">
                  <span className="text-slate-500 block text-[10px] uppercase mb-1">Usual Merchants</span>
                  <span className="text-slate-300">{activeModal.data.usualMerchants}</span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-cyan-300">
                  🛡️ Pre-Auth Policy: {activeModal.data.policy}
                </div>
              </div>

              <button
                onClick={() => {
                  setActiveModal(null)
                  onOpenPayment && onOpenPayment(`scenario_${activeModal.data.name.toLowerCase()}_safe`)
                }}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold transition flex items-center justify-center gap-2 shadow-lg"
              >
                <CreditCard className="w-4 h-4" />
                <span>Open Pre-Auth Gateway for {activeModal.data.name}</span>
              </button>
            </div>
          )}

          {/* MODAL BODY 2: METRIC DRILLDOWN */}
          {activeModal.type === 'METRIC' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2.5">
                {Object.entries(activeModal.data).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                    <span className="text-slate-400 capitalize">{key.replace(/([A-Z])/g, ' $1')}:</span>
                    <strong className="text-white text-sm">{String(val)}</strong>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* MODAL BODY 3: TRANSACTION DETAIL */}
          {activeModal.type === 'TX' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Transaction ID</span>
                    <strong className="text-cyan-400 font-bold">{activeModal.data.transaction_id}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Customer</span>
                    <strong className="text-white">{activeModal.data.customer_id}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Amount</span>
                    <strong className="text-emerald-400 text-base">{formatINR(activeModal.data.amount)}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Risk Score</span>
                    <strong className="text-rose-400 text-base">{activeModal.data.risk_score} / 100</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">ML Probability</span>
                    <strong className="text-purple-300">{(Number(activeModal.data.fraud_probability || 0) * 100).toFixed(1)}%</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Severity Level</span>
                    <strong className="text-rose-400 uppercase">{activeModal.data.risk_level || 'HIGH'}</strong>
                  </div>
                </div>
              </div>

              {onSelectTransaction && (
                <button
                  onClick={() => {
                    const txId = activeModal.data.transaction_id
                    setActiveModal(null)
                    onSelectTransaction(txId)
                  }}
                  className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold transition flex items-center justify-center gap-2 shadow-lg"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Inspect Local TreeSHAP Attributions</span>
                </button>
              )}
            </div>
          )}

          {/* MODAL BODY 4: SHAP FACTORS */}
          {activeModal.type === 'SHAP' && (
            <div className="space-y-3 text-xs">
              <p className="text-slate-300 text-xs">
                Global TreeSHAP feature importances represent the absolute contribution of each feature towards fraud classification decisions:
              </p>
              <div className="space-y-2 font-mono">
                {Array.isArray(activeModal.data) &&
                  activeModal.data.map((f, i) => (
                    <div key={i} className="p-3 bg-slate-900 rounded-xl border border-slate-800 flex items-center justify-between">
                      <span className="text-white font-bold">{f.name}</span>
                      <span className="text-purple-300 font-bold">+{f.importance?.toFixed(4)} mean |SHAP|</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* MODAL BODY 5: MODEL DETAILS */}
          {activeModal.type === 'MODEL' && (
            <div className="space-y-3 text-xs font-mono">
              <div className="p-4 bg-slate-900 rounded-2xl border border-slate-800 space-y-2">
                <div className="text-cyan-300 font-bold text-sm">Champion Model: {activeModal.data.modelName || 'Logistic Regression'}</div>
                <div className="text-slate-400">Version: {activeModal.data.modelVersion} • Threshold: {activeModal.data.threshold}</div>
                <div className="grid grid-cols-2 gap-2 pt-2 text-[11px]">
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">F1 Score</span>
                    <strong className="text-emerald-400">{activeModal.data.f1Score}</strong>
                  </div>
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">PR-AUC</span>
                    <strong className="text-cyan-300">{activeModal.data.precisionAuc}</strong>
                  </div>
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Accuracy</span>
                    <strong className="text-white">{activeModal.data.accuracy}</strong>
                  </div>
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Recall</span>
                    <strong className="text-white">{activeModal.data.recall}</strong>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* MODAL BODY 6: ALERT DETAIL */}
          {activeModal.type === 'ALERT' && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-4 bg-slate-900 rounded-2xl border border-slate-800 space-y-3">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Alert Description</span>
                  <p className="text-slate-100 font-sans text-xs mt-1 leading-relaxed">{activeModal.data.message}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Entity ID</span>
                    <strong className="text-cyan-400">{activeModal.data.entity_id || 'System'}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Status</span>
                    <strong className={activeModal.data.is_acknowledged ? 'text-emerald-400' : 'text-amber-400'}>
                      {activeModal.data.is_acknowledged ? 'ACKNOWLEDGED' : 'PENDING REVIEW'}
                    </strong>
                  </div>
                </div>
              </div>

              {!activeModal.data.is_acknowledged && (
                <button
                  onClick={() => {
                    handleAcknowledgeAlert(activeModal.data.alert_id)
                    setActiveModal(null)
                  }}
                  className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold transition flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Acknowledge This Security Alert</span>
                </button>
              )}
            </div>
          )}
        </GlobalCenterModal>
      )}
    </div>
  )
}
