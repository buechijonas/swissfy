<template>
  <span role="img" aria-label="verborgen" class="text-app-muted select-none">
    <span aria-hidden="true">{{ glyphs.join('') }}</span>
  </span>
</template>

<script>
import { useIntervalFn } from '@vueuse/core'
import random from 'lodash-es/random'
import sample from 'lodash-es/sample'
import times from 'lodash-es/times'
import { reducedMotion } from '@/lib/browser.js'

const GLYPHS = Array.from('⏃⏚☊⎅⟒⎎☌⊑⟟⟊☍⌰⋔⋏⍜⌿⍾⍀⌇⏁⎍⎐⍙⌖⊬⋉')
const INTERVAL = 150

export default {
  name: 'CipherText',
  props: {
    length: { type: Number, default: 3 },
  },
  data() {
    return { glyphs: times(this.length, this.randomGlyph) }
  },
  computed: {
    animated() {
      return reducedMotion.value !== 'reduce'
    },
  },
  created() {
    this.shuffler = useIntervalFn(this.shuffle, INTERVAL)
  },
  beforeUnmount() {
    this.shuffler.pause()
  },
  methods: {
    randomGlyph() {
      return sample(GLYPHS)
    },
    shuffle() {
      if (!this.animated) return
      this.glyphs = this.glyphs.with(random(this.glyphs.length - 1), this.randomGlyph())
    },
  },
}
</script>
