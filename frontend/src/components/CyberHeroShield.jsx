import React, { useEffect, useRef } from 'react'

/**
 * CyberHeroShield - Holographic AI Security Core 3D/Canvas Component.
 * Preserves the dark cyber fintech aesthetic with rotating neural rings,
 * dynamic transaction particles, holographic shield, and radar telemetry.
 * Automatically respects prefers-reduced-motion.
 */
export default function CyberHeroShield({ activeModel, fraudRate = 0, riskScore = 0 }) {
  const canvasRef = useRef(null)

  const isHighRisk = Number(riskScore) > 70 || Number(fraudRate) > 5.0
  const isMedRisk = Number(riskScore) > 30

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId
    let width = (canvas.width = canvas.offsetWidth * window.devicePixelRatio)
    let height = (canvas.height = canvas.offsetHeight * window.devicePixelRatio)

    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Particle nodes representing network transaction verification
    const particleCount = 48
    const particles = Array.from({ length: particleCount }, () => ({
      x: (Math.random() - 0.5) * (width * 0.7),
      y: (Math.random() - 0.5) * (height * 0.7),
      radius: Math.random() * 2 + 1,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      alpha: Math.random() * 0.7 + 0.3,
      isRisk: Math.random() < (isHighRisk ? 0.25 : 0.12),
    }))

    let angle = 0

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      const centerX = width / 2
      const centerY = height / 2

      // 1. Cyber Grid Radial Glow
      const gradient = ctx.createRadialGradient(centerX, centerY, 10, centerX, centerY, width * 0.45)
      if (isHighRisk) {
        gradient.addColorStop(0, 'rgba(244, 63, 94, 0.15)')
        gradient.addColorStop(0.5, 'rgba(168, 85, 247, 0.08)')
      } else if (isMedRisk) {
        gradient.addColorStop(0, 'rgba(245, 158, 11, 0.14)')
        gradient.addColorStop(0.5, 'rgba(6, 182, 212, 0.08)')
      } else {
        gradient.addColorStop(0, 'rgba(6, 182, 212, 0.12)')
        gradient.addColorStop(0.5, 'rgba(99, 102, 241, 0.06)')
      }
      gradient.addColorStop(1, 'rgba(2, 6, 23, 0)')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, width * 0.45, 0, Math.PI * 2)
      ctx.fill()

      // 2. Rotating Holographic Outer Neural Rings
      ctx.save()
      ctx.translate(centerX, centerY)

      // Ring 1 (Electric Primary)
      ctx.strokeStyle = isHighRisk ? 'rgba(244, 63, 94, 0.45)' : 'rgba(6, 182, 212, 0.4)'
      ctx.lineWidth = 1.5
      ctx.setLineDash([12, 18])
      ctx.beginPath()
      ctx.arc(0, 0, Math.min(width, height) * 0.36, angle, angle + Math.PI * 2)
      ctx.stroke()

      // Ring 2 (Purple/Cyan Accent)
      ctx.strokeStyle = 'rgba(168, 85, 247, 0.35)'
      ctx.lineWidth = 1.2
      ctx.setLineDash([8, 24])
      ctx.beginPath()
      ctx.arc(0, 0, Math.min(width, height) * 0.30, -angle * 1.4, -angle * 1.4 + Math.PI * 2)
      ctx.stroke()

      // Ring 3 (Radar Sweep)
      ctx.setLineDash([])
      const sweepGradient = ctx.createConicGradient(angle * 1.8, 0, 0)
      sweepGradient.addColorStop(0, 'rgba(6, 182, 212, 0)')
      sweepGradient.addColorStop(0.85, 'rgba(6, 182, 212, 0)')
      sweepGradient.addColorStop(1, isHighRisk ? 'rgba(244, 63, 94, 0.25)' : 'rgba(6, 182, 212, 0.25)')
      ctx.fillStyle = sweepGradient
      ctx.beginPath()
      ctx.arc(0, 0, Math.min(width, height) * 0.36, 0, Math.PI * 2)
      ctx.fill()

      // 3. Floating Network Verification Particles
      particles.forEach((p, idx) => {
        if (!prefersReducedMotion) {
          p.x += p.vx
          p.y += p.vy
          const maxDist = Math.min(width, height) * 0.35
          const currentDist = Math.sqrt(p.x * p.x + p.y * p.y)
          if (currentDist > maxDist) {
            p.vx *= -1
            p.vy *= -1
          }
        }

        ctx.fillStyle = p.isRisk ? `rgba(244, 63, 94, ${p.alpha})` : `rgba(34, 211, 238, ${p.alpha})`
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fill()

        // Connect nearby nodes
        for (let j = idx + 1; j < particles.length; j++) {
          const p2 = particles[j]
          const dx = p.x - p2.x
          const dy = p.y - p2.y
          const d = Math.sqrt(dx * dx + dy * dy)
          if (d < 55) {
            ctx.strokeStyle = p.isRisk || p2.isRisk ? 'rgba(244, 63, 94, 0.18)' : 'rgba(34, 211, 238, 0.12)'
            ctx.lineWidth = 0.6
            ctx.beginPath()
            ctx.moveTo(p.x, p.y)
            ctx.lineTo(p2.x, p2.y)
            ctx.stroke()
          }
        }
      })

      // 4. Central Holographic Security Shield Geometry
      const shieldScale = Math.min(width, height) * 0.16
      ctx.shadowColor = isHighRisk ? 'rgba(244, 63, 94, 0.6)' : 'rgba(6, 182, 212, 0.6)'
      ctx.shadowBlur = 15
      ctx.strokeStyle = isHighRisk ? 'rgba(251, 113, 133, 0.9)' : 'rgba(34, 211, 238, 0.85)'
      ctx.lineWidth = 2.5
      ctx.fillStyle = 'rgba(15, 23, 42, 0.75)'

      ctx.beginPath()
      ctx.moveTo(0, -shieldScale)
      ctx.bezierCurveTo(shieldScale * 0.8, -shieldScale * 0.9, shieldScale * 0.9, -shieldScale * 0.2, shieldScale * 0.8, shieldScale * 0.3)
      ctx.bezierCurveTo(shieldScale * 0.6, shieldScale * 0.8, 0, shieldScale * 1.1, 0, shieldScale * 1.25)
      ctx.bezierCurveTo(0, shieldScale * 1.1, -shieldScale * 0.6, shieldScale * 0.8, -shieldScale * 0.8, shieldScale * 0.3)
      ctx.bezierCurveTo(-shieldScale * 0.9, -shieldScale * 0.2, -shieldScale * 0.8, -shieldScale * 0.9, 0, -shieldScale)
      ctx.closePath()
      ctx.fill()
      ctx.stroke()
      ctx.shadowBlur = 0

      // Inner Core Glow Icon
      ctx.strokeStyle = isHighRisk ? 'rgba(244, 63, 94, 0.8)' : 'rgba(168, 85, 247, 0.7)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(-shieldScale * 0.3, 0)
      ctx.lineTo(0, -shieldScale * 0.35)
      ctx.lineTo(shieldScale * 0.3, 0)
      ctx.lineTo(0, shieldScale * 0.35)
      ctx.closePath()
      ctx.stroke()

      ctx.restore()

      if (!prefersReducedMotion) {
        angle += 0.007
        animationFrameId = requestAnimationFrame(render)
      }
    }

    render()

    const handleResize = () => {
      width = canvas.width = canvas.offsetWidth * window.devicePixelRatio
      height = canvas.height = canvas.offsetHeight * window.devicePixelRatio
      if (prefersReducedMotion) render()
    }

    window.addEventListener('resize', handleResize)
    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
    }
  }, [isHighRisk, isMedRisk])

  const modelName = activeModel?.model_name || activeModel?.name || 'XGBoost_Champion'
  const modelVersion = activeModel?.model_version || activeModel?.version || 'v1.2.0'
  const thresholdVal = activeModel?.threshold ?? 0.50

  return (
    <div className="relative w-full h-56 sm:h-64 rounded-3xl bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-slate-950/90 border border-cyan-900/40 overflow-hidden shadow-2xl flex items-center justify-between p-4 sm:p-6">
      {/* Canvas Hologram Background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
        aria-hidden="true"
      />

      {/* Hero Foreground Content */}
      <div className="relative z-10 max-w-md space-y-2.5">
        <div className="flex items-center gap-2">
          <span className="flex h-2.5 w-2.5 relative">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isHighRisk ? 'bg-rose-400' : 'bg-cyan-400'} opacity-75`}></span>
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isHighRisk ? 'bg-rose-500' : 'bg-cyan-500'}`}></span>
          </span>
          <span className={`text-[11px] font-mono tracking-widest uppercase font-bold ${isHighRisk ? 'text-rose-400' : 'text-cyan-400'}`}>
            AI Neural Shield • {isHighRisk ? 'Threat Elevated' : 'Defense Active'}
          </span>
        </div>

        <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
          FraudLens AI Intelligence Command Center
        </h2>

        <p className="text-xs text-slate-300 leading-relaxed max-w-sm">
          Real-time multi-model financial defense with validation-tuned decision boundaries, deterministic risk scoring, and local SHAP explainability.
        </p>

        <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] font-mono">
          <div className="px-2.5 py-1 rounded-lg bg-slate-950/80 border border-cyan-800/60 text-cyan-300 shadow-sm">
            Model: <span className="font-bold text-white uppercase">{String(modelName).replace('_', ' ')}</span>
          </div>
          <div className="px-2.5 py-1 rounded-lg bg-slate-950/80 border border-purple-800/60 text-purple-300 shadow-sm">
            Version: <span className="font-bold text-white">{modelVersion}</span>
          </div>
          <div className="px-2.5 py-1 rounded-lg bg-slate-950/80 border border-emerald-800/60 text-emerald-300 shadow-sm">
            Threshold: <span className="font-bold text-white">{Number(thresholdVal).toFixed(4)}</span>
          </div>
        </div>
      </div>

      {/* Right Cyber Stat Pills */}
      <div className="relative z-10 hidden md:flex flex-col gap-2.5 text-right font-mono">
        <div className="bg-slate-950/85 backdrop-blur-md border border-slate-800/90 rounded-2xl p-3 text-right shadow-lg">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Population Fraud Rate</div>
          <div className={`text-xl font-black ${isHighRisk ? 'text-rose-400' : 'text-emerald-400'}`}>
            {Number(fraudRate).toFixed(2)}%
          </div>
        </div>
        <div className="bg-slate-950/85 backdrop-blur-md border border-slate-800/90 rounded-2xl p-3 text-right shadow-lg">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Mean Risk Score</div>
          <div className="text-xl font-black text-cyan-400">
            {Number(riskScore).toFixed(1)} <span className="text-xs font-normal text-slate-500">/ 100</span>
          </div>
        </div>
      </div>
    </div>
  )
}
