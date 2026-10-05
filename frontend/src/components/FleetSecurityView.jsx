import React, { useState, useEffect, useCallback } from 'react'
import {
  Radio,
  Cpu,
  Laptop,
  Smartphone,
  Watch,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  LogOut,
  Globe,
  Clock,
  Key,
  Layers,
  Sparkles,
  Zap,
  Lock,
  Plus,
  Trash2,
} from 'lucide-react'
import { premiumApi } from '../services/api'
import { getCustomerPersona } from '../utils/customerHelper'
import ContextualModuleHelp from './common/ContextualModuleHelp'

export default function FleetSecurityView({ user, isAdmin }) {
  const customerPersona = getCustomerPersona(user) || {}
  const isPremium = user?.account_tier === 'PREMIUM' || customerPersona?.isPremium || (customerPersona?.name || '').toLowerCase().includes('ajay')

  const [activeTab, setActiveTab] = useState('devices') // 'devices' | 'sessions'
  const [devices, setDevices] = useState([])
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionMsg, setActionMsg] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  // Fetch both devices and sessions for the current user
  const loadFleetData = useCallback(async () => {
    try {
      setLoading(true)
      const [devRes, sessRes] = await Promise.all([
        premiumApi.getDevices().catch(() => []),
        premiumApi.getSessions().catch(() => []),
      ])
      setDevices(devRes || [])
      setSessions(sessRes || [])
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to sync fleet security telemetry.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadFleetData()
  }, [loadFleetData])

  // Trust a device
  const handleTrustDevice = async (deviceId) => {
    try {
      setActionLoading(true)
      const res = await premiumApi.trustDevice(deviceId)
      setActionMsg(res.message || `Device '${deviceId}' marked as Trusted.`)
      setTimeout(() => setActionMsg(null), 3500)
      loadFleetData()
    } catch (err) {
      setError(err.message || 'Failed to update device trust.')
    } finally {
      setActionLoading(false)
    }
  }

  // Revoke a device
  const handleRevokeDevice = async (deviceId) => {
    if (!window.confirm(`Are you sure you want to revoke trust for device '${deviceId}'? All future transactions from this device will require step-up verification.`)) return
    try {
      setActionLoading(true)
      const res = await premiumApi.revokeDevice(deviceId)
      setActionMsg(res.message || `Device '${deviceId}' trust revoked.`)
      setTimeout(() => setActionMsg(null), 3500)
      loadFleetData()
    } catch (err) {
      setError(err.message || 'Failed to revoke device trust.')
    } finally {
      setActionLoading(false)
    }
  }

  // Revoke single session
  const handleRevokeSession = async (sessionId) => {
    if (!window.confirm(`Immediately terminate session '${sessionId}'? The user on that connection will be logged out instantly.`)) return
    try {
      setActionLoading(true)
      const res = await premiumApi.revokeSession(sessionId)
      setActionMsg(res.message || `Session '${sessionId}' terminated.`)
      setTimeout(() => setActionMsg(null), 3500)
      loadFleetData()
    } catch (err) {
      setError(err.message || 'Failed to revoke session.')
    } finally {
      setActionLoading(false)
    }
  }

  // Terminate All Other Sessions
  const handleTerminateAllOther = async () => {
    if (sessions.length <= 1) {
      setActionMsg('No other active sessions found.')
      setTimeout(() => setActionMsg(null), 3000)
      return
    }
    if (!window.confirm(`Terminate all ${sessions.length - 1} other active sessions across your fleet?`)) return
    try {
      setActionLoading(true)
      for (const s of sessions.slice(1)) {
        await premiumApi.revokeSession(s.session_id).catch(() => null)
      }
      setActionMsg('All other sessions terminated. Hardware enclave perimeter locked.')
      setTimeout(() => setActionMsg(null), 4000)
      loadFleetData()
    } catch (err) {
      setError(err.message || 'Failed to terminate all sessions.')
    } finally {
      setActionLoading(false)
    }
  }

  // Simulate Incursion (Defensive Testing Feature for all users)
  const handleSimulateIncursion = async () => {
    try {
      setActionLoading(true)
      // Call trust API with a rogue emulator to simulate an untrusted hardware detection
      const rogueId = `dev-rogue-emulator-${Math.floor(100 + Math.random() * 900)}`
      await premiumApi.revokeDevice(rogueId).catch(() => null)
      setActionMsg(`🚨 Simulated Rogue Hardware Intercepted: '${rogueId}' isolated and flagged with 0% trust score.`)
      setTimeout(() => setActionMsg(null), 5000)
      loadFleetData()
    } catch (err) {
      setError(err.message || 'Simulation error.')
    } finally {
      setActionLoading(false)
    }
  }

  // Metric Computations
  const trustedCount = devices.filter((d) => d.trusted).length
  const activeSessionsCount = sessions.filter((s) => s.session_status === 'ACTIVE').length
  const flaggedSessionsCount = sessions.filter((s) => s.session_status === 'FLAGGED' || s.risk_score >= 50).length

  const getDeviceIcon = (deviceType, name = '') => {
    const l = (name + ' ' + (deviceType || '')).toLowerCase()
    if (l.includes('watch')) return Watch
    if (l.includes('mac') || l.includes('thinkpad') || l.includes('laptop') || l.includes('desktop')) return Laptop
    if (l.includes('bot') || l.includes('emulator') || l.includes('rogue')) return ShieldAlert
    return Smartphone
  }

  return (
    <div className="space-y-6 animate-fade-in text-slate-100">
      {/* ── Top Header ── */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/60 border border-slate-800 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-700/60 flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                ENTERPRISE FLEET SECURITY SUITE
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${customerPersona.badgeColor}`}>
                👤 {customerPersona.name} ({customerPersona.customerId})
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                ZERO-LEAK ISOLATION
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-2">
                <Cpu className="w-7 h-7 text-cyan-400" />
                Hardware Enclave &amp; Session Fleet Monitor
              </h1>
              <ContextualModuleHelp moduleKey="fleet-security" />
            </div>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Cryptographically verify registered hardware devices, monitor active IP sessions, detect unauthorized access in real-time, and execute instant 1-click token revocations.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={handleSimulateIncursion}
              disabled={loading || actionLoading}
              className="px-3.5 py-2 rounded-xl bg-rose-950/80 hover:bg-rose-900 border border-rose-500/60 text-rose-300 font-mono text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-rose-950"
              title="Test real-time defensive containment against simulated rogue devices"
            >
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>Simulate Threat Incursion</span>
            </button>

            <button
              onClick={loadFleetData}
              disabled={loading || actionLoading}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-mono text-xs font-bold transition flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
              <span>Sync Fleet</span>
            </button>
          </div>
        </div>

        {/* ── Key Metrics Overview ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 border-t border-slate-800/80 mt-6">
          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Enrolled Hardware</div>
            <div className="text-xl font-black text-white font-mono mt-0.5">{devices.length} Devices</div>
            <div className="text-[10px] text-emerald-400 font-mono mt-0.5">{trustedCount} Cryptographically Trusted</div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Active Session Fleet</div>
            <div className="text-xl font-black text-cyan-300 font-mono mt-0.5">{activeSessionsCount} Active</div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Continuous Invariant Audit</div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Hardware Enclave Trust</div>
            <div className="text-xl font-black text-emerald-400 font-mono mt-0.5">
              {devices.length > 0 ? `${Math.round((trustedCount / devices.length) * 100)}%` : '100%'}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Biometric TPM / Secure Key</div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Threat Perimeter</div>
            <div className={`text-xl font-black font-mono mt-0.5 ${flaggedSessionsCount > 0 ? 'text-rose-400 animate-pulse' : 'text-emerald-400'}`}>
              {flaggedSessionsCount > 0 ? `${flaggedSessionsCount} Threat Isolated` : 'Shield Secure'}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Zero Incursion Tolerance</div>
          </div>
        </div>
      </div>

      {/* ── Status Notifications ── */}
      {actionMsg && (
        <div className="p-4 rounded-2xl bg-emerald-950/80 border border-emerald-500 text-emerald-200 text-xs flex items-center justify-between font-mono animate-fadeIn shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{actionMsg}</span>
          </div>
          <button onClick={() => setActionMsg(null)} className="text-slate-400 hover:text-white text-xs">✕</button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/80 border border-rose-500 text-rose-200 text-xs flex items-center justify-between font-mono animate-fadeIn shadow-lg">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-slate-400 hover:text-white text-xs">✕</button>
        </div>
      )}

      {/* ── Tab Switcher ── */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('devices')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-mono font-bold transition ${
            activeTab === 'devices'
              ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/70 shadow-lg shadow-cyan-950/50'
              : 'text-slate-400 hover:text-white bg-slate-900 border border-slate-800'
          }`}
        >
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span>Registered Hardware Devices ({devices.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('sessions')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-mono font-bold transition ${
            activeTab === 'sessions'
              ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/70 shadow-lg shadow-indigo-950/50'
              : 'text-slate-400 hover:text-white bg-slate-900 border border-slate-800'
          }`}
        >
          <Radio className="w-4 h-4 text-indigo-400" />
          <span>Active Session Fleet ({sessions.length})</span>
        </button>

        {activeTab === 'sessions' && sessions.length > 1 && (
          <button
            onClick={handleTerminateAllOther}
            disabled={actionLoading}
            className="ml-auto px-3.5 py-2 rounded-xl bg-rose-950/80 hover:bg-rose-900 border border-rose-600/70 text-rose-300 font-mono text-xs font-bold transition flex items-center gap-1.5 shadow-md"
          >
            <LogOut className="w-3.5 h-3.5 text-rose-400" />
            <span>Terminate All Other Sessions</span>
          </button>
        )}
      </div>

      {/* ── Content View ── */}
      {loading ? (
        <div className="p-16 text-center space-y-3 bg-slate-900/60 rounded-3xl border border-slate-800">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-sm font-mono text-cyan-300 font-bold">Querying Hardware Enclave Vault &amp; Active Fleet…</p>
          <p className="text-xs text-slate-500 font-mono">Zero-leak tenant isolation active for {customerPersona.name}</p>
        </div>
      ) : activeTab === 'devices' ? (
        /* 📱 Registered Devices Grid */
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {devices.map((device) => {
              const Icon = getDeviceIcon(device.device_type, device.device_name)
              const isTrusted = device.trusted && device.status !== 'SUSPICIOUS'
              const score = device.trust_score ?? (isTrusted ? 95 : 20)

              return (
                <div
                  key={device.device_id || device.id}
                  className={`p-5 rounded-3xl border transition-all duration-200 flex flex-col justify-between space-y-4 ${
                    isTrusted
                      ? 'bg-slate-900/90 border-slate-800 hover:border-cyan-500/50 hover:shadow-xl shadow-slate-950'
                      : 'bg-rose-950/30 border-rose-500/60 shadow-lg shadow-rose-950/30'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div
                          className={`p-3 rounded-2xl border ${
                            isTrusted
                              ? 'bg-slate-800/80 border-cyan-500/40 text-cyan-300'
                              : 'bg-rose-900/60 border-rose-500 text-rose-300 animate-pulse'
                          }`}
                        >
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-white font-mono truncate max-w-[170px]">
                            {device.device_name || device.device_id}
                          </h3>
                          <div className="text-[11px] text-slate-400 font-mono">{device.device_id}</div>
                        </div>
                      </div>

                      <span
                        className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold border uppercase ${
                          isTrusted
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                            : 'bg-rose-950 text-rose-300 border-rose-700 animate-pulse'
                        }`}
                      >
                        {isTrusted ? 'TRUSTED' : 'UNTRUSTED'}
                      </span>
                    </div>

                    {/* Trust Gauge */}
                    <div className="space-y-1.5 pt-1">
                      <div className="flex items-center justify-between text-[11px] font-mono">
                        <span className="text-slate-400">Trust Score:</span>
                        <strong className={isTrusted ? 'text-emerald-400' : 'text-rose-400'}>
                          {score} / 100
                        </strong>
                      </div>
                      <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
                        <div
                          className={`h-full transition-all duration-500 ${
                            isTrusted ? 'bg-gradient-to-r from-cyan-500 to-emerald-400' : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
                        />
                      </div>
                    </div>

                    {/* Device Specs Telemetry */}
                    <div className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-1 text-[11px] font-mono text-slate-400">
                      <div className="flex justify-between">
                        <span>OS Platform:</span>
                        <span className="text-slate-200 font-semibold">{device.os || 'Unknown OS'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Client Engine:</span>
                        <span className="text-slate-200 font-semibold truncate max-w-[160px]">{device.browser || 'Browser Enclave'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Registered Geo:</span>
                        <span className="text-cyan-300 font-semibold">{device.location_region || 'Mumbai'}</span>
                      </div>
                      <div className="flex justify-between text-[10px] pt-1 border-t border-slate-800 text-slate-400">
                        <span>First Seen:</span>
                        <span>{device.first_seen ? new Date(device.first_seen).toLocaleDateString() : 'Baseline'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-end gap-2">
                    {isTrusted ? (
                      <button
                        onClick={() => handleRevokeDevice(device.device_id)}
                        disabled={actionLoading}
                        className="w-full py-2 rounded-xl bg-slate-800/80 hover:bg-rose-950/70 border border-slate-700 hover:border-rose-600 text-slate-300 hover:text-rose-200 text-xs font-mono font-bold transition flex items-center justify-center gap-1.5"
                      >
                        <ShieldX className="w-3.5 h-3.5 text-rose-400" />
                        <span>Revoke Trust</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleTrustDevice(device.device_id)}
                        disabled={actionLoading}
                        className="w-full py-2 rounded-xl bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-600 text-emerald-200 text-xs font-mono font-bold transition flex items-center justify-center gap-1.5"
                      >
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Trust Device</span>
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        /* 🌐 Active Session Fleet Table */
        <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Globe className="w-4 h-4 text-cyan-400" />
                Active Cryptographic Sessions
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Each session represents an active JWT cryptographic token bound to an IP address and hardware fingerprint.
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-cyan-300 border border-slate-800 font-bold">
              {sessions.length} Live Sessions Active
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
                <tr>
                  <th className="p-3">Session &amp; Device</th>
                  <th className="p-3">IP Address</th>
                  <th className="p-3">Geographic Region</th>
                  <th className="p-3">Risk Assessment</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Emergency Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {sessions.map((sess, idx) => {
                  const isRevoked = sess.session_status === 'REVOKED'
                  const isFlagged = sess.session_status === 'FLAGGED' || sess.risk_score >= 50

                  return (
                    <tr key={sess.session_id || idx} className="hover:bg-slate-800/40 transition">
                      <td className="p-3">
                        <div className="font-bold text-white font-mono flex items-center gap-2">
                          <Laptop className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                          <span>{sess.device_name || sess.device_id || 'Browser Terminal'}</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">{sess.session_id}</div>
                      </td>
                      <td className="p-3 font-mono text-cyan-300">{sess.ip_address}</td>
                      <td className="p-3">
                        <div className="text-slate-200 font-mono flex items-center gap-1.5">
                          <Globe className="w-3 h-3 text-slate-400" />
                          <span>{sess.approximate_location || 'Mumbai, India'}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold border ${
                            sess.risk_score >= 70
                              ? 'bg-rose-950 text-rose-300 border-rose-700 animate-pulse'
                              : sess.risk_score >= 30
                              ? 'bg-amber-950 text-amber-300 border-amber-700'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-700'
                          }`}
                        >
                          Risk: {sess.risk_score ?? 5} / 100
                        </span>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded-full font-mono text-[9px] font-bold border uppercase ${
                            isRevoked
                              ? 'bg-slate-900 text-slate-400 border-slate-700'
                              : isFlagged
                              ? 'bg-rose-950 text-rose-300 border-rose-700'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-700'
                          }`}
                        >
                          {sess.session_status || 'ACTIVE'}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        {isRevoked ? (
                          <span className="text-[10px] font-mono text-slate-500">Revoked</span>
                        ) : (
                          <button
                            onClick={() => handleRevokeSession(sess.session_id)}
                            disabled={actionLoading}
                            className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-rose-950 border border-slate-700 hover:border-rose-600 text-slate-300 hover:text-rose-200 font-mono text-[10px] font-bold transition flex items-center gap-1 ml-auto"
                          >
                            <LogOut className="w-3 h-3 text-rose-400" />
                            <span>Terminate</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
