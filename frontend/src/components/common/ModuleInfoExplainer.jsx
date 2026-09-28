import React, { useState, useEffect, useRef } from 'react'
import {
  X,
  Sparkles,
  ShieldCheck,
  ChevronRight,
  Zap,
} from 'lucide-react'

// Ultra-Concise, Simple-English Module Intelligence (5-6 short, scannable lines, NO numbered lists)
const MODULE_INTEL = {
  dashboard: {
    title: 'Executive Overview',
    badge: 'LIVE TELEMETRY',
    accent: '#06b6d4',
    features: ['Real-Time Telemetry', 'Trust Score AI', 'Instant Alerts'],
    description: [
      'Your central financial command center.',
      'Monitors account safety and live trust scores 24/7.',
      'Shows all active hardware devices and private sessions.',
      'Detects spending surges and unusual location changes instantly.',
      'Gives you one-click access to all security tools.',
    ],
  },
  analyzer: {
    title: 'Risk Analyzer & SHAP',
    badge: 'AI ML INFERENCE',
    accent: '#8b5cf6',
    features: ['Sub-ms Scoring', 'TreeSHAP Math', 'Multi-Factor'],
    description: [
      'Test and score any payment for fraud in real time.',
      'Simulates how our AI thinks before approving a transaction.',
      'Compares payments against your personal spending baseline.',
      'Produces a clear 0 to 100 risk score with instant status.',
      'Interactive SHAP charts explain the exact math behind decisions.',
    ],
  },
  'executive-transactions': {
    title: 'Transactions & Scenarios',
    badge: 'ADAPTIVE ENGINE',
    accent: '#6366f1',
    features: ['1-Click Scenarios', 'OTP Step-Up', 'Encrypted Ledger'],
    description: [
      'Live execution arena for testing high-value transactions.',
      'Run realistic test scenarios with a single click.',
      'Watch the AI trigger cryptographic step-up challenges.',
      'All payments are sealed into your private encrypted ledger.',
      'Guarantees zero data leakage with total privacy.',
    ],
  },
  'premium-transactions': {
    title: 'Transactions & Scenarios',
    badge: 'ADAPTIVE ENGINE',
    accent: '#6366f1',
    features: ['1-Click Scenarios', 'OTP Step-Up', 'Encrypted Ledger'],
    description: [
      'Live execution arena for testing high-value transactions.',
      'Run realistic test scenarios with a single click.',
      'Watch the AI trigger cryptographic step-up challenges.',
      'All payments are sealed into your private encrypted ledger.',
      'Guarantees zero data leakage with total privacy.',
    ],
  },
  transactions: {
    title: 'Transaction History',
    badge: 'SECURE LEDGER',
    accent: '#10b981',
    features: ['1,500+ Records', 'Deep Filter', 'Instant Search'],
    description: [
      'Your complete financial record safely stored in the database.',
      'Browse through all 1,500+ verified historical transactions.',
      'Search and filter by risk level, merchant, or amount.',
      'Click any transaction to inspect timestamps and fraud scores.',
      'Trains and refines your personalized AI spending baseline.',
    ],
  },
  'security-center': {
    title: 'Security Center',
    badge: 'ENCLAVE DEFENSE',
    accent: '#06b6d4',
    features: ['Hardware Keys', 'Step-Up Armed', 'Lockdown Shield'],
    description: [
      'Your personal cybersecurity headquarters.',
      'Monitors multi-factor defense and hardware encryption keys.',
      'Verifies that cryptographic challenges are actively armed.',
      'Trigger instant account lockdown if you suspect threat activity.',
      'Bank-grade protection running silently around the clock.',
    ],
  },
  'premium-security-center': {
    title: 'Security Center',
    badge: 'ENCLAVE DEFENSE',
    accent: '#06b6d4',
    features: ['Hardware Keys', 'Step-Up Armed', 'Lockdown Shield'],
    description: [
      'Your personal cybersecurity headquarters.',
      'Monitors multi-factor defense and hardware encryption keys.',
      'Verifies that cryptographic challenges are actively armed.',
      'Trigger instant account lockdown if you suspect threat activity.',
      'Bank-grade protection running silently around the clock.',
    ],
  },
  'fleet-security': {
    title: 'Fleet & Device Security',
    badge: 'BIOMETRIC TRUST',
    accent: '#3b82f6',
    features: ['Passkey Binding', 'Zero-Delay Revoke', 'Session Kill'],
    description: [
      'Total control over all your authorized hardware devices.',
      'View trusted laptops, smartphones, and biometric passkeys.',
      'Trust new verified devices with one-click hardware binding.',
      'Instantly revoke lost devices and terminate remote sessions.',
      'Stops account takeovers even if your password is stolen.',
    ],
  },
  payment: {
    title: 'Payment Gateway',
    badge: 'QUANTUM RAILS',
    accent: '#0ea5e9',
    features: ['Pre-Auth AI', 'Instant Approval', 'Step-Up OTP'],
    description: [
      'Interactive point-of-sale checkout gateway.',
      'Pre-scores every payment in sub-milliseconds with zero lag.',
      'Routine safe purchases are approved instantly with zero friction.',
      'High-risk transfers trigger an elegant verification challenge.',
      'Full protection and peace of mind during online purchases.',
    ],
  },
  'live-monitor': {
    title: 'Live Radar & Cases',
    badge: 'GEOSPATIAL RADAR',
    accent: '#f59e0b',
    features: ['3D Global Radar', 'Threat Beacons', 'Case Forensics'],
    description: [
      'Global radar tracking real-time payment traffic across the globe.',
      'High-risk spikes and cross-border attempts flash instantly.',
      'Open full forensic investigation cases on flagged activities.',
      'Compare normal patterns against botnet and proxy attacks.',
      'Gives fraud analysts complete operational command.',
    ],
  },
  investigations: {
    title: 'Investigation Hub',
    badge: 'FORENSIC CASES',
    accent: '#f97316',
    features: ['Case Workflow', 'Forensic Hashes', 'Audit Notes'],
    description: [
      'Active workbench for investigating flagged fraud cases.',
      'Inspect detailed device hashes, IP subnets, and geo hops.',
      'Transition case status from Open to Resolved or False Alarm.',
      'Helps teams stop coordinated attacks methodically and fast.',
      'Produces full compliance logs for banking and audit teams.',
    ],
  },
  'security-alerts': {
    title: 'Security Alerts',
    badge: 'INCIDENT RESPONSE',
    accent: '#ef4444',
    features: ['Severity Ranked', '1-Click Resolve', 'Live Push'],
    description: [
      'Early warning system for critical security events.',
      'Highlights unauthorized logins, velocity spikes, and anomalies.',
      'Clear explanations tell you exactly why each alert fired.',
      'Acknowledge alerts and jump directly into linked transactions.',
      'Protects your account before any financial damage occurs.',
    ],
  },
  'audit-trail': {
    title: 'Compliance Audit Trail',
    badge: 'IMMUTABLE LOGS',
    accent: '#10b981',
    features: ['SHA-256 Sealed', 'Non-Repudiation', 'ISO 27001'],
    description: [
      'Tamper-proof permanent record of all account actions.',
      'Every login, payment, and security change is timestamped.',
      'Secured by SHA-256 cryptographic hashes for non-repudiation.',
      'Meets international banking compliance and audit standards.',
      'Guarantees full transparency and verifiable legal safety.',
    ],
  },
  'audit-logs': {
    title: 'Compliance Audit Trail',
    badge: 'IMMUTABLE LOGS',
    accent: '#10b981',
    features: ['SHA-256 Sealed', 'Non-Repudiation', 'ISO 27001'],
    description: [
      'Tamper-proof permanent record of all account actions.',
      'Every login, payment, and security change is timestamped.',
      'Secured by SHA-256 cryptographic hashes for non-repudiation.',
      'Meets international banking compliance and audit standards.',
      'Guarantees full transparency and verifiable legal safety.',
    ],
  },
  'ai-copilot': {
    title: 'AI Security Assistant',
    badge: 'FINTECH AGENT',
    accent: '#a855f7',
    features: ['Voice Explainer', 'Risk Breakdown', 'Reasoning AI'],
    description: [
      'Your personal AI assistant specialized in fraud defense.',
      'Ask any question in plain English about payments and security.',
      'Explains complex risk signals and merchant anomalies clearly.',
      'Features natural voice audio synthesis for hands-free insights.',
      'Provides smart recommendations to strengthen your account.',
    ],
  },
  merchants: {
    title: 'Merchant Intelligence',
    badge: 'COMMERCE INTEL',
    accent: '#06b6d4',
    features: ['30 Profiles', 'MCC Fraud Rates', 'Network Intel'],
    description: [
      'Inspect 30 verified merchants across retail, travel, and bullion.',
      'Check historical fraud rates, ticket averages, and MCC risk.',
      'Understand how merchant category influences fraud risk scores.',
      'Protects you from fraudulent storefronts and shady billing.',
      'Complete visibility into who you are transacting with.',
    ],
  },
  'explainable-ai': {
    title: 'Explainable AI & SHAP',
    badge: 'INTERPRETABILITY',
    accent: '#ec4899',
    features: ['Game Theory', 'Global Weights', 'Zero Black-Box'],
    description: [
      'Reveals exactly how machine learning models make decisions.',
      'Eliminates black-box mysteries using game-theoretic SHAP math.',
      'Shows which features have the strongest impact on fraud detection.',
      'Dissects false positives to keep AI decisions fair and transparent.',
      'The gold standard for trustworthy, compliant financial AI.',
    ],
  },
  'model-lab': {
    title: 'Model Lab & Registry',
    badge: 'ML GOVERNANCE',
    accent: '#3b82f6',
    features: ['ROC-AUC Curves', 'LightGBM / XGB', 'Latency Bench'],
    description: [
      'Benchmarks and manages machine learning model versions.',
      'Compare LightGBM, XGBoost, and CatBoost detection models.',
      'Inspect ROC-AUC curves, precision-recall, and sub-ms latency.',
      'Safely promote newly trained models to active production.',
      'Ensures your fraud defense engine is always cutting-edge.',
    ],
  },
  'dataset-health': {
    title: 'Dataset Health',
    badge: 'DATA INTEGRITY',
    accent: '#14b8a6',
    features: ['Zero Data Leak', '55 Columns', '0.2% Purity'],
    description: [
      'Monitors the cleanliness and integrity of training records.',
      'Verifies zero data leakage between customer partitions.',
      'Confirms dataset maintains pure 0.2% anomaly calibration.',
      'Audits schema compliance across all 55 mathematical features.',
      'Clean data ensures reliable, razor-sharp predictions.',
    ],
  },
  settings: {
    title: 'Platform Settings',
    badge: 'CONFIG MATRIX',
    accent: '#64748b',
    features: ['Custom Thresholds', 'Alert Webhooks', 'Audio Theme'],
    description: [
      'Customize platform thresholds and notification preferences.',
      'Adjust sensitivity levels for automated step-up challenges.',
      'Configure webhook integrations and export audit snapshots.',
      'Toggle audio synthesizer volume, themes, and display formats.',
      'Tailor your FraudLens AI experience exactly to your workflow.',
    ],
  },
}

// Aliases for sub-views and routes
MODULE_INTEL['premium-devices'] = MODULE_INTEL['fleet-security']
MODULE_INTEL['premium-sessions'] = MODULE_INTEL['fleet-security']
MODULE_INTEL['premium-alerts'] = MODULE_INTEL['security-alerts']
MODULE_INTEL['premium-audit'] = MODULE_INTEL['audit-trail']
MODULE_INTEL['admin-models'] = MODULE_INTEL['model-lab']
MODULE_INTEL['admin-dataset'] = MODULE_INTEL['dataset-health']
MODULE_INTEL['admin-ml'] = MODULE_INTEL['model-lab']

export default function ModuleInfoExplainer({
  activeView = 'dashboard',
  isOpenExternal = false,
  onOpenChange = null,
  showFloatingButton = true,
}) {
  const [isOpenInternal, setIsOpenInternal] = useState(false)
  const isControlled = typeof onOpenChange === 'function'
  const isActuallyOpen = isControlled ? isOpenExternal : isOpenInternal

  const [isRendered, setIsRendered] = useState(false)
  const [isAnimatingIn, setIsAnimatingIn] = useState(false)
  const canvasRef = useRef(null)
  const animFrameRef = useRef(null)

  const intel = MODULE_INTEL[activeView] || MODULE_INTEL.dashboard

  useEffect(() => {
    if (isOpenExternal && !isRendered) {
      handleOpen()
    } else if (!isOpenExternal && isControlled && isRendered) {
      handleClose()
    }
  }, [isOpenExternal])

  const handleOpen = () => {
    if (isControlled) {
      onOpenChange(true)
    } else {
      setIsOpenInternal(true)
    }
    setIsRendered(true)
    requestAnimationFrame(() => {
      setIsAnimatingIn(true)
    })
  }

  const handleClose = () => {
    setIsAnimatingIn(false)
    if (isControlled) {
      onOpenChange(false)
    } else {
      setIsOpenInternal(false)
    }
    setTimeout(() => {
      setIsRendered(false)
    }, 280)
  }

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isRendered) {
        handleClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isRendered])

  // High-Fidelity Futuristic Canvas Visual Engine (60 FPS)
  useEffect(() => {
    if (!isRendered || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let width = (canvas.width = canvas.offsetWidth * 2 || 900)
    let height = (canvas.height = canvas.offsetHeight * 2 || 400)

    const handleResize = () => {
      if (!canvas) return
      width = canvas.width = canvas.offsetWidth * 2 || 900
      height = canvas.height = canvas.offsetHeight * 2 || 400
    }
    window.addEventListener('resize', handleResize)

    let t = 0

    const renderScene = () => {
      t += 0.02
      ctx.clearRect(0, 0, width, height)

      // Rich Deep Space Charcoal-Navy Background
      const bgGrad = ctx.createRadialGradient(
        width / 2,
        height / 2,
        20,
        width / 2,
        height / 2,
        width * 0.65
      )
      bgGrad.addColorStop(0, '#101726')
      bgGrad.addColorStop(0.6, '#0b0f19')
      bgGrad.addColorStop(1, '#06080e')
      ctx.fillStyle = bgGrad
      ctx.fillRect(0, 0, width, height)

      // Module-Specific Visual Graphic
      switch (activeView) {
        case 'dashboard': {
          // 3D Concentric Orbiting Telemetry & Radar Earth Core
          const cx = width / 2
          const cy = height * 0.52
          const maxR = Math.min(width, height) * 0.44

          // Glowing concentric holographic rings with 3D tilt
          for (let r = 35; r <= maxR; r += 28) {
            ctx.beginPath()
            ctx.ellipse(cx, cy, r * 1.3, r * 0.65, 0, 0, Math.PI * 2)
            ctx.strokeStyle = `rgba(6, 182, 212, ${0.25 - (r / maxR) * 0.15})`
            ctx.lineWidth = 1.5
            ctx.setLineDash([4, 6])
            ctx.stroke()
            ctx.setLineDash([])
          }

          // 360-Degree Sweeping Holographic Radar Beam
          const sweep = t * 1.5
          const sweepGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR * 1.2)
          sweepGrad.addColorStop(0, 'rgba(6, 182, 212, 0.45)')
          sweepGrad.addColorStop(0.5, 'rgba(14, 165, 233, 0.15)')
          sweepGrad.addColorStop(1, 'rgba(6, 182, 212, 0)')
          ctx.beginPath()
          ctx.moveTo(cx, cy)
          ctx.arc(cx, cy, maxR * 1.2, sweep, sweep + 0.55)
          ctx.closePath()
          ctx.fillStyle = sweepGrad
          ctx.fill()

          // Center Glowing AI Core
          ctx.beginPath()
          ctx.arc(cx, cy, 18 + Math.sin(t * 3) * 3, 0, Math.PI * 2)
          ctx.fillStyle = '#06b6d4'
          ctx.shadowColor = '#38bdf8'
          ctx.shadowBlur = 25
          ctx.fill()
          ctx.shadowBlur = 0

          // Orbiting Telemetry Beacons
          for (let i = 0; i < 4; i++) {
            const angle = t * 0.7 + (i * Math.PI) / 2
            const rx = cx + Math.cos(angle) * (maxR * 0.8)
            const ry = cy + Math.sin(angle) * (maxR * 0.42)
            ctx.beginPath()
            ctx.arc(rx, ry, 5, 0, Math.PI * 2)
            ctx.fillStyle = '#38bdf8'
            ctx.shadowColor = '#38bdf8'
            ctx.shadowBlur = 15
            ctx.fill()
            ctx.shadowBlur = 0

            // Pulse ring
            const ping = (t * 2 + i) % 1
            ctx.beginPath()
            ctx.arc(rx, ry, 5 + ping * 18, 0, Math.PI * 2)
            ctx.strokeStyle = `rgba(56, 189, 248, ${1 - ping})`
            ctx.lineWidth = 1.5
            ctx.stroke()
          }
          break
        }

        case 'analyzer': {
          // Glowing Synaptic Network & Dynamic TreeSHAP Attribution Vectors
          const cx = width / 2
          const cy = height * 0.5
          const numNodes = 10
          const nodes = []

          for (let i = 0; i < numNodes; i++) {
            const a = (i / numNodes) * Math.PI * 2 + t * 0.3
            const dist = 65 + (i % 3) * 45
            nodes.push({
              x: cx + Math.cos(a) * dist * 1.2,
              y: cy + Math.sin(a) * dist * 0.7,
              color: i % 2 === 0 ? '#8b5cf6' : '#06b6d4',
            })
          }

          // Neural connection lines with laser pulses
          ctx.lineWidth = 1.8
          for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
              if (Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y) < 140) {
                ctx.beginPath()
                ctx.moveTo(nodes[i].x, nodes[i].y)
                ctx.lineTo(nodes[j].x, nodes[j].y)
                ctx.strokeStyle = 'rgba(139, 92, 246, 0.22)'
                ctx.stroke()

                // Fast synaptic spark
                const progress = (t * 1.5 + (i + j) * 0.15) % 1
                const px = nodes[i].x + (nodes[j].x - nodes[i].x) * progress
                const py = nodes[i].y + (nodes[j].y - nodes[i].y) * progress
                ctx.beginPath()
                ctx.arc(px, py, 2.5, 0, Math.PI * 2)
                ctx.fillStyle = '#e879f9'
                ctx.fill()
              }
            }
          }

          // Center Brain AI Processor Chip
          ctx.save()
          ctx.translate(cx, cy)
          ctx.rotate(t * 0.4)
          ctx.strokeStyle = '#c084fc'
          ctx.lineWidth = 2
          ctx.shadowColor = '#c084fc'
          ctx.shadowBlur = 18
          ctx.strokeRect(-20, -20, 40, 40)
          ctx.fillStyle = 'rgba(139, 92, 246, 0.35)'
          ctx.fillRect(-20, -20, 40, 40)
          ctx.restore()
          ctx.shadowBlur = 0

          // Floating TreeSHAP Attribution Bars
          for (let b = 0; b < 4; b++) {
            const barY = cy - 40 + b * 26
            const barW = 40 + Math.sin(t * 2 + b) * 25
            const isRed = b % 2 === 0
            const grad = ctx.createLinearGradient(cx - barW, barY, cx + barW, barY)
            grad.addColorStop(0, isRed ? 'rgba(244, 63, 94, 0.8)' : 'rgba(6, 182, 212, 0.8)')
            grad.addColorStop(1, isRed ? 'rgba(244, 63, 94, 0.1)' : 'rgba(6, 182, 212, 0.1)')

            ctx.fillStyle = grad
            ctx.fillRect(isRed ? cx - 80 - barW : cx + 80, barY, barW, 6)
          }
          break
        }

        case 'executive-transactions':
        case 'premium-transactions':
        case 'transactions': {
          // Flowing 3D Isometric Digital Money Rails with Light Trails
          const cx = width / 2
          const cy = height * 0.5
          const numTracks = 5

          // Flowing Rails
          for (let i = 0; i < numTracks; i++) {
            const y = cy + (i - 2) * 32
            ctx.beginPath()
            ctx.moveTo(0, y)
            ctx.lineTo(width, y)
            ctx.strokeStyle = `rgba(99, 102, 241, ${0.15 + (i % 2) * 0.1})`
            ctx.lineWidth = 1.5
            ctx.stroke()

            // Fast digital money packets (₹, $, tokens)
            const speed = 180 + i * 45
            const x = ((t * speed) % (width + 120)) - 60
            const blockW = 50 + (i % 3) * 15

            ctx.fillStyle = 'rgba(99, 102, 241, 0.4)'
            ctx.strokeStyle = '#818cf8'
            ctx.lineWidth = 2
            ctx.shadowColor = '#6366f1'
            ctx.shadowBlur = 15
            ctx.strokeRect(x, y - 10, blockW, 20)
            ctx.fillRect(x, y - 10, blockW, 20)
            ctx.shadowBlur = 0

            // Trailing Light Sparkle
            ctx.beginPath()
            ctx.moveTo(x - 30, y)
            ctx.lineTo(x, y)
            ctx.strokeStyle = '#38bdf8'
            ctx.lineWidth = 2
            ctx.stroke()
          }
          break
        }

        case 'security-center':
        case 'premium-security-center': {
          // 3D Cybernetic Forcefield Shield & Biometric Keylock
          const cx = width / 2
          const cy = height * 0.5
          const hexR = 65 + Math.sin(t * 1.5) * 6

          // Multi-layer rotating 3D hexagon forcefields
          for (let l = 0; l < 3; l++) {
            const r = hexR - l * 16
            ctx.beginPath()
            for (let a = 0; a < 6; a++) {
              const angle = (a * Math.PI) / 3 + t * 0.25 * (l % 2 === 0 ? 1 : -1)
              const x = cx + Math.cos(angle) * r
              const y = cy + Math.sin(angle) * (r * 0.85)
              if (a === 0) ctx.moveTo(x, y)
              else ctx.lineTo(x, y)
            }
            ctx.closePath()
            ctx.strokeStyle = l === 0 ? '#06b6d4' : 'rgba(56, 189, 248, 0.4)'
            ctx.lineWidth = 2
            ctx.shadowColor = '#06b6d4'
            ctx.shadowBlur = l === 0 ? 15 : 0
            ctx.stroke()
            ctx.shadowBlur = 0
          }

          // Undulating DNA Double-Helix Laser Beams
          for (let i = 0; i < 18; i++) {
            const y = cy - 70 + i * 8
            const wave1 = Math.sin(t * 3 + i * 0.35) * 35
            const wave2 = -wave1

            ctx.beginPath()
            ctx.arc(cx + wave1, y, 2.5, 0, Math.PI * 2)
            ctx.fillStyle = '#38bdf8'
            ctx.fill()

            ctx.beginPath()
            ctx.arc(cx + wave2, y, 2.5, 0, Math.PI * 2)
            ctx.fillStyle = '#a855f7'
            ctx.fill()

            // Horizontal cross-rungs
            if (i % 3 === 0) {
              ctx.beginPath()
              ctx.moveTo(cx + wave1, y)
              ctx.lineTo(cx + wave2, y)
              ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)'
              ctx.lineWidth = 1
              ctx.stroke()
            }
          }
          break
        }

        case 'fleet-security': {
          // Orbital Satellite Constellation with Floating Hardware Nodes
          const cx = width / 2
          const cy = height * 0.5
          const nodes = [
            { label: 'MacBook', angle: t * 0.5, r: 80, color: '#38bdf8' },
            { label: 'iPhone', angle: t * 0.5 + (Math.PI * 2) / 3, r: 110, color: '#818cf8' },
            { label: 'Watch', angle: t * 0.5 + (Math.PI * 4) / 3, r: 90, color: '#34d399' },
          ]

          // Center Hardware Enclave Node
          ctx.beginPath()
          ctx.arc(cx, cy, 16, 0, Math.PI * 2)
          ctx.fillStyle = '#6366f1'
          ctx.shadowColor = '#818cf8'
          ctx.shadowBlur = 20
          ctx.fill()
          ctx.shadowBlur = 0

          // Laser links and orbiting hardware nodes
          nodes.forEach((n) => {
            const nx = cx + Math.cos(n.angle) * (n.r * 1.3)
            const ny = cy + Math.sin(n.angle) * (n.r * 0.65)

            // Connecting Laser Link
            ctx.beginPath()
            ctx.moveTo(cx, cy)
            ctx.lineTo(nx, ny)
            ctx.strokeStyle = 'rgba(99, 102, 241, 0.35)'
            ctx.lineWidth = 1.5
            ctx.stroke()

            // Biometric Ripple Wave
            const ping = (t * 1.5) % 1
            ctx.beginPath()
            ctx.arc(nx, ny, 8 + ping * 20, 0, Math.PI * 2)
            ctx.strokeStyle = `rgba(56, 189, 248, ${1 - ping})`
            ctx.lineWidth = 1.5
            ctx.stroke()

            // Node Circle
            ctx.beginPath()
            ctx.arc(nx, ny, 8, 0, Math.PI * 2)
            ctx.fillStyle = n.color
            ctx.shadowColor = n.color
            ctx.shadowBlur = 15
            ctx.fill()
            ctx.shadowBlur = 0
          })
          break
        }

        case 'payment': {
          // High-Speed Quantum Payment Rails with Pre-Auth Spark Waves
          const cy = height * 0.5
          for (let i = 0; i < 4; i++) {
            const speed = 280 + i * 50
            const x = ((t * speed) % (width + 100)) - 50
            const y = cy + (i - 1.5) * 28

            const grad = ctx.createLinearGradient(x - 80, y, x + 30, y)
            grad.addColorStop(0, 'rgba(14, 165, 233, 0)')
            grad.addColorStop(0.8, 'rgba(14, 165, 233, 0.85)')
            grad.addColorStop(1, '#ffffff')

            ctx.beginPath()
            ctx.moveTo(x - 80, y)
            ctx.lineTo(x + 30, y)
            ctx.strokeStyle = grad
            ctx.lineWidth = 4
            ctx.stroke()

            // Sparkle Head
            ctx.beginPath()
            ctx.arc(x + 30, y, 4, 0, Math.PI * 2)
            ctx.fillStyle = '#38bdf8'
            ctx.shadowColor = '#38bdf8'
            ctx.shadowBlur = 15
            ctx.fill()
            ctx.shadowBlur = 0
          }
          break
        }

        case 'live-monitor':
        case 'investigations': {
          // 3D Rotating Geospatial World Radar with Threat Flight Arcs
          const cx = width / 2
          const cy = height * 0.5
          const globeR = 75

          ctx.strokeStyle = 'rgba(245, 158, 11, 0.35)'
          ctx.lineWidth = 1.5
          ctx.beginPath()
          ctx.arc(cx, cy, globeR, 0, Math.PI * 2)
          ctx.stroke()

          // Latitude/Longitude Wireframe Ellipses
          for (let r = 22; r < globeR; r += 22) {
            ctx.beginPath()
            ctx.ellipse(cx, cy, r, globeR, t * 0.25, 0, Math.PI * 2)
            ctx.stroke()
          }

          // Threat Beacons & Arc Trajectories
          for (let b = 0; b < 3; b++) {
            const angle = t * 0.5 + (b * Math.PI * 2) / 3
            const bx = cx + Math.cos(angle) * (globeR * 0.75)
            const by = cy + Math.sin(angle) * (globeR * 0.5)
            const ping = (t * 2 + b * 0.33) % 1

            ctx.beginPath()
            ctx.arc(bx, by, 5 + ping * 18, 0, Math.PI * 2)
            ctx.strokeStyle = `rgba(245, 158, 11, ${1 - ping})`
            ctx.lineWidth = 2
            ctx.stroke()

            ctx.beginPath()
            ctx.arc(bx, by, 4, 0, Math.PI * 2)
            ctx.fillStyle = '#fbbf24'
            ctx.shadowColor = '#f59e0b'
            ctx.shadowBlur = 15
            ctx.fill()
            ctx.shadowBlur = 0
          }
          break
        }

        case 'security-alerts': {
          // Acoustic Threat Sonar with Expanding Danger Polygons
          const cx = width / 2
          const cy = height * 0.5
          for (let i = 0; i < 4; i++) {
            const wave = (t * 0.9 + i * 0.25) % 1
            const r = wave * 130
            ctx.beginPath()
            ctx.arc(cx, cy, r, 0, Math.PI * 2)
            ctx.strokeStyle = `rgba(239, 68, 68, ${Math.max(0, 0.6 - wave * 0.6)})`
            ctx.lineWidth = 2.5
            ctx.stroke()
          }

          // Center Pulsating Red Danger Core
          const beaconSize = 15 + Math.sin(t * 4) * 4
          ctx.beginPath()
          ctx.arc(cx, cy, beaconSize, 0, Math.PI * 2)
          ctx.fillStyle = 'rgba(239, 68, 68, 0.9)'
          ctx.shadowColor = '#ef4444'
          ctx.shadowBlur = 25
          ctx.fill()
          ctx.shadowBlur = 0
          break
        }

        case 'ai-copilot': {
          // 3D Quantum Gyroscope AI Core & Equalizer Waveforms
          const cx = width / 2
          const cy = height * 0.45

          for (let g = 0; g < 3; g++) {
            ctx.save()
            ctx.translate(cx, cy)
            ctx.rotate(t * (0.7 + g * 0.2) + (g * Math.PI) / 3)
            ctx.beginPath()
            ctx.ellipse(0, 0, 85, 30, 0, 0, Math.PI * 2)
            ctx.strokeStyle = `rgba(168, 85, 247, ${0.6 - g * 0.12})`
            ctx.lineWidth = 2.2
            ctx.stroke()
            ctx.restore()
          }

          // Center AI Core
          ctx.beginPath()
          ctx.arc(cx, cy, 16 + Math.sin(t * 3) * 2, 0, Math.PI * 2)
          ctx.fillStyle = '#a855f7'
          ctx.shadowColor = '#c084fc'
          ctx.shadowBlur = 30
          ctx.fill()
          ctx.shadowBlur = 0

          // Audio Spectrum Waveforms
          const numBars = 20
          for (let b = 0; b < numBars; b++) {
            const bx = cx - 90 + b * 9
            const h = 8 + Math.abs(Math.sin(t * 4 + b * 0.4)) * 25
            ctx.fillStyle = 'rgba(192, 132, 252, 0.6)'
            ctx.fillRect(bx, height * 0.85 - h, 5, h)
          }
          break
        }

        default: {
          // Futuristic Cyber Circuit Grid
          for (let p = 0; p < 30; p++) {
            const px = (p * 55 + t * 40) % width
            const py = (p * 85 + Math.sin(t + p) * 25) % height
            ctx.beginPath()
            ctx.arc(px, py, 3, 0, Math.PI * 2)
            ctx.fillStyle = 'rgba(6, 182, 212, 0.4)'
            ctx.shadowColor = '#06b6d4'
            ctx.shadowBlur = 10
            ctx.fill()
            ctx.shadowBlur = 0
          }
        }
      }

      animFrameRef.current = requestAnimationFrame(renderScene)
    }

    renderScene()

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      window.removeEventListener('resize', handleResize)
    }
  }, [isRendered, activeView])

  return (
    <>
      {/* =========================================================================
          1. PROMINENT FLOATING (i) INFO CAPSULE AT BOTTOM RIGHT
          ========================================================================= */}
      {showFloatingButton && (
        <div className="fixed bottom-4 sm:bottom-6 right-20 sm:right-24 md:right-28 z-40">
          <button
            onClick={handleOpen}
            className="relative group px-3 py-2 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-slate-900 border-2 border-cyan-400/80 hover:border-cyan-300 text-slate-100 hover:text-white shadow-[0_10px_25px_rgba(0,0,0,0.8),0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_10px_35px_rgba(6,182,212,0.7)] transition-all duration-300 flex items-center gap-2 cursor-pointer active:scale-95"
            title={`Click to view what the "${intel.title}" module does`}
            aria-label={`Open information about ${intel.title}`}
          >
            <span className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500 opacity-50 group-hover:opacity-100 blur-xs transition-opacity duration-300 pointer-events-none" />

            <div className="relative z-10 w-5 h-5 rounded-full bg-cyan-950 border border-cyan-400 text-cyan-300 flex items-center justify-center font-mono font-black text-xs shadow-[0_0_10px_rgba(6,182,212,0.5)] group-hover:scale-110 transition-transform">
              i
            </div>

            <span className="relative z-10 text-xs font-bold tracking-wide font-mono text-cyan-200 group-hover:text-white uppercase hidden xs:inline">
              Module Guide
            </span>
          </button>
        </div>
      )}

      {/* =========================================================================
          2. COMPACT, VISUAL-FIRST CHARCOAL GREY POPUP
          ========================================================================= */}
      {isRendered && (
        <div
          role="dialog"
          aria-modal="true"
          className={`fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md transition-opacity duration-300 ${
            isAnimatingIn ? 'opacity-100' : 'opacity-0'
          }`}
          onClick={handleClose}
        >
          {/* Small Compact Card */}
          <div
            onClick={(e) => e.stopPropagation()}
            className={`relative w-full max-w-[440px] sm:max-w-[480px] rounded-3xl bg-[#0d121c]/95 border border-slate-700/70 shadow-[0_25px_60px_rgba(0,0,0,0.9),0_0_35px_rgba(6,182,212,0.25)] overflow-hidden transition-all duration-300 transform ${
              isAnimatingIn
                ? 'scale-100 translate-y-0 opacity-100'
                : 'scale-95 translate-y-4 opacity-0'
            }`}
          >
            {/* HERO VISUAL CANVAS (The Main Visual Attraction) */}
            <div className="relative w-full h-44 sm:h-48 overflow-hidden bg-slate-950 border-b border-slate-800/80">
              <canvas ref={canvasRef} className="w-full h-full" />

              {/* Badge Overlay */}
              <div className="absolute top-3.5 left-4 flex items-center gap-2 pointer-events-none">
                <span
                  className="text-[9px] font-mono px-2.5 py-0.5 rounded-full uppercase font-black tracking-wider border shadow-md flex items-center gap-1.5"
                  style={{
                    backgroundColor: `${intel.accent}25`,
                    color: intel.accent,
                    borderColor: `${intel.accent}70`,
                  }}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                  {intel.badge}
                </span>
              </div>

              {/* Close Button Top Right */}
              <button
                onClick={handleClose}
                className="absolute top-3.5 right-4 p-1.5 rounded-full bg-slate-950/80 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700/80 transition cursor-pointer shadow-lg"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* COMPACT CONTENT AREA (5-6 Short Scannable Lines) */}
            <div className="p-5 sm:p-6 space-y-3.5">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-cyan-400" />
                  <span>{intel.title}</span>
                </h3>
                <span className="text-[10px] font-mono text-slate-400">FRAUDLENS INTEL</span>
              </div>

              {/* Short, Easy English Lines (No numbers, quick scan) */}
              <div className="space-y-1.5 text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
                {intel.description.map((line, idx) => (
                  <p key={idx} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
                    <span>{line}</span>
                  </p>
                ))}
              </div>

              {/* 3 Quick Capability Tags */}
              <div className="pt-2 flex flex-wrap gap-1.5 border-t border-slate-800/80">
                {intel.features.map((feat, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-slate-900 border border-slate-800 text-cyan-300 font-semibold"
                  >
                    {feat}
                  </span>
                ))}
              </div>

              {/* Action Button */}
              <div className="pt-1">
                <button
                  onClick={handleClose}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-cyan-950/50 transition flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <span>Explore Module</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
