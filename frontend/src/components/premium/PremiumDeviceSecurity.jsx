import React, { useState, useEffect, useCallback } from 'react'
import {
  Laptop,
  Smartphone,
  Cpu,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Plus,
  Trash2,
  Lock,
  Globe,
} from 'lucide-react'
import { premiumApi } from '../../services/api'

export default function PremiumDeviceSecurity({ user }) {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionMsg, setActionMsg] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const loadDevices = useCallback(async () => {
    try {
      setLoading(true)
      const res = await premiumApi.getDevices()
      setDevices(res)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load hardware devices.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDevices()
  }, [loadDevices])

  const handleTrust = async (deviceId) => {
    try {
      setActionLoading(true)
      const res = await premiumApi.trustDevice(deviceId)
      setActionMsg(res.message || 'Device trust elevated to 100/100.')
      setTimeout(() => setActionMsg(null), 3000)
      loadDevices()
    } catch (err) {
      setError(err.message || 'Failed to trust device.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRevoke = async (deviceId) => {
    if (!window.confirm(`Revoke trust and remove device '${deviceId}' from hardware enclave?`)) return
    try {
      setActionLoading(true)
      const res = await premiumApi.revokeDevice(deviceId)
      setActionMsg(res.message || 'Device revoked and quarantined.')
      setTimeout(() => setActionMsg(null), 3000)
      loadDevices()
    } catch (err) {
      setError(err.message || 'Failed to revoke device.')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in text-slate-100">
      {/* Header */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-white font-mono tracking-tight flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-400" />
              HARDWARE ENCLAVE &amp; DEVICE SECURITY CENTER (SECTION 14 SPEC)
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700 font-bold">
              FIDO2 / ENCLAVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage authenticated hardware signatures, trust scores, and instant enclave access revocation.
          </p>
        </div>

        <button
          onClick={loadDevices}
          disabled={loading || actionLoading}
          className="self-start md:self-auto px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh Hardware Vault</span>
        </button>
      </div>

      {/* Action Messages */}
      {actionMsg && (
        <div className="p-3.5 rounded-2xl bg-emerald-950/80 border border-emerald-600 text-emerald-200 text-xs flex items-center gap-2 font-mono">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-2xl bg-rose-950/80 border border-rose-600 text-rose-200 text-xs flex items-center gap-2 font-mono">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Device Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {devices.map((dev) => {
          const isMac = dev.device_type?.includes('desktop') || dev.os?.includes('macOS')
          const isTrusted = dev.is_trusted && !dev.is_compromised

          return (
            <div
              key={dev.id || dev.device_identifier}
              className={`p-5 rounded-3xl bg-slate-900/90 border-2 transition-all duration-300 flex flex-col justify-between space-y-4 shadow-xl ${
                isTrusted
                  ? 'border-indigo-500/50 hover:border-indigo-400 shadow-[0_0_25px_rgba(99,102,241,0.15)]'
                  : 'border-rose-700/60 bg-rose-950/20'
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-3 rounded-2xl border ${
                        isTrusted
                          ? 'bg-indigo-950/90 border-indigo-500/60 text-indigo-400'
                          : 'bg-rose-950/90 border-rose-600 text-rose-400'
                      }`}
                    >
                      {isMac ? <Laptop className="w-6 h-6" /> : <Smartphone className="w-6 h-6" />}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white font-mono">{dev.device_name || dev.device_identifier}</h4>
                      <div className="text-[10px] font-mono text-slate-400">{dev.device_type}</div>
                    </div>
                  </div>

                  <span
                    className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                      isTrusted
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                        : 'bg-rose-950 text-rose-300 border-rose-700'
                    }`}
                  >
                    {isTrusted ? 'TRUSTED ENCLAVE' : 'QUARANTINED'}
                  </span>
                </div>

                {/* Specs List */}
                <div className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1.5 text-xs font-mono">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">OS</span>
                    <span className="truncate">{dev.os || 'Darwin / Linux'}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">Browser / Client</span>
                    <span className="truncate">{dev.browser || dev.browser_or_client || 'Encrypted Enclave'}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">Trust Score</span>
                    <span className="font-bold text-emerald-400">{dev.trust_score || 98} / 100</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">Location</span>
                    <span className="text-cyan-400">{dev.location_region || 'Mumbai / Cyber City'}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80">
                {!isTrusted ? (
                  <button
                    type="button"
                    onClick={() => handleTrust(dev.device_identifier)}
                    disabled={actionLoading}
                    className="flex-1 py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold uppercase transition flex items-center justify-center gap-1.5"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Trust Device</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleRevoke(dev.device_identifier)}
                    disabled={actionLoading}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-900 hover:bg-rose-950/80 border border-slate-700 hover:border-rose-600 text-slate-300 hover:text-rose-300 font-mono text-xs font-semibold transition flex items-center justify-center gap-1.5"
                  >
                    <ShieldX className="w-3.5 h-3.5" />
                    <span>Revoke Enclave</span>
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
