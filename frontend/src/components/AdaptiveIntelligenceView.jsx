import React, { useState, useEffect, useCallback } from 'react'
import {
  ShieldAlert,
  Flame,
  Activity,
  Sliders,
  Cpu,
  Layers,
  Lock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Zap,
  TrendingUp,
  Share2,
  Users,
  Eye,
  Check,
  X,
  Sparkles,
  GitBranch,
} from 'lucide-react'
import { adaptiveApi } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function AdaptiveIntelligenceView({ onSelectTransaction, onOpenInvestigation }) {
  const { isAdmin } = useAuth()
  const [activeTab, setActiveTab] = useState('threats') // 'threats' | 'rules' | 'federated' | 'comparison' | 'feedback'

  // Threats & Drift State
  const [threatData, setThreatData] = useState(null)
  const [threatLoading, setThreatLoading] = useState(true)

  // Rules & Candidate State
  const [rules, setRules] = useState([])
  const [candidates, setCandidates] = useState([])
  const [rulesLoading, setRulesLoading] = useState(false)
  const [newRuleModalOpen, setNewRuleModalOpen] = useState(false)
  const [newRuleForm, setNewRuleForm] = useState({
    rule_id: `CAND-${Date.now().toString().slice(-4)}`,
    rule_name: '',
    condition_description: '',
    category: 'VELOCITY',
    proposed_action: 'FLAG_REVIEW',
    rationale: '',
  })

  // Federated Simulation State
  const [fedSimData, setFedSimData] = useState(null)
  const [simulating, setSimulating] = useState(false)
  const [simRounds, setSimRounds] = useState(3)

  // Model Comparison State
  const [comparisonData, setComparisonData] = useState(null)

  // Feedback State
  const [feedbackSuccess, setFeedbackSuccess] = useState('')

  // Action status feedback
  const [actionMessage, setActionMessage] = useState('')

  // Load threats
  const loadThreats = useCallback(async () => {
    setThreatLoading(true)
    try {
      const data = await adaptiveApi.getThreats()
      setThreatData(data)
    } catch (err) {
      console.error('Failed to load threats:', err)
    } finally {
      setThreatLoading(false)
    }
  }, [])

  // Load rules & candidate rules
  const loadRules = useCallback(async () => {
    setRulesLoading(true)
    try {
      const [effList, candList] = await Promise.all([
        adaptiveApi.getRuleEffectiveness(),
        adaptiveApi.getCandidateRules(),
      ])
      setRules(effList || [])
      setCandidates(candList || [])
    } catch (err) {
      console.error('Failed to load rules:', err)
    } finally {
      setRulesLoading(false)
    }
  }, [])

  // Load model comparison
  const loadComparison = useCallback(async () => {
    try {
      const data = await adaptiveApi.getModelComparison()
      setComparisonData(data)
    } catch (err) {
      console.error('Failed to load comparison:', err)
    }
  }, [])

  useEffect(() => {
    loadThreats()
    loadRules()
    loadComparison()
  }, [loadThreats, loadRules, loadComparison])

  // Approve Candidate Rule
  const handleApproveRule = async (ruleId) => {
    try {
      await adaptiveApi.approveCandidateRule(ruleId)
      setActionMessage(`Candidate Rule ${ruleId} approved successfully.`)
      loadRules()
      setTimeout(() => setActionMessage(''), 4000)
    } catch (err) {
      alert(err.message || 'Failed to approve rule')
    }
  }

  // Reject Candidate Rule
  const handleRejectRule = async (ruleId) => {
    const reason = prompt('Enter rejection rationale:', 'High false positive risk')
    if (!reason) return
    try {
      await adaptiveApi.rejectCandidateRule(ruleId, reason)
      setActionMessage(`Candidate Rule ${ruleId} rejected.`)
      loadRules()
      setTimeout(() => setActionMessage(''), 4000)
    } catch (err) {
      alert(err.message || 'Failed to reject rule')
    }
  }

  // Create Candidate Rule
  const handleCreateRule = async (e) => {
    e.preventDefault()
    try {
      await adaptiveApi.createCandidateRule(newRuleForm)
      setNewRuleModalOpen(false)
      setActionMessage(`New candidate rule ${newRuleForm.rule_id} submitted for review.`)
      loadRules()
      setTimeout(() => setActionMessage(''), 4000)
    } catch (err) {
      alert(err.message || 'Failed to create candidate rule')
    }
  }

  // Run Federated Simulation
  const handleRunSimulation = async () => {
    setSimulating(true)
    try {
      const res = await adaptiveApi.runFederatedSimulation(simRounds)
      setFedSimData(res)
      setActionMessage('Federated aggregation simulation completed successfully with zero raw data transfers!')
      setTimeout(() => setActionMessage(''), 5000)
    } catch (err) {
      alert(err.message || 'Failed to run federated simulation')
    } finally {
      setSimulating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-900/40 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-3">
              <div className="p-2.5 bg-indigo-500/20 border border-indigo-500/40 rounded-xl text-indigo-400 shadow-lg shadow-indigo-500/20">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
                  Adaptive Fraud Intelligence <span className="text-indigo-400 text-xs px-2 py-0.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 uppercase tracking-widest font-mono">Phase 2</span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Real-time threat pattern detection, adaptive rule governance, and privacy-preserving federated simulation.
                </p>
              </div>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-3">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl px-4 py-2 text-right">
              <div className="text-[10px] uppercase font-mono text-slate-400">Drift Status</div>
              <div className="text-sm font-bold text-emerald-400 flex items-center gap-1 justify-end">
                <Activity className="w-3.5 h-3.5" />
                {threatData?.model_drift_status || 'STABLE'}
              </div>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl px-4 py-2 text-right">
              <div className="text-[10px] uppercase font-mono text-slate-400">Active Threats</div>
              <div className="text-sm font-bold text-rose-400">
                {threatData?.active_threats ?? 0}
              </div>
            </div>
            <button
              onClick={() => {
                loadThreats()
                loadRules()
                loadComparison()
              }}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
              title="Refresh Intelligence Data"
            >
              <RefreshCw className={`w-4 h-4 ${threatLoading || rulesLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 mt-6 pt-4 border-t border-slate-800/80 overflow-x-auto">
          {[
            { id: 'threats', label: 'Emerging Threats', icon: Flame, badge: threatData?.active_threats },
            { id: 'rules', label: 'Rule Adaptation', icon: Sliders, badge: candidates.filter(c => c.status === 'CANDIDATE').length },
            { id: 'federated', label: 'Federated Simulation', icon: Lock, badge: 'Privacy-Safe' },
            { id: 'comparison', label: 'Model Benchmarks', icon: Cpu },
          ].map(tab => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition whitespace-nowrap ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800/80'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
                {tab.badge !== undefined && (
                  <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold ${
                    isActive ? 'bg-indigo-950 text-indigo-200' : 'bg-slate-800 text-slate-300'
                  }`}>
                    {tab.badge}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Action Notice */}
      {actionMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 text-xs flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage('')} className="text-emerald-400 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* ================= TAB 1: EMERGING THREATS ================= */}
      {activeTab === 'threats' && (
        <div className="space-y-6">
          {/* Drift Gauges */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <div className="text-xs text-slate-400 font-mono uppercase">Model Probability Shift</div>
              <div className="flex items-end justify-between">
                <span className="text-xl font-bold text-white">{(threatData?.drift_score * 100 || 2.4).toFixed(1)}%</span>
                <span className="text-xs text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
                  {threatData?.model_drift_status || 'STABLE'}
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div
                  className="bg-emerald-500 h-1.5 rounded-full"
                  style={{ width: `${Math.min(100, (threatData?.drift_score || 0.05) * 100)}%` }}
                />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <div className="text-xs text-slate-400 font-mono uppercase">Velocity Density Shift</div>
              <div className="flex items-end justify-between">
                <span className="text-xl font-bold text-white">
                  {((threatData?.feature_drift_indicators?.velocity_density_shift || 0.04) * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/60 font-mono">
                  NOMINAL
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div
                  className="bg-indigo-500 h-1.5 rounded-full"
                  style={{ width: `${Math.min(100, (threatData?.feature_drift_indicators?.velocity_density_shift || 0.04) * 100)}%` }}
                />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <div className="text-xs text-slate-400 font-mono uppercase">Device Novelty Shift</div>
              <div className="flex items-end justify-between">
                <span className="text-xl font-bold text-white">
                  {((threatData?.feature_drift_indicators?.device_novelty_drift || 0.08) * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/60 font-mono">
                  MONITORED
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div
                  className="bg-amber-500 h-1.5 rounded-full"
                  style={{ width: `${Math.min(100, (threatData?.feature_drift_indicators?.device_novelty_drift || 0.08) * 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Active Emerging Patterns List */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Flame className="w-4 h-4 text-rose-400" />
                  Emerging Threat Patterns ({threatData?.emerging_patterns?.length || 0})
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated cluster pattern analysis across recent transactions and device telemetry.
                </p>
              </div>
            </div>

            {threatData?.emerging_patterns?.length === 0 ? (
              <div className="p-8 text-center rounded-xl bg-slate-950/60 border border-slate-800/80 text-slate-400 text-xs">
                No active critical threat patterns detected in recent transaction window.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {threatData?.emerging_patterns?.map((pattern) => {
                  const isCrit = pattern.severity === 'CRITICAL'
                  const isHigh = pattern.severity === 'HIGH'
                  return (
                    <div
                      key={pattern.pattern_id}
                      className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 space-y-3 transition"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[10px] text-slate-400">{pattern.pattern_id}</span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase font-mono border ${
                              isCrit
                                ? 'bg-rose-950 text-rose-300 border-rose-800'
                                : isHigh
                                ? 'bg-amber-950 text-amber-300 border-amber-800'
                                : 'bg-indigo-950 text-indigo-300 border-indigo-800'
                            }`}>
                              {pattern.severity}
                            </span>
                          </div>
                          <h4 className="text-sm font-bold text-white mt-1">{pattern.pattern_name}</h4>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">
                          Confidence: {(pattern.confidence * 100).toFixed(0)}%
                        </span>
                      </div>

                      <div className="text-xs text-slate-300 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                        <span className="text-slate-400 font-semibold">Target Segment: </span>
                        {pattern.affected_segment}
                      </div>

                      <div className="space-y-1">
                        <div className="text-[10px] font-mono text-slate-400 uppercase">Evidence:</div>
                        <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                          {pattern.evidence.map((ev, i) => (
                            <li key={i}>{ev}</li>
                          ))}
                        </ul>
                      </div>

                      {pattern.sample_transaction_ids?.length > 0 && (
                        <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                          <div className="text-[10px] font-mono text-slate-400">
                            Samples: {pattern.sample_transaction_ids.slice(0, 2).join(', ')}
                          </div>
                          <button
                            onClick={() => onOpenInvestigation && onOpenInvestigation()}
                            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                          >
                            Open Case &rarr;
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= TAB 2: RULE ADAPTATION ================= */}
      {activeTab === 'rules' && (
        <div className="space-y-6">
          {/* Active Rule Performance Table */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  Active Rule Effectiveness ({rules.length})
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Hit frequency, confirmed fraud accuracy, and false positive metrics across historical transactions.
                </p>
              </div>
              {isAdmin && (
                <button
                  onClick={() => setNewRuleModalOpen(true)}
                  className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 transition"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Propose Rule
                </button>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="p-3">Rule ID & Name</th>
                    <th className="p-3">Category</th>
                    <th className="p-3 text-center">Hits</th>
                    <th className="p-3 text-center">Confirmed Fraud</th>
                    <th className="p-3 text-center">False Positive %</th>
                    <th className="p-3 text-center">Effectiveness</th>
                    <th className="p-3">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {rules.map((r) => (
                    <tr key={r.rule_id} className="hover:bg-slate-800/40 transition">
                      <td className="p-3">
                        <div className="font-mono font-bold text-white">{r.rule_id}</div>
                        <div className="text-[11px] text-slate-400">{r.rule_name}</div>
                      </td>
                      <td className="p-3 font-mono text-slate-400">{r.category}</td>
                      <td className="p-3 text-center font-bold text-white">{r.total_hits}</td>
                      <td className="p-3 text-center font-bold text-rose-400">{r.confirmed_fraud_hits}</td>
                      <td className="p-3 text-center font-mono">{(r.false_positive_rate * 100).toFixed(1)}%</td>
                      <td className="p-3 text-center">
                        <span className="px-2 py-0.5 rounded-full font-mono font-bold text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800">
                          {(r.effectiveness_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="p-3">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {r.recommendation}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Candidate Rules & Admin Approval Section */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <GitBranch className="w-4 h-4 text-purple-400" />
                  Candidate Rules Lifecycle & Governance
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Proposed adaptations require explicit human administrator approval before production deployment.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {candidates.map((c) => {
                const isApproved = c.status === 'APPROVED'
                const isCandidate = c.status === 'CANDIDATE'
                return (
                  <div
                    key={c.rule_id}
                    className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 space-y-3"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-slate-400">{c.rule_id}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full font-mono border ${
                            isApproved
                              ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                              : isCandidate
                              ? 'bg-purple-950 text-purple-300 border-purple-800'
                              : 'bg-rose-950 text-rose-300 border-rose-800'
                          }`}>
                            {c.status}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-white mt-1">{c.rule_name}</h4>
                      </div>
                      <span className="text-[10px] font-mono text-cyan-400 px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800">
                        {c.proposed_action}
                      </span>
                    </div>

                    <div className="text-xs text-slate-300 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 font-mono">
                      {c.condition_description}
                    </div>

                    <div className="text-xs text-slate-400">
                      <span className="font-semibold text-slate-300">Rationale: </span>
                      {c.rationale}
                    </div>

                    {isAdmin && isCandidate && (
                      <div className="pt-2 border-t border-slate-800 flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleRejectRule(c.rule_id)}
                          className="px-3 py-1 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800/80 text-xs font-semibold flex items-center gap-1 transition"
                        >
                          <X className="w-3.5 h-3.5" /> Reject
                        </button>
                        <button
                          onClick={() => handleApproveRule(c.rule_id)}
                          className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1 shadow-lg shadow-emerald-600/20 transition"
                        >
                          <Check className="w-3.5 h-3.5" /> Approve & Activate
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 3: FEDERATED SIMULATION ================= */}
      {activeTab === 'federated' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-6">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Lock className="w-5 h-5 text-indigo-400" />
                  Privacy-Preserving Federated Learning Simulation
                </h3>
                <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                  Simulates multi-institution collaborative model training across isolated synthetic banking entities (Institution A, B, and C).
                  Raw transaction records remain strictly within local institution boundaries; only aggregated parameter weights are exchanged via FedAvg.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5">
                  <span className="text-xs text-slate-400 font-mono">Rounds:</span>
                  <select
                    value={simRounds}
                    onChange={(e) => setSimRounds(Number(e.target.value))}
                    className="bg-transparent text-white text-xs font-bold font-mono focus:outline-none"
                  >
                    <option value={1} className="bg-slate-900 text-white">1 Round</option>
                    <option value={3} className="bg-slate-900 text-white">3 Rounds</option>
                    <option value={5} className="bg-slate-900 text-white">5 Rounds</option>
                  </select>
                </div>

                <button
                  onClick={handleRunSimulation}
                  disabled={simulating}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition disabled:opacity-50"
                >
                  <Zap className={`w-4 h-4 ${simulating ? 'animate-spin' : ''}`} />
                  {simulating ? 'Simulating FedAvg Aggregation...' : 'Run Federated Simulation'}
                </button>
              </div>
            </div>

            {/* Privacy Boundary Status */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                <div className="text-[10px] font-mono uppercase text-slate-400">Raw Data Shared</div>
                <div className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> 0 Rows (Blocked by Design)
                </div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                <div className="text-[10px] font-mono uppercase text-slate-400">Parameter Aggregator</div>
                <div className="text-sm font-bold text-indigo-300">
                  Federated Averaging (FedAvg)
                </div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                <div className="text-[10px] font-mono uppercase text-slate-400">Differential Privacy &epsilon;</div>
                <div className="text-sm font-bold text-purple-300 font-mono">
                  &epsilon; = 2.5 (Laplace Noise)
                </div>
              </div>
            </div>

            {/* Simulation Results if available */}
            {fedSimData && (
              <div className="space-y-6 pt-4 border-t border-slate-800">
                {/* Participating Institutions */}
                <div>
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                    Participating Synthetic Banking Entities ({fedSimData.participating_institutions?.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {fedSimData.participating_institutions?.map((inst) => (
                      <div key={inst.institution_id} className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[10px] text-indigo-400 font-bold">{inst.institution_id}</span>
                          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800/80">
                            ISOLATED
                          </span>
                        </div>
                        <div className="text-xs font-bold text-white">{inst.institution_name}</div>
                        <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300 pt-2 border-t border-slate-800/80">
                          <div>Samples: <span className="font-mono text-white">{inst.local_sample_count}</span></div>
                          <div>Fraud Rate: <span className="font-mono text-rose-400">{inst.local_fraud_rate_pct}%</span></div>
                          <div>PR-AUC: <span className="font-mono text-cyan-400">{inst.local_pr_auc}</span></div>
                          <div>Recall: <span className="font-mono text-indigo-400">{inst.local_recall}</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Global Candidate Model Comparison */}
                <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                        Global Candidate Model Metrics (FedAvg Benchmarked)
                      </h4>
                      <p className="text-[11px] text-slate-400">
                        Evaluated against standardized validation split across {fedSimData.global_candidate_metrics?.total_federated_samples} combined synthetic samples.
                      </p>
                    </div>
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-950 px-2.5 py-1 rounded-full border border-emerald-800">
                      Challenger Eligible
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                    <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                      <div className="text-[10px] uppercase font-mono text-slate-400">PR-AUC</div>
                      <div className="text-base font-bold text-indigo-400 font-mono">{fedSimData.global_candidate_metrics?.pr_auc}</div>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                      <div className="text-[10px] uppercase font-mono text-slate-400">Recall</div>
                      <div className="text-base font-bold text-emerald-400 font-mono">{fedSimData.global_candidate_metrics?.recall}</div>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                      <div className="text-[10px] uppercase font-mono text-slate-400">F1 Score</div>
                      <div className="text-base font-bold text-cyan-400 font-mono">{fedSimData.global_candidate_metrics?.f1_score}</div>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800">
                      <div className="text-[10px] uppercase font-mono text-slate-400">Optimal Threshold</div>
                      <div className="text-base font-bold text-purple-400 font-mono">{fedSimData.global_candidate_metrics?.optimal_threshold}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= TAB 4: MODEL COMPARISON MATRIX ================= */}
      {activeTab === 'comparison' && (
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                Champion vs Challengers Multi-Model Evaluation Matrix
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Comparative metrics at validation-optimized operating thresholds.
              </p>
            </div>

            {/* Imbalanced Fraud Metric Warning Box */}
            <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/40 text-xs text-amber-300 flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Metric Limitations on Imbalanced Financial Data: </span>
                Standard accuracy is severely deceptive on highly skewed fraud datasets (e.g. 99% accuracy can be achieved by predicting zero fraud).
                FraudLens optimizes primarily for <strong className="text-white">PR-AUC and Recall</strong> to maximize actual fraud dollar capture while constraining False Positive Rate.
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="p-3">Model Candidate</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-center">Optimal Threshold</th>
                    <th className="p-3 text-center">PR-AUC (Primary)</th>
                    <th className="p-3 text-center">Recall</th>
                    <th className="p-3 text-center">Precision</th>
                    <th className="p-3 text-center">F1 Score</th>
                    <th className="p-3 text-center">ROC-AUC</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {/* Active Champion */}
                  {comparisonData?.active_champion && (
                    <tr className="bg-indigo-950/20 hover:bg-indigo-950/30 transition">
                      <td className="p-3 font-bold text-white flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                        {comparisonData.active_champion.name} ({comparisonData.active_champion.version})
                      </td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded-full font-mono text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                          {comparisonData.active_champion.status}
                        </span>
                      </td>
                      <td className="p-3 text-center font-mono">{comparisonData.active_champion.optimal_threshold}</td>
                      <td className="p-3 text-center font-bold font-mono text-indigo-400">{comparisonData.active_champion.pr_auc}</td>
                      <td className="p-3 text-center font-bold font-mono text-emerald-400">{comparisonData.active_champion.recall}</td>
                      <td className="p-3 text-center font-mono">{comparisonData.active_champion.precision}</td>
                      <td className="p-3 text-center font-mono">{comparisonData.active_champion.f1_score}</td>
                      <td className="p-3 text-center font-mono">{comparisonData.active_champion.roc_auc}</td>
                    </tr>
                  )}

                  {/* Challengers */}
                  {comparisonData?.challengers?.map((c) => (
                    <tr key={c.name} className="hover:bg-slate-800/40 transition">
                      <td className="p-3 font-bold text-slate-200">
                        {c.name} ({c.version})
                      </td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded-full font-mono text-[10px] font-bold bg-purple-950 text-purple-300 border border-purple-800">
                          {c.status}
                        </span>
                      </td>
                      <td className="p-3 text-center font-mono">{c.optimal_threshold}</td>
                      <td className="p-3 text-center font-bold font-mono text-indigo-400">{c.pr_auc}</td>
                      <td className="p-3 text-center font-bold font-mono text-emerald-400">{c.recall}</td>
                      <td className="p-3 text-center font-mono">{c.precision}</td>
                      <td className="p-3 text-center font-mono">{c.f1_score}</td>
                      <td className="p-3 text-center font-mono">{c.roc_auc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Propose Rule Modal */}
      {newRuleModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Submit Candidate Rule Proposal
              </h3>
              <button onClick={() => setNewRuleModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 font-mono block mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  value={newRuleForm.rule_name}
                  onChange={(e) => setNewRuleForm({ ...newRuleForm, rule_name: e.target.value })}
                  placeholder="e.g. Unusual Channel Spike"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-mono block mb-1">Category</label>
                  <select
                    value={newRuleForm.category}
                    onChange={(e) => setNewRuleForm({ ...newRuleForm, category: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:border-indigo-500 focus:outline-none font-mono"
                  >
                    <option value="VELOCITY">VELOCITY</option>
                    <option value="AMOUNT_DEVIATION">AMOUNT_DEVIATION</option>
                    <option value="DEVICE_SECURITY">DEVICE_SECURITY</option>
                    <option value="GEOGRAPHIC">GEOGRAPHIC</option>
                    <option value="NETWORK_SYNDICATE">NETWORK_SYNDICATE</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 font-mono block mb-1">Proposed Action</label>
                  <select
                    value={newRuleForm.proposed_action}
                    onChange={(e) => setNewRuleForm({ ...newRuleForm, proposed_action: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:border-indigo-500 focus:outline-none font-mono"
                  >
                    <option value="FLAG_REVIEW">FLAG_REVIEW</option>
                    <option value="BLOCK">BLOCK</option>
                    <option value="STEP_UP_AUTH">STEP_UP_AUTH</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-mono block mb-1">Condition Description</label>
                <input
                  type="text"
                  required
                  value={newRuleForm.condition_description}
                  onChange={(e) => setNewRuleForm({ ...newRuleForm, condition_description: e.target.value })}
                  placeholder="e.g. Velocity_1h >= 4 AND Is_New_Device == True"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 font-mono block mb-1">Security Rationale</label>
                <textarea
                  rows={2}
                  required
                  value={newRuleForm.rationale}
                  onChange={(e) => setNewRuleForm({ ...newRuleForm, rationale: e.target.value })}
                  placeholder="Explain why this rule is needed..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setNewRuleModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold"
                >
                  Submit Proposal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
