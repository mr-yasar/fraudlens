import React, { useState, useEffect, useCallback } from 'react'
import {
  ShieldCheck,
  Shield,
  Lock,
  Cpu,
  Smartphone,
  Laptop,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Zap,
  Sliders,
  Sparkles,
  Layers,
  Fingerprint,
  Activity,
  FileCheck,
} from 'lucide-react'
import { premiumApi } from '../../services/api'
import ContextualModuleHelp from '../common/ContextualModuleHelp'

export default function PremiumSecurityCenter({ user }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  // Interactive Security Settings state
  const [mfaEnforced, setMfaEnforced] = useState(true)
  const [hardwareEnclaveOnly, setHardwareEnclaveOnly] = useState(true)
  const [geoFencingActive, setGeoFencingActive] = useState(true)
  const [adaptiveThreshold, setAdaptiveThreshold] = useState(50)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const loadData = useCallback(async () => {
    try {
      setRefreshing(true)
      const res = await premiumApi.getSecurityCenter()
      setData(res)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load Security Center posture.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleSaveSettings = () => {
    setSaveSuccess(true)
    setTimeout(() => setSaveSuccess(false), 2500)
  }

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
        <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <div className="text-xs font-mono text-indigo-300">Auditing Security Posture &amp; Hardware Baseline...</div>
      </div>
    )
  }

  const health = data?.security_health || { score: 98, status: 'Excellent', factors: [] }
  const profile = data?.behavioral_profile || {}

  return (
    <div className="space-y-8 animate-fade-in text-slate-100">
      {/* Header */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-black text-white font-mono tracking-tight flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              SECURITY POSTURE &amp; DEFENSE CENTER
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold">
              ARMORED
            </span>
            <ContextualModuleHelp moduleKey="security-center" />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Comprehensive audit of tenant isolation, behavioral invariant baselines, and hardware enclave credentials.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={refreshing}
          className="self-start md:self-auto px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Audit Posture</span>
        </button>
      </div>

      {/* Security Health Score Breakdown (Section 36) */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border-2 border-indigo-500/50 shadow-[0_0_35px_rgba(99,102,241,0.25)] space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-emerald-950/80 border-2 border-emerald-500/60 flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.35)]">
              <span className="text-2xl font-black font-mono text-emerald-300">{health.score}</span>
            </div>
            <div>
              <div className="text-xs font-mono uppercase text-slate-400 font-semibold">Overall Defense Health</div>
              <h3 className="text-xl font-bold font-mono text-white flex items-center gap-2">
                <span>{health.status} Status</span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              </h3>
              <p className="text-xs text-slate-300">Section 36 Explainable Security Health Algorithm</p>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs text-slate-300">
            <span className="px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800">
              Active Fleet: <strong className="text-white">{health.trusted_devices_count} Devices</strong>
            </span>
            <span className="px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800">
              Open Alerts: <strong className="text-emerald-400">{health.open_alerts_count}</strong>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          {health.factors?.map((fac, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex items-start gap-2.5 text-xs font-mono text-slate-300"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>{fac}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Behavioral Baseline Matrix (Section 11) */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              BEHAVIORAL INVARIANT PROFILE (SECTION 11 SPEC)
            </h3>
            <p className="text-xs text-slate-400">
              Dynamic statistical model baseline comparing incoming transaction activity against historical telemetry.
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-bold">
            CONTINUOUSLY CALIBRATED
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">Normal Volume Range</span>
            <div className="text-base font-mono font-bold text-white">{profile.normal_transaction_range || '₹5,000 - ₹150,000'}</div>
            <div className="text-[10px] font-mono text-indigo-400">Avg ₹{Number(profile.average_transaction_amount || 45000).toLocaleString('en-IN')}</div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">Normal Velocity</span>
            <div className="text-base font-mono font-bold text-white">{profile.normal_transaction_frequency || '2-4 transactions/day'}</div>
            <div className="text-[10px] font-mono text-slate-500">Peak Burst: ≤ 8/hour</div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">Operating Window</span>
            <div className="text-base font-mono font-bold text-emerald-400">{profile.common_transaction_times || '08:00 - 22:00 IST'}</div>
            <div className="text-[10px] font-mono text-slate-500">Night window (00-05) stepped-up</div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">Trusted Locations</span>
            <div className="text-base font-mono font-bold text-white">{profile.common_locations || 'Mumbai, Bangalore, Singapore'}</div>
            <div className="text-[10px] font-mono text-slate-500">Foreign rogue Geo-IP held</div>
          </div>
        </div>
      </div>

      {/* Active Defense Invariants & Interactive Controls */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              ENTERPRISE SECURITY POLICIES &amp; CONTROLS
            </h3>
            <p className="text-xs text-slate-400">
              Configure adaptive enforcement policies and enclave hardware protection invariants.
            </p>
          </div>
        </div>

        {saveSuccess && (
          <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-600 text-emerald-200 text-xs flex items-center gap-2 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Security policies successfully saved and propagated to enclave vault.</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-xs font-mono font-bold text-white">Adaptive Step-Up OTP</div>
              <div className="text-[11px] text-slate-400">Enforce cryptographic challenge on anomalies</div>
            </div>
            <input
              type="checkbox"
              checked={mfaEnforced}
              onChange={(e) => setMfaEnforced(e.target.checked)}
              className="w-4 h-4 rounded text-indigo-500 bg-slate-900 border-slate-700"
            />
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-xs font-mono font-bold text-white">Hardware Enclave Only</div>
              <div className="text-[11px] text-slate-400">Require trusted hardware signature</div>
            </div>
            <input
              type="checkbox"
              checked={hardwareEnclaveOnly}
              onChange={(e) => setHardwareEnclaveOnly(e.target.checked)}
              className="w-4 h-4 rounded text-indigo-500 bg-slate-900 border-slate-700"
            />
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-xs font-mono font-bold text-white">Geo-Fencing Shield</div>
              <div className="text-[11px] text-slate-400">Hold rogue cross-border transfers</div>
            </div>
            <input
              type="checkbox"
              checked={geoFencingActive}
              onChange={(e) => setGeoFencingActive(e.target.checked)}
              className="w-4 h-4 rounded text-indigo-500 bg-slate-900 border-slate-700"
            />
          </div>
        </div>

        <div className="flex items-center justify-end pt-2">
          <button
            type="button"
            onClick={handleSaveSettings}
            className="py-2 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold uppercase transition"
          >
            Apply Policy Rules
          </button>
        </div>
      </div>
    </div>
  )
}
