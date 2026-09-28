/**
 * Web Audio API synthesizer for cinematic sci-fi command center feedback.
 * Completely standalone, no external mp3s/wavs required.
 * Gracefully handles browser autoplay policies and muted states.
 */

class SoundEffectsEngine {
  constructor() {
    this.ctx = null
    this.isMuted = typeof window !== 'undefined' && localStorage.getItem('fraudlens_sound_muted') === 'true'
  }

  _getAudioContext() {
    if (this.isMuted || typeof window === 'undefined') return null
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) return null
      if (!this.ctx) {
        this.ctx = new AudioCtx()
      }
      if (this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {})
      }
      return this.ctx
    } catch {
      return null
    }
  }

  toggleMute() {
    this.isMuted = !this.isMuted
    if (typeof window !== 'undefined') {
      localStorage.setItem('fraudlens_sound_muted', String(this.isMuted))
    }
    return this.isMuted
  }

  getMuted() {
    return this.isMuted
  }

  /** Subtle tactical blip on button hover or click */
  playBlip() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.setValueAtTime(820, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(1240, ctx.currentTime + 0.05)

      gain.gain.setValueAtTime(0.04, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start()
      osc.stop(ctx.currentTime + 0.05)
    } catch {
      // Audio failure ignored
    }
  }

  /** Error buzzer on invalid credentials */
  playError() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sawtooth'
      osc.frequency.setValueAtTime(140, ctx.currentTime)
      osc.frequency.setValueAtTime(110, ctx.currentTime + 0.1)

      gain.gain.setValueAtTime(0.08, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start()
      osc.stop(ctx.currentTime + 0.25)
    } catch {
      // Audio failure ignored
    }
  }

  /** Access verified harmonic chord */
  playVerified() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      const freqs = [440, 659.25, 880]
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()

        osc.type = 'sine'
        osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.08)
        osc.frequency.exponentialRampToValueAtTime(freq * 1.5, ctx.currentTime + idx * 0.08 + 0.3)

        gain.gain.setValueAtTime(0.06, ctx.currentTime + idx * 0.08)
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.08 + 0.4)

        osc.connect(gain)
        gain.connect(ctx.destination)

        osc.start(ctx.currentTime + idx * 0.08)
        osc.stop(ctx.currentTime + idx * 0.08 + 0.4)
      })
    } catch {
      // Audio failure ignored
    }
  }

  /** Shield unlock metallic laser release */
  playUnlock() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'triangle'
      osc.frequency.setValueAtTime(320, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(1760, ctx.currentTime + 0.22)

      gain.gain.setValueAtTime(0.08, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start()
      osc.stop(ctx.currentTime + 0.3)
    } catch {
      // Audio failure ignored
    }
  }

  /** Deep energy pulse shockwave */
  playShockwave() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.setValueAtTime(160, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(38, ctx.currentTime + 0.6)

      gain.gain.setValueAtTime(0.15, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.7)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start()
      osc.stop(ctx.currentTime + 0.7)
    } catch {
      // Audio failure ignored
    }
  }

  /** Subtle laser radar scan pass across the security door */
  playDoorScan() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.setValueAtTime(520, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(1400, ctx.currentTime + 0.18)

      gain.gain.setValueAtTime(0.035, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start()
      osc.stop(ctx.currentTime + 0.2)
    } catch {
      // Audio failure ignored
    }
  }

  /** Satisfying crisp digital vault latch lock clamp */
  playVaultLock() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      // Primary metallic lock click
      const osc1 = ctx.createOscillator()
      const gain1 = ctx.createGain()

      osc1.type = 'triangle'
      osc1.frequency.setValueAtTime(280, ctx.currentTime)
      osc1.frequency.exponentialRampToValueAtTime(75, ctx.currentTime + 0.12)

      gain1.gain.setValueAtTime(0.09, ctx.currentTime)
      gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15)

      osc1.connect(gain1)
      gain1.connect(ctx.destination)

      osc1.start()
      osc1.stop(ctx.currentTime + 0.15)

      // Secondary magnetic seal hum
      const osc2 = ctx.createOscillator()
      const gain2 = ctx.createGain()

      osc2.type = 'sine'
      osc2.frequency.setValueAtTime(110, ctx.currentTime + 0.05)
      osc2.frequency.exponentialRampToValueAtTime(55, ctx.currentTime + 0.3)

      gain2.gain.setValueAtTime(0.06, ctx.currentTime + 0.05)
      gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35)

      osc2.connect(gain2)
      gain2.connect(ctx.destination)

      osc2.start(ctx.currentTime + 0.05)
      osc2.stop(ctx.currentTime + 0.35)
    } catch {
      // Audio failure ignored
    }
  }

  /** Soft harmonic session sealed chord */
  playSecureExit() {
    const ctx = this._getAudioContext()
    if (!ctx) return
    try {
      const freqs = [587.33, 440, 329.63] // Descending harmonic triad (D5 -> A4 -> E4)
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()

        osc.type = 'sine'
        osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.09)
        osc.frequency.exponentialRampToValueAtTime(freq * 0.9, ctx.currentTime + idx * 0.09 + 0.3)

        gain.gain.setValueAtTime(0.045, ctx.currentTime + idx * 0.09)
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.09 + 0.35)

        osc.connect(gain)
        gain.connect(ctx.destination)

        osc.start(ctx.currentTime + idx * 0.09)
        osc.stop(ctx.currentTime + idx * 0.09 + 0.35)
      })
    } catch {
      // Audio failure ignored
    }
  }
}

export const sound = new SoundEffectsEngine()
