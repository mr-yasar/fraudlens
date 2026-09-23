import React, { useState, useEffect, useCallback } from 'react'
import {
  Share2,
  Users,
  Smartphone,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Activity,
  Zap,
  RefreshCw,
  Search,
  ChevronRight,
  Database,
  Lock,
  Layers,
  Clock,
  MapPin,
  Laptop,
  CheckCircle2,
  Info
} from 'lucide-react'
import { intelligenceApi, networkApi, customersApi } from '../services/api'

export default function FraudIntelligenceView({ setActiveView, onSelectTransaction }) {
  const [selectedCustomerId, setSelectedCustomerId] = useState('CUST-DEMO-001')
  const [customerList, setCustomerList] = useState([])
  const [behaviorReport, setBehaviorReport] = useState(null)
  const [deviceAssessment, setDeviceAssessment] = useState(null)
  const [networkGraph, setNetworkGraph] = useState(null)
  const [networkClusters, setNetworkClusters] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('graph') // 'graph' | 'behavior' | 'device' | 'clusters'
  const [selectedNode, setSelectedNode] = useState(null)

  // Fetch customer list on mount
  useEffect(() => {
    async function loadCustomers() {
      try {
        const data = await customersApi.getCustomers(1, 20)
        if (data && data.customers && data.customers.length > 0) {
          setCustomerList(data.customers)
          setSelectedCustomerId(data.customers[0].customer_id)
        }
      } catch (err) {
        console.warn('Failed to load customers for intelligence selector:', err)
      }
    }
    loadCustomers()
  }, [])

  // Load intelligence data for selected customer
  const fetchIntelligenceData = useCallback(async (custId) => {
    if (!custId) return
    setLoading(true)
    setError(null)
    setSelectedNode(null)
    try {
      const [behData, devData, graphData, clusterData] = await Promise.all([
        intelligenceApi.getCustomerBehavior(custId, 150.0).catch(() => null),
        intelligenceApi.assessDeviceRisk(custId, 'web', 0).catch(() => null),
        networkApi.getRelationshipGraph(custId, 2).catch(() => null),
        networkApi.getNetworkClusters().catch(() => null),
      ])

      setBehaviorReport(behData)
      setDeviceAssessment(devData)
      setNetworkGraph(graphData)
      setNetworkClusters(clusterData)
    } catch (err) {
      console.error('Error fetching intelligence fabric data:', err)
      setError(err.message || 'Failed to load intelligence telemetry')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedCustomerId) {
      fetchIntelligenceData(selectedCustomerId)
    }
  }, [selectedCustomerId, fetchIntelligenceData])

  // Helper for node colors
  const getNodeColor = (type, risk) => {
    if (risk === 'HIGH' || risk === 'CRITICAL') return '#ef4444' // red-500
    if (risk === 'MEDIUM') return '#f59e0b' // amber-500
    if (type === 'customer') return '#3b82f6' // blue-500
    if (type === 'device') return '#8b5cf6' // purple-500
    if (type === 'merchant') return '#10b981' // emerald-500
    if (type === 'investigation') return '#ec4899' // pink-500
    return '#6b7280'
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl shadow-xl">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 rounded-xl text-indigo-400 shadow-inner">
            <Share2 className="w-8 h-8 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-white tracking-tight">Fraud Intelligence Fabric</h1>
              <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 rounded-full">
                Layer 2 Active
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Continuous behavioral baselines, hardware telemetry & multi-hop relationship graph intelligence.
            </p>
          </div>
        </div>

        {/* Customer Selector & Refresh */}
        <div className="flex items-center gap-3">
          <div className="relative min-w-[200px]">
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value)}
              className="w-full bg-slate-800/90 text-slate-200 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {customerList.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.name || c.customer_id} ({c.customer_id})
                </option>
              ))}
              {!customerList.some(c => c.customer_id === selectedCustomerId) && (
                <option value={selectedCustomerId}>{selectedCustomerId}</option>
              )}
            </select>
          </div>

          <button
            onClick={() => fetchIntelligenceData(selectedCustomerId)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600/80 hover:bg-indigo-600 text-white text-sm font-medium rounded-xl border border-indigo-500/50 shadow-md transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Sync
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-2 pb-1">
        {[
          { id: 'graph', label: 'Relationship Graph', icon: Share2 },
          { id: 'behavior', label: 'Continuous Behavior', icon: Activity },
          { id: 'device', label: 'Device & Session Trust', icon: Smartphone },
          { id: 'clusters', label: 'Syndicate Clusters', icon: Layers },
        ].map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="flex flex-col items-center justify-center p-16 bg-slate-900/40 border border-slate-800/80 rounded-2xl">
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
          <p className="text-sm text-slate-400">Synthesizing intelligence telemetry & relationship graph...</p>
        </div>
      )}

      {error && !loading && (
        <div className="p-4 bg-red-900/20 border border-red-500/40 rounded-xl text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => fetchIntelligenceData(selectedCustomerId)} className="underline hover:text-red-200">
            Retry
          </button>
        </div>
      )}

      {/* TAB 1: RELATIONSHIP GRAPH VISUALIZER */}
      {activeTab === 'graph' && !loading && networkGraph && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Visual Graph Canvas */}
          <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 relative overflow-hidden shadow-2xl min-h-[480px]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-white">Interactive Entity Topology</h3>
                <p className="text-xs text-slate-400">Centered on customer {selectedCustomerId} (Depth: 2 hops)</p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 text-blue-400"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" /> Customer</span>
                <span className="flex items-center gap-1.5 text-purple-400"><span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block" /> Device</span>
                <span className="flex items-center gap-1.5 text-emerald-400"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Merchant</span>
                <span className="flex items-center gap-1.5 text-red-400"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" /> High Risk</span>
              </div>
            </div>

            {/* SVG Relationship Graph */}
            <div className="w-full h-[400px] border border-slate-800/70 rounded-xl bg-slate-950/70 relative flex items-center justify-center p-4">
              <svg className="w-full h-full" viewBox="0 0 600 360">
                {/* Center Coordinates */}
                {/* Render Edges */}
                {networkGraph.edges.map((edge, idx) => {
                  const angle = (idx / Math.max(1, networkGraph.edges.length)) * 2 * Math.PI
                  const targetX = 300 + Math.cos(angle) * 140
                  const targetY = 180 + Math.sin(angle) * 110
                  return (
                    <g key={edge.id || idx}>
                      <line
                        x1="300"
                        y1="180"
                        x2={targetX}
                        y2={targetY}
                        stroke={edge.is_suspicious ? '#ef4444' : '#475569'}
                        strokeWidth={edge.is_suspicious ? '2.5' : '1.5'}
                        strokeDasharray={edge.is_suspicious ? '4,4' : 'none'}
                        className="transition-all duration-300 opacity-70"
                      />
                    </g>
                  )
                })}

                {/* Render Outer Nodes */}
                {networkGraph.nodes.filter(n => !n.metadata?.is_root).map((node, idx) => {
                  const total = networkGraph.nodes.length - 1
                  const angle = (idx / Math.max(1, total)) * 2 * Math.PI
                  const cx = 300 + Math.cos(angle) * 140
                  const cy = 180 + Math.sin(angle) * 110
                  const isSelected = selectedNode?.id === node.id
                  const nodeColor = getNodeColor(node.node_type, node.risk_level)

                  return (
                    <g
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className="cursor-pointer transition-transform hover:scale-110"
                    >
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isSelected ? "18" : "14"}
                        fill="#0f172a"
                        stroke={nodeColor}
                        strokeWidth={isSelected ? "3.5" : "2"}
                        className="drop-shadow-lg"
                      />
                      <text
                        x={cx}
                        y={cy + 26}
                        textAnchor="middle"
                        fill="#94a3b8"
                        fontSize="10"
                        className="font-mono select-none"
                      >
                        {node.label.length > 14 ? node.label.substring(0, 12) + '..' : node.label}
                      </text>
                    </g>
                  )
                })}

                {/* Central Root Node (Customer) */}
                <g onClick={() => setSelectedNode(networkGraph.nodes.find(n => n.metadata?.is_root) || null)} className="cursor-pointer">
                  <circle cx="300" cy="180" r="24" fill="#1e1b4b" stroke="#6366f1" strokeWidth="3" className="animate-pulse drop-shadow-xl" />
                  <text x="300" y="185" textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="bold" className="select-none">
                    ROOT
                  </text>
                </g>
              </svg>
            </div>
          </div>

          {/* Node Inspector & Network Evidence */}
          <div className="space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                <Info className="w-4 h-4 text-indigo-400" />
                Entity Details Inspector
              </h3>

              {selectedNode ? (
                <div className="space-y-4">
                  <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-indigo-400 uppercase">{selectedNode.node_type}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                        selectedNode.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-300 border border-red-500/40' :
                        selectedNode.risk_level === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                        'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      }`}>
                        {selectedNode.risk_level}
                      </span>
                    </div>
                    <p className="text-base font-bold text-white">{selectedNode.label}</p>
                    <p className="text-xs text-slate-400 mt-1 font-mono">ID: {selectedNode.id}</p>
                  </div>

                  {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                    <div className="space-y-1.5 text-xs text-slate-300 bg-slate-950/40 p-3 rounded-lg border border-slate-800/60">
                      {Object.entries(selectedNode.metadata).map(([k, v]) => (
                        <div key={k} className="flex justify-between py-0.5 border-b border-slate-800/40 last:border-0">
                          <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}:</span>
                          <span className="font-mono text-slate-200">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                  Click any node in the relationship canvas to inspect hardware, linked transactions, and risk flags.
                </div>
              )}
            </div>

            {/* Network Risk Summary */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center justify-between">
                <span>Multi-Hop Network Risk</span>
                <span className="text-indigo-400 font-mono text-xs">{networkGraph.total_nodes} nodes linked</span>
              </h3>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                  <span className="text-xs text-slate-400">Total Entities</span>
                  <p className="text-xl font-bold text-white mt-0.5">{networkGraph.total_nodes}</p>
                </div>
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                  <span className="text-xs text-slate-400">Active Edges</span>
                  <p className="text-xl font-bold text-indigo-400 mt-0.5">{networkGraph.total_edges}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CONTINUOUS BEHAVIOR INTELLIGENCE */}
      {activeTab === 'behavior' && !loading && behaviorReport && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Baseline Summary Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-400" />
                Customer Baseline
              </h3>
              <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${
                behaviorReport.confidence_level === 'HIGH' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
                behaviorReport.confidence_level === 'MEDIUM' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40' :
                'bg-amber-500/20 text-amber-300 border border-amber-500/40'
              }`}>
                {behaviorReport.confidence_level} CONFIDENCE
              </span>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between py-1.5 border-b border-slate-800 text-sm">
                <span className="text-slate-400">Historical Avg Amount:</span>
                <span className="font-bold text-white font-mono">${behaviorReport.historical_avg_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800 text-sm">
                <span className="text-slate-400">Median Amount:</span>
                <span className="font-mono text-slate-200">${behaviorReport.historical_median_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800 text-sm">
                <span className="text-slate-400">Historical Max:</span>
                <span className="font-mono text-slate-200">${behaviorReport.historical_max_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800 text-sm">
                <span className="text-slate-400">Account Tenure:</span>
                <span className="text-slate-200">{behaviorReport.account_age_days} days</span>
              </div>
              <div className="flex justify-between py-1.5 text-sm">
                <span className="text-slate-400">Total Transactions:</span>
                <span className="font-bold text-indigo-400">{behaviorReport.total_historical_transactions}</span>
              </div>
            </div>
          </div>

          {/* Velocity Matrix */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              Rolling Velocity Telemetry
            </h3>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-center">
                <span className="text-xs text-slate-400">5-Min Burst</span>
                <p className="text-2xl font-bold text-white mt-1">{behaviorReport.velocity_5m}</p>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-center">
                <span className="text-xs text-slate-400">15-Min Velocity</span>
                <p className="text-2xl font-bold text-white mt-1">{behaviorReport.velocity_15m}</p>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-center">
                <span className="text-xs text-slate-400">1-Hour Velocity</span>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{behaviorReport.velocity_1h}</p>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-center">
                <span className="text-xs text-slate-400">24-Hour Velocity</span>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{behaviorReport.velocity_24h}</p>
              </div>
            </div>

            <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-xl flex items-center justify-between text-xs text-slate-300">
              <span>Failed Attempts in Session:</span>
              <span className={`font-bold font-mono ${behaviorReport.failed_attempts_count > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {behaviorReport.failed_attempts_count}
              </span>
            </div>
          </div>

          {/* Behavior Deviation Score & Diagnostic Evidence */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-white flex items-center justify-between">
              <span>Deviation Score</span>
              <span className={`text-lg font-mono font-bold ${
                behaviorReport.behaviour_risk_level === 'HIGH' ? 'text-red-400' :
                behaviorReport.behaviour_risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {behaviorReport.behaviour_deviation_score.toFixed(1)}/100
              </span>
            </h3>

            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  behaviorReport.behaviour_deviation_score >= 70 ? 'bg-red-500' :
                  behaviorReport.behaviour_deviation_score >= 35 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${behaviorReport.behaviour_deviation_score}%` }}
              />
            </div>

            <div className="space-y-2 mt-4">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Diagnostic Evidence:</span>
              {behaviorReport.evidence && behaviorReport.evidence.length > 0 ? (
                behaviorReport.evidence.map((ev, i) => (
                  <div key={i} className="text-xs p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-lg text-slate-300 flex items-start gap-2">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>{ev}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-950/40 rounded-lg border border-slate-800">
                  Transaction aligns closely with historical behavioral norms.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: DEVICE & SESSION INTELLIGENCE */}
      {activeTab === 'device' && !loading && deviceAssessment && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Smartphone className="w-5 h-5 text-purple-400" />
              Hardware Telemetry & Fingerprint
            </h3>

            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Anonymized Device ID:</span>
                <span className="font-mono text-purple-300">{deviceAssessment.device_fingerprint}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Device Platform:</span>
                <span className="text-white capitalize">{deviceAssessment.device_type}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Device Novelty:</span>
                <span className={deviceAssessment.is_novel_device ? 'text-amber-400 font-semibold' : 'text-emerald-400'}>
                  {deviceAssessment.is_novel_device ? 'NOVEL / UNSEEN' : 'RECOGNIZED'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Spoofed / Anonymized:</span>
                <span className={deviceAssessment.is_spoofed_environment ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                  {deviceAssessment.is_spoofed_environment ? 'SPOOFED (PROXY/TOR)' : 'CLEAN'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-xs text-slate-400">Device Risk Score</span>
                <p className="text-xl font-bold text-purple-400 mt-1">{deviceAssessment.device_risk_score.toFixed(0)}/100</p>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-xs text-slate-400">Session Risk Score</span>
                <p className="text-xl font-bold text-amber-400 mt-1">{deviceAssessment.session_risk_score.toFixed(0)}/100</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-400" />
              Session Telemetry
            </h3>

            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Active Session ID:</span>
                <span className="font-mono text-slate-300">{deviceAssessment.session_id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Estimated Session Age:</span>
                <span className="text-white">{deviceAssessment.session_age_minutes} minutes</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Session Transaction Count:</span>
                <span className="font-bold text-indigo-400">{deviceAssessment.session_transaction_count} attempts</span>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Device Evidence:</span>
              {deviceAssessment.evidence && deviceAssessment.evidence.length > 0 ? (
                deviceAssessment.evidence.map((ev, i) => (
                  <div key={i} className="text-xs p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-lg text-slate-300 flex items-start gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <span>{ev}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-950/40 rounded-lg border border-slate-800">
                  Zero hardware spoofing or novel device anomalies detected.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: SYNDICATE CLUSTERS */}
      {activeTab === 'clusters' && !loading && networkClusters && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Monitored Entity Population</span>
              <p className="text-3xl font-bold text-white mt-1">{networkClusters.total_monitored_entities}</p>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Shared Hardware Clusters</span>
              <p className="text-3xl font-bold text-purple-400 mt-1">{networkClusters.shared_hardware_clusters_count}</p>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <span className="text-xs font-semibold text-slate-400 uppercase">Active Investigation Cases</span>
              <p className="text-3xl font-bold text-red-400 mt-1">{networkClusters.active_investigation_cases}</p>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <h3 className="text-base font-bold text-white mb-4">Multi-Account Shared Device Rings</h3>
            {networkClusters.shared_hardware_clusters && networkClusters.shared_hardware_clusters.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 text-xs uppercase font-mono border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Hardware Profile / Channel</th>
                      <th className="py-3 px-4">Linked Customer Accounts</th>
                      <th className="py-3 px-4">Syndicate Risk Level</th>
                      <th className="py-3 px-4">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {networkClusters.shared_hardware_clusters.map((cluster, i) => (
                      <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4 font-mono text-purple-300">{cluster.device_type}</td>
                        <td className="py-3.5 px-4 font-bold text-white">{cluster.linked_customers_count} accounts</td>
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                            cluster.risk_tier === 'HIGH' ? 'bg-red-500/20 text-red-300 border border-red-500/40' :
                            'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          }`}>
                            {cluster.risk_tier}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <button
                            onClick={() => {
                              setActiveTab('graph')
                            }}
                            className="text-xs font-medium text-indigo-400 hover:text-indigo-300 underline"
                          >
                            Explore Subgraph →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No multi-account device rings currently detected.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
