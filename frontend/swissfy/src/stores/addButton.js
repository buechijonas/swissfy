import { defineStore } from 'pinia'
import { shallowRef } from 'vue'

export const useAddButtonStore = defineStore('addButton', () => {
  const action = shallowRef(null)

  function show(owner, config) {
    action.value = { owner, ...config }
  }

  function hide(owner) {
    if (action.value?.owner === owner) action.value = null
  }

  return { action, show, hide }
})
