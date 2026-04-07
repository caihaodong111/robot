import { onUnmounted } from 'vue'

export function useMouseMoveGlow() {
  const cleanups = new Map()

  const bindGlow = (el) => {
    if (!el || cleanups.has(el)) {
      return
    }

    const updateGlow = ({ clientX, clientY }) => {
      const { left, top, width, height } = el.getBoundingClientRect()
      const x = ((clientX - left) / width) * 100
      const y = ((clientY - top) / height) * 100

      el.style.setProperty('--glow-x', `${x}%`)
      el.style.setProperty('--glow-y', `${y}%`)
    }

    const resetGlow = () => {
      el.style.setProperty('--glow-x', '50%')
      el.style.setProperty('--glow-y', '50%')
    }

    el.addEventListener('mousemove', updateGlow)
    el.addEventListener('mouseleave', resetGlow)

    cleanups.set(el, () => {
      el.removeEventListener('mousemove', updateGlow)
      el.removeEventListener('mouseleave', resetGlow)
    })
  }

  onUnmounted(() => {
    cleanups.forEach((cleanup) => cleanup())
    cleanups.clear()
  })

  return { bindGlow }
}
