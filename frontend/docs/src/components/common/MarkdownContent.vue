<template>
  <div class="markdown" v-html="html"></div>
</template>

<script>
export default {
  name: 'MarkdownContent',
  props: {
    html: { type: String, default: '' },
  },
}
</script>
