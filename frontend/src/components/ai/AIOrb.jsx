import React, { useRef, useEffect } from 'react'

/**
 * AIOrb — Bioluminescent Holographic AI Visual Core with Warm Ivory Luminescence.
 *
 * Visual Direction:
 * - Deep dark-blue environment + warm-white & ivory illumination emerging from the core
 * - Reference video motion language: controlled, organic, mathematically precise
 *
 * 7 Defined States:
 * - 'idle': Subtle organic breathing with warm ivory nucleus and deep blue/cyan aura.
 * - 'listening': Gentle rhythmic dilation with responsive ambient waves.
 * - 'searching': Moving radial radar sweep / scanning beam with data particle drift.
 * - 'analysing': Higher particle excitation with luminous energy flares.
 * - 'deep_reasoning': Dual counter-rotating harmonic rings with high-intensity ivory core.
 * - 'cross_validating': Multi-node orbiting satellite beacons exchanging data trails.
 * - 'ready': Harmonious deceleration into a tranquil, warm glow.
 */
export default function AIOrb({
  state = 'idle', // 'idle' | 'listening' | 'searching' | 'analysing' | 'deep_reasoning' | 'cross_validating' | 'ready'
  size = 180,
  provider = 'auto',
  className = '',
  onClick,
}) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId
    let startTime = performance.now()

    // Respect reduced-motion accessibility preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Provider color palettes with warm-white / ivory highlights
    const paletteMap = {
      auto: {
        primary: 'rgba(6, 182, 212, ',     // Cyan
        secondary: 'rgba(59, 130, 246, ',  // Deep Blue
        accent: 'rgba(16, 185, 129, ',     // Emerald
        coreWarm: 'rgba(255, 253, 245, ',  // Warm Ivory / Soft White
        coreIvory: '#fefae0',
        glow: 'rgba(6, 182, 212, 0.45)',
      },
      gemini: {
        primary: 'rgba(6, 182, 212, ',     // Cyan
        secondary: 'rgba(37, 99, 235, ',   // Blue
        accent: 'rgba(147, 197, 253, ',    // Ice Blue
        coreWarm: 'rgba(255, 255, 255, ',  // Cool White
        coreIvory: '#ffffff',
        glow: 'rgba(6, 182, 212, 0.5)',
      },
      grok: {
        primary: 'rgba(139, 92, 246, ',    // Violet
        secondary: 'rgba(99, 102, 241, ',  // Indigo
        accent: 'rgba(245, 158, 11, ',     // Amber
        coreWarm: 'rgba(255, 251, 235, ',  // Warm Amber-White
        coreIvory: '#fef3c7',
        glow: 'rgba(139, 92, 246, 0.5)',
      },
      mistral: {
        primary: 'rgba(245, 158, 11, ',    // Amber / Gold
        secondary: 'rgba(217, 119, 6, ',   // Warm Gold
        accent: 'rgba(251, 191, 36, ',     // Pale Gold
        coreWarm: 'rgba(255, 253, 245, ',  // Warm Ivory
        coreIvory: '#fffbeb',
        glow: 'rgba(245, 158, 11, 0.45)',
      },
    }

    const currentPalette = paletteMap[provider] || paletteMap.auto

    // Particle nodes for orbiting intelligence dust
    const isHeavy = state === 'deep_reasoning' || state === 'cross_validating'
    const particleCount = isHeavy ? 36 : state === 'analysing' || state === 'searching' ? 26 : 14
    const particles = Array.from({ length: particleCount }, (_, i) => ({
      angle: (i / particleCount) * Math.PI * 2,
      distance: 30 + Math.random() * 38,
      speed: 0.008 + Math.random() * 0.018,
      size: 1.0 + Math.random() * 2.2,
      opacity: 0.35 + Math.random() * 0.65,
      isCore: i % 4 === 0,
    }))

    const render = (time) => {
      const elapsed = (time - startTime) / 1000
      ctx.clearRect(0, 0, size, size)

      const centerX = size / 2
      const centerY = size / 2
      const baseRadius = size * 0.22

      // State speeds and multipliers
      let speedMultiplier = 1.0
      let pulseIntensity = 0.07
      let deformationMagnitude = 3

      if (state === 'listening') {
        speedMultiplier = 1.3
        pulseIntensity = 0.14
        deformationMagnitude = 5
      } else if (state === 'searching') {
        speedMultiplier = 1.8
        pulseIntensity = 0.18
        deformationMagnitude = 6
      } else if (state === 'analysing') {
        speedMultiplier = 2.4
        pulseIntensity = 0.22
        deformationMagnitude = 8
      } else if (state === 'deep_reasoning') {
        speedMultiplier = 3.0
        pulseIntensity = 0.26
        deformationMagnitude = 11
      } else if (state === 'cross_validating') {
        speedMultiplier = 2.2
        pulseIntensity = 0.20
        deformationMagnitude = 7
      } else if (state === 'ready') {
        speedMultiplier = 0.7
        pulseIntensity = 0.04
        deformationMagnitude = 2
      }

      if (prefersReducedMotion) {
        speedMultiplier = 0.05
        pulseIntensity = 0.02
        deformationMagnitude = 1
      }

      const breath = 1 + Math.sin(elapsed * 2 * speedMultiplier) * pulseIntensity

      // ── 1. DEEP DARK-BLUE AMBIENT BACKGROUND FIELD ──
      const outerGlow = ctx.createRadialGradient(
        centerX, centerY, baseRadius * 0.1,
        centerX, centerY, baseRadius * 2.4 * breath
      )
      outerGlow.addColorStop(0, currentPalette.coreWarm + '0.22)')
      outerGlow.addColorStop(0.3, currentPalette.primary + '0.28)')
      outerGlow.addColorStop(0.7, currentPalette.secondary + '0.12)')
      outerGlow.addColorStop(1, 'rgba(10, 15, 29, 0)')

      ctx.fillStyle = outerGlow
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius * 2.4 * breath, 0, Math.PI * 2)
      ctx.fill()

      // ── 2. RADIAL SEARCHING RADAR BEAM (Only when state === 'searching') ──
      if (state === 'searching') {
        const sweepAngle = elapsed * 3.5
        const sweepRadius = baseRadius * 1.8

        ctx.save()
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.arc(centerX, centerY, sweepRadius, sweepAngle, sweepAngle + Math.PI / 3)
        ctx.closePath()

        const sweepGradient = ctx.createRadialGradient(
          centerX, centerY, 0,
          centerX, centerY, sweepRadius
        )
        sweepGradient.addColorStop(0, currentPalette.coreWarm + '0.6)')
        sweepGradient.addColorStop(0.7, currentPalette.primary + '0.3)')
        sweepGradient.addColorStop(1, 'rgba(6, 182, 212, 0)')
        ctx.fillStyle = sweepGradient
        ctx.fill()
        ctx.restore()
      }

      // ── 3. ORBITAL LIGHT RINGS (Counter-rotating 3D ellipses) ──
      const ringRotations = [
        { angle: elapsed * 0.8 * speedMultiplier, tiltX: 0.85, tiltY: 0.35, color: currentPalette.primary },
        { angle: -elapsed * 0.65 * speedMultiplier + Math.PI / 3, tiltX: 0.45, tiltY: 0.85, color: currentPalette.secondary },
        { angle: elapsed * 1.1 * speedMultiplier + Math.PI / 1.5, tiltX: 0.7, tiltY: 0.7, color: currentPalette.coreWarm },
      ]

      ringRotations.forEach((ring) => {
        ctx.save()
        ctx.translate(centerX, centerY)
        ctx.rotate(ring.angle)
        ctx.scale(ring.tiltX, ring.tiltY)

        ctx.beginPath()
        ctx.arc(0, 0, baseRadius * 1.45 * breath, 0, Math.PI * 2)
        ctx.strokeStyle = ring.color + (state === 'deep_reasoning' ? '0.75)' : '0.45)')
        ctx.lineWidth = 1.4
        ctx.stroke()

        // Orbital beacon photon
        const beaconX = Math.cos(ring.angle * 2) * baseRadius * 1.45 * breath
        const beaconY = Math.sin(ring.angle * 2) * baseRadius * 1.45 * breath
        ctx.beginPath()
        ctx.arc(beaconX, beaconY, 2.2, 0, Math.PI * 2)
        ctx.fillStyle = '#ffffff'
        ctx.shadowColor = '#ffffff'
        ctx.shadowBlur = 8
        ctx.fill()
        ctx.shadowBlur = 0

        ctx.restore()
      })

      // ── 4. CROSS-VALIDATING SATELLITE BEACONS (When cross_validating) ──
      if (state === 'cross_validating') {
        const beaconCount = 3
        for (let b = 0; b < beaconCount; b++) {
          const bAngle = elapsed * 1.5 + (b * Math.PI * 2) / beaconCount
          const bDist = baseRadius * 1.7
          const bx = centerX + Math.cos(bAngle) * bDist
          const by = centerY + Math.sin(bAngle) * bDist

          // Data trail connecting to core
          ctx.beginPath()
          ctx.moveTo(centerX, centerY)
          ctx.lineTo(bx, by)
          ctx.strokeStyle = currentPalette.coreWarm + '0.3)'
          ctx.lineWidth = 0.8
          ctx.setLineDash([3, 3])
          ctx.stroke()
          ctx.setLineDash([])

          // Satellite beacon dot
          ctx.beginPath()
          ctx.arc(bx, by, 3.2, 0, Math.PI * 2)
          ctx.fillStyle = currentPalette.coreIvory
          ctx.shadowColor = '#fffdfa'
          ctx.shadowBlur = 10
          ctx.fill()
          ctx.shadowBlur = 0
        }
      }

      // ── 5. HARMONIC DEFORMING LIQUID CORE WITH WARM IVORY EMBEDDING ──
      ctx.save()
      ctx.beginPath()
      const segments = 64
      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2
        // Dual harmonic wave synthesis
        const wave1 = Math.sin(theta * 3 + elapsed * 3 * speedMultiplier) * deformationMagnitude
        const wave2 = Math.cos(theta * 5 - elapsed * 2 * speedMultiplier) * (deformationMagnitude * 0.5)
        const wave3 = Math.sin(theta * 2 + elapsed * 4 * speedMultiplier) * (deformationMagnitude * 0.3)
        const currentR = baseRadius * breath + wave1 + wave2 + wave3

        const x = centerX + Math.cos(theta) * currentR
        const y = centerY + Math.sin(theta) * currentR
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.closePath()

      // Gradient: Warm Ivory Center radiating into deep cyan/navy
      const coreGradient = ctx.createRadialGradient(
        centerX - baseRadius * 0.15,
        centerY - baseRadius * 0.15,
        baseRadius * 0.05,
        centerX,
        centerY,
        baseRadius * 1.2
      )
      coreGradient.addColorStop(0, 'rgba(255, 255, 255, 0.98)')      // Pure white nucleus
      coreGradient.addColorStop(0.25, currentPalette.coreWarm + '0.92)') // Soft warm ivory
      coreGradient.addColorStop(0.6, currentPalette.primary + '0.80)')   // Primary cyan/indigo
      coreGradient.addColorStop(0.9, currentPalette.secondary + '0.85)') // Deep oceanic blue
      coreGradient.addColorStop(1, 'rgba(7, 13, 30, 0.95)')           // Outer perimeter

      ctx.fillStyle = coreGradient
      ctx.shadowColor = currentPalette.coreIvory
      ctx.shadowBlur = state === 'deep_reasoning' ? 24 : 14
      ctx.fill()
      ctx.shadowBlur = 0
      ctx.restore()

      // ── 6. WARM WHITE HIGH-FREQUENCY NUCLEUS REFLECTION ──
      ctx.beginPath()
      ctx.ellipse(
        centerX - baseRadius * 0.28,
        centerY - baseRadius * 0.28,
        baseRadius * 0.28,
        baseRadius * 0.16,
        -Math.PI / 4,
        0,
        Math.PI * 2
      )
      ctx.fillStyle = 'rgba(255, 253, 245, 0.65)'
      ctx.fill()

      // ── 7. FLOWING INTELLIGENCE DUST PARTICLES ──
      particles.forEach((p) => {
        p.angle += p.speed * speedMultiplier
        const px = centerX + Math.cos(p.angle) * p.distance * breath
        const py = centerY + Math.sin(p.angle) * p.distance * breath * 0.85

        ctx.beginPath()
        ctx.arc(px, py, p.size, 0, Math.PI * 2)
        ctx.fillStyle = p.isCore
          ? `rgba(255, 253, 245, ${p.opacity})`
          : currentPalette.primary + `${p.opacity})`
        ctx.fill()
      })

      animationFrameId = requestAnimationFrame(render)
    }

    animationFrameId = requestAnimationFrame(render)

    return () => {
      cancelAnimationFrame(animationFrameId)
    }
  }, [state, size, provider])

  return (
    <div
      onClick={onClick}
      className={`relative inline-flex items-center justify-center cursor-pointer select-none transition-transform duration-300 hover:scale-105 ${className}`}
      style={{ width: size, height: size }}
      title={`FraudLens AI Visual Core • State: ${state.toUpperCase()}`}
    >
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="block"
      />
    </div>
  )
}
