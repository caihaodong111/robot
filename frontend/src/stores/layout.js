import { defineStore } from 'pinia'

export const useLayoutStore = defineStore('layout', {
  state: () => ({
    isCollapsed: false
  }),

  actions: {
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
    },
    setCollapsed(collapsed) {
      this.isCollapsed = collapsed
    }
  }
})
