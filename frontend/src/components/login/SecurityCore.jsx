import React, { useEffect, useRef } from 'react'
import { Lock, Unlock, Shield, ShieldCheck, Zap } from 'lucide-react'

/**
 * SecurityCore - Holographic 3D Wireframe Globe, Concentric Sci-Fi Pedestal,
 * and Central Locked/Unlocked Shield Centerpiece matching the cinematic command center reference.
 */
export default function SecurityCore({
  isUnlocked = false,
  sequenceStage = 'IDLE', // 'IDLE' | 'AUTHENTICATING' | 'VERIFIED' | 'SHIELD_UNLOCK' | 'SYSTEM_HANDOFF' | 'ENERGY_PULSE' | 'COMMAND_CENTER_OPEN'
  mouseOffset = { x: 0, y: 0 },
}) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId
    let width = (canvas.width = canvas.offsetWidth * window.devicePixelRatio)
    let height = (canvas.height = canvas.offsetHeight * window.devicePixelRatio)

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Generate 3D sphere wireframe vertices (latitude & longitude rings)
    const sphereRadius = Math.min(width, height) * 0.28
    const numLat = 10
    const numLon = 16
    const vertices = []

    for (let lat = 1; lat < numLat; lat++) {
      const phi = (Math.PI * lat) / numLat
      const y = Math.cos(phi) * sphereRadius
      const rAtY = Math.sin(phi) * sphereRadius

      for (let lon = 0; lon < numLon; lon++) {
        const theta = (2 * Math.PI * lon) / numLon
        const x = Math.cos(theta) * rAtY
        const z = Math.sin(theta) * rAtY
        vertices.push({ x, y, z, lat, lon })
      }
    }

    // Floating neural data particles
    const particleCount = 45
    const particles = Array.from({ length: particleCount }, () => ({
      x: (Math.random() - 0.5) * (width * 0.8),
      y: (Math.random() - 0.5) * (height * 0.8),
      radius: Math.random() * 2 + 1,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      alpha: Math.random() * 0.7 + 0.3,
      isFlagged: Math.random() < 0.12,
    }))

    let rotY = 0

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      const centerX = width / 2
      const centerY = height / 2 - 15

      const isHyperSpeed =
        sequenceStage === 'SYSTEM_HANDOFF' ||
        sequenceStage === 'ENERGY_PULSE' ||
        sequenceStage === 'COMMAND_CENTER_OPEN'
      const speedMult = isHyperSpeed ? 3.8 : sequenceStage === 'AUTHENTICATING' ? 1.8 : 1.0

      ctx.save()
      ctx.translate(centerX, centerY)

      // 1. Perspective Cybernetic Pedestal Base (bottom concentric sci-fi rings)
      const pedestalY = sphereRadius * 0.95
      const pedestalW = sphereRadius * 2.2
      const pedestalH = sphereRadius * 0.7

      // Multi-layer pedestal gradient
      ctx.save()
      ctx.translate(0, pedestalY)

      // Outer glowing ring
      ctx.strokeStyle = isUnlocked ? 'rgba(52, 211, 153, 0.5)' : 'rgba(6, 182, 212, 0.45)'
      ctx.lineWidth = 2.5
      ctx.beginPath()
      ctx.ellipse(0, 0, pedestalW * 0.6, pedestalH * 0.4, 0, 0, Math.PI * 2)
      ctx.stroke()

      // Mid tier ring with dashed tick marks
      ctx.strokeStyle = isUnlocked ? 'rgba(34, 211, 238, 0.6)' : 'rgba(168, 85, 247, 0.45)'
      ctx.lineWidth = 1.8
      ctx.setLineDash([8, 14])
      ctx.beginPath()
      ctx.ellipse(0, -6, pedestalW * 0.48, pedestalH * 0.32, 0, rotY, rotY + Math.PI * 2)
      ctx.stroke()

      // Inner glowing core ring
      ctx.setLineDash([])
      ctx.strokeStyle = isUnlocked ? 'rgba(52, 211, 153, 0.8)' : 'rgba(34, 211, 238, 0.8)'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.ellipse(0, -12, pedestalW * 0.36, pedestalH * 0.24, 0, 0, Math.PI * 2)
      ctx.stroke()

      // Vertical holographic light beams rising from the pedestal
      for (let b = -4; b <= 4; b++) {
        const beamX = b * (pedestalW * 0.08)
        const beamGrad = ctx.createLinearGradient(beamX, -12, beamX, -sphereRadius * 1.5)
        beamGrad.addColorStop(0, isUnlocked ? 'rgba(52, 211, 153, 0.4)' : 'rgba(6, 182, 212, 0.35)')
        beamGrad.addColorStop(1, 'rgba(6, 182, 212, 0)')
        ctx.strokeStyle = beamGrad
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.moveTo(beamX, -12)
        ctx.lineTo(beamX, -sphereRadius * 1.4)
        ctx.stroke()
      }

      ctx.restore()

      // 2. Central 3D Wireframe Neural Globe
      const d = 400 // Camera distance for projection
      const projected = vertices.map((v) => {
        // Rotate around Y-axis
        const cos = Math.cos(rotY)
        const sin = Math.sin(rotY)
        const xRot = v.x * cos - v.z * sin
        const zRot = v.x * sin + v.z * cos
        const scale = d / (d + zRot)
        return {
          x: xRot * scale,
          y: v.y * scale,
          z: zRot,
          alpha: (zRot + sphereRadius) / (2 * sphereRadius), // Depth shading
          lat: v.lat,
          lon: v.lon,
        }
      })

      // Draw latitude lines
      for (let lat = 1; lat < numLat; lat++) {
        const latPoints = projected.filter((p) => p.lat === lat)
        if (latPoints.length > 2) {
          ctx.beginPath()
          ctx.strokeStyle = isUnlocked ? 'rgba(52, 211, 153, 0.22)' : 'rgba(6, 182, 212, 0.20)'
          ctx.lineWidth = 1
          ctx.moveTo(latPoints[0].x, latPoints[0].y)
          for (let i = 1; i < latPoints.length; i++) {
            ctx.lineTo(latPoints[i].x, latPoints[i].y)
          }
          ctx.closePath()
          ctx.stroke()
        }
      }

      // Draw projected wireframe nodes
      projected.forEach((p) => {
        const isFront = p.z > -sphereRadius * 0.3
        if (isFront) {
          ctx.fillStyle = isUnlocked
            ? `rgba(52, 211, 153, ${0.4 + p.alpha * 0.5})`
            : `rgba(34, 211, 238, ${0.35 + p.alpha * 0.5})`
          ctx.beginPath()
          ctx.arc(p.x, p.y, 1.4 + p.alpha * 1.2, 0, Math.PI * 2)
          ctx.fill()
        }
      })

      // 3. Dynamic Orbital Rings around Globe
      // Ring A (Cyan Tilt)
      ctx.save()
      ctx.rotate(-0.25)
      ctx.strokeStyle = isUnlocked ? 'rgba(52, 211, 153, 0.55)' : 'rgba(6, 182, 212, 0.5)'
      ctx.lineWidth = 2
      ctx.setLineDash([12, 20])
      ctx.beginPath()
      ctx.ellipse(0, 0, sphereRadius * 1.35, sphereRadius * 0.5, 0, rotY * 1.5, rotY * 1.5 + Math.PI * 2)
      ctx.stroke()
      ctx.restore()

      // Ring B (Purple Counter-Tilt)
      ctx.save()
      ctx.rotate(0.35)
      ctx.strokeStyle = isUnlocked ? 'rgba(34, 211, 238, 0.6)' : 'rgba(168, 85, 247, 0.5)'
      ctx.lineWidth = 1.6
      ctx.setLineDash([6, 16])
      ctx.beginPath()
      ctx.ellipse(0, 0, sphereRadius * 1.25, sphereRadius * 0.45, 0, -rotY * 1.2, -rotY * 1.2 + Math.PI * 2)
      ctx.stroke()
      ctx.restore()

      // 4. Floating Neural Data Particles
      particles.forEach((p) => {
        if (!prefersReducedMotion) {
          if (isHyperSpeed) {
            p.x *= 0.96
            p.y *= 0.96
          } else {
            p.x += p.vx * speedMult
            p.y += p.vy * speedMult
            const maxD = sphereRadius * 1.5
            const currentD = Math.sqrt(p.x * p.x + p.y * p.y)
            if (currentD > maxD) {
              p.vx *= -1
              p.vy *= -1
            }
          }
        }

        ctx.fillStyle = isUnlocked
          ? `rgba(52, 211, 153, ${p.alpha})`
          : p.isFlagged
          ? `rgba(244, 63, 94, ${p.alpha})`
          : `rgba(34, 211, 238, ${p.alpha})`
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fill()
      })

      ctx.restore()

      if (!prefersReducedMotion) {
        rotY += 0.009 * speedMult
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
  }, [isUnlocked, sequenceStage])

  // Mouse parallax 3D tilt
  const tiltStyle = {
    transform: `perspective(1200px) rotateY(${mouseOffset.x * 10}deg) rotateX(${-mouseOffset.y * 10}deg) translateZ(0)`,
    transition: 'transform 0.15s ease-out',
  }

  return (
    <div className="relative w-full h-[400px] sm:h-[480px] lg:h-[540px] flex items-center justify-center select-none" style={tiltStyle}>
      {/* 1. Canvas Layer: 3D Wireframe Globe, Pedestal, Orbital Rings */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
        aria-hidden="true"
      />

      {/* 2. Central Glowing Holographic Security Shield Centerpiece */}
      <div className="relative z-10 flex flex-col items-center justify-center -translate-y-4">
        {/* Shield Atmospheric Aura */}
        <div
          className={`absolute w-44 sm:w-56 h-44 sm:h-56 rounded-full filter blur-3xl pointer-events-none transition-all duration-700 ${
            isUnlocked
              ? 'bg-emerald-500/40 scale-125'
              : sequenceStage === 'AUTHENTICATING'
              ? 'bg-cyan-400/45 scale-110'
              : 'bg-cyan-500/30'
          }`}
        />

        {/* High-Fidelity SVG Cyber Shield */}
        <div className="relative w-36 h-44 sm:w-44 sm:h-52 flex items-center justify-center transition-transform duration-500 animate-shield-breathe">
          <svg
            viewBox="0 0 200 240"
            className="w-full h-full drop-shadow-[0_0_35px_rgba(6,182,212,0.8)]"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <linearGradient id="shieldGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={isUnlocked ? '#10B981' : '#06B6D4'} stopOpacity="0.85" />
                <stop offset="50%" stopColor={isUnlocked ? '#059669' : '#3B82F6'} stopOpacity="0.75" />
                <stop offset="100%" stopColor="#020617" stopOpacity="0.95" />
              </linearGradient>

              <linearGradient id="shieldStroke2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={isUnlocked ? '#6EE7B7' : '#38BDF8'} />
                <stop offset="50%" stopColor={isUnlocked ? '#10B981' : '#818CF8'} />
                <stop offset="100%" stopColor={isUnlocked ? '#047857' : '#0284C7'} />
              </linearGradient>
            </defs>

            {/* Outer Cyber Shield Contour */}
            <path
              d="M 100 12 
                 C 145 12, 184 32, 184 85 
                 C 184 158, 130 205, 100 230 
                 C 70 205, 16 158, 16 85 
                 C 16 32, 55 12, 100 12 Z"
              fill="url(#shieldGrad2)"
              stroke="url(#shieldStroke2)"
              strokeWidth="4"
            />

            {/* Inner Holographic Grid Hatch */}
            <path
              d="M 100 30 
                 C 135 30, 166 48, 166 90 
                 C 166 148, 124 186, 100 208 
                 C 76 186, 34 148, 34 90 
                 C 34 48, 65 30, 100 30 Z"
              fill="rgba(2, 6, 23, 0.75)"
              stroke={isUnlocked ? 'rgba(52, 211, 153, 0.7)' : 'rgba(34, 211, 238, 0.55)'}
              strokeWidth="1.8"
              strokeDasharray="6 4"
            />

            {/* Core Circular Padlock Capsule */}
            <circle
              cx="100"
              cy="105"
              r="40"
              fill="rgba(2, 6, 23, 0.92)"
              stroke={isUnlocked ? '#34D399' : '#06B6D4'}
              strokeWidth="2.8"
            />
          </svg>

          {/* Central Padlock (Locked Initially 🔒 -> Unlocks On Auth Success) */}
          <div className="absolute inset-0 flex items-center justify-center pt-2">
            {isUnlocked ? (
              <div className="flex flex-col items-center justify-center animate-bounce">
                <div className="p-3.5 rounded-full bg-emerald-500/20 border-2 border-emerald-400 shadow-[0_0_35px_rgba(52,211,153,1)]">
                  <Unlock className="w-9 h-9 sm:w-11 sm:h-11 text-emerald-300 drop-shadow-[0_0_12px_#34d399]" />
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center">
                <div
                  className={`p-3.5 rounded-full bg-slate-950/90 border-2 transition-all duration-300 ${
                    sequenceStage === 'AUTHENTICATING'
                      ? 'border-cyan-400 shadow-[0_0_35px_rgba(6,182,212,1)] scale-110'
                      : 'border-cyan-500/70 shadow-[0_0_25px_rgba(6,182,212,0.65)]'
                  }`}
                >
                  <Lock
                    className={`w-9 h-9 sm:w-11 sm:h-11 text-cyan-300 drop-shadow-[0_0_12px_#22d3ee] ${
                      sequenceStage === 'AUTHENTICATING' ? 'animate-pulse' : ''
                    }`}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Shield Status Capsule */}
        <div className="mt-2 flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-950/90 border border-cyan-800/80 backdrop-blur-md shadow-xl">
          <span
            className={`w-2 h-2 rounded-full ${
              isUnlocked
                ? 'bg-emerald-400 shadow-[0_0_12px_#34d399]'
                : sequenceStage === 'AUTHENTICATING'
                ? 'bg-amber-400 animate-ping'
                : 'bg-cyan-400 shadow-[0_0_8px_#22d3ee]'
            }`}
          />
          <span className="text-[10px] sm:text-[11px] font-mono font-extrabold tracking-wider uppercase text-slate-200">
            {isUnlocked
              ? 'ACCESS VERIFIED • CORE UNLOCKED'
              : sequenceStage === 'AUTHENTICATING'
              ? 'AUTHENTICATING ENCRYPTED ACCESS...'
              : 'AI NEURAL SHIELD • LOCKED 🔒'}
          </span>
        </div>
      </div>
    </div>
  )
}
