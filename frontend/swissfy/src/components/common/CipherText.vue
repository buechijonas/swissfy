<template>
  <span role="img" aria-label="verborgen" class="text-swissfy-muted select-none">
    <span aria-hidden="true">{{ glyphs.join('') }}</span>
  </span>
</template>

<script>
const GLYPHS = Array.from('⏃⏚☊⎅⟒⎎☌⊑⟟⟊☍⌰⋔⋏⍜⌿⍾⍀⌇⏁⎍⎐⍙⌖⊬⋉')
const INTERVAL = 150

function randomGlyph() {
  return GLYPHS[Math.floor(Math.random() * GLYPHS.length)]
}

function scramble(length) {
  return Array.from({ length }, randomGlyph)
}

function shuffleOne(glyphs) {
  const index = Math.floor(Math.random() * glyphs.length)
  return glyphs.with(index, randomGlyph())
}

export default {
  name: 'CipherText',
  props: {
    length: { type: Number, default: 3 },
  },
  data() {
    return { glyphs: scramble(this.length) }
  },
  mounted() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    this.timer = setInterval(() => (this.glyphs = shuffleOne(this.glyphs)), INTERVAL)
  },
  beforeUnmount() {
    clearInterval(this.timer)
  },
}
</script>
