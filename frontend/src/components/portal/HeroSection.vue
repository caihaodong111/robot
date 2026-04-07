<template>
  <section id="hero" ref="heroContainer" class="relative h-screen min-h-[720px] overflow-hidden bg-benz-black">
    <img
      ref="heroImage"
      :src="heroImageUrl"
      alt="Benz Robotics Factory"
      class="absolute inset-0 h-full w-full object-cover object-center opacity-60"
    />

    <div
      ref="heroCard"
      class="relative flex h-full w-full flex-col items-center justify-center overflow-hidden bg-benz-black/45 px-6 pb-8 pt-28 text-center backdrop-blur-sm sm:pt-32 lg:pt-36"
    >
      <div
        class="absolute inset-0 bg-portal-grid bg-[size:38px_38px] opacity-[0.08]"
        aria-hidden="true"
      ></div>
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(0,255,255,0.16),transparent_34%),radial-gradient(circle_at_bottom,rgba(0,113,227,0.28),transparent_38%)]" aria-hidden="true"></div>
      <div
        ref="heroBorder"
        class="pointer-events-none absolute inset-0 rounded-[inherit] border border-white/10 opacity-0 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]"
      ></div>

      <div class="relative z-10 mt-4 max-w-5xl space-y-4 sm:mt-6 sm:space-y-5 lg:mt-8">
        <p
          data-hero-reveal
          class="text-xs font-semibold uppercase tracking-[0.34em] text-benz-cyan sm:text-sm"
        >
          Intelligent Manufacturing Portal
        </p>
        <h1
          data-hero-reveal
          class="text-4xl font-semibold leading-[0.9] tracking-[-0.06em] text-white sm:text-5xl lg:text-[6.25rem]"
        >
          智造驱动，
          <br />
          <span class="text-white/[0.62]">未来已来</span>
        </h1>
      </div>

      <div
        class="absolute bottom-6 left-1/2 z-10 flex -translate-x-1/2 flex-col items-center gap-2 text-benz-gray sm:bottom-8"
      >
        <span class="text-xs font-semibold uppercase tracking-[0.24em]">向下滚动</span>
        <div class="h-10 w-px bg-gradient-to-b from-benz-gray to-transparent sm:h-12"></div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const heroContainer = ref(null)
const heroCard = ref(null)
const heroImage = ref(null)
const heroBorder = ref(null)
const heroImageUrl = `${import.meta.env.BASE_URL}portal-hero-bg.jpg`
let ctx

onMounted(() => {
  ctx = gsap.context(() => {
    const revealTargets = heroContainer.value?.querySelectorAll('[data-hero-reveal]')

    gsap.from(revealTargets, {
      y: 36,
      opacity: 0,
      duration: 1.15,
      stagger: 0.12,
      ease: 'power3.out',
      delay: 0.2
    })

    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: heroContainer.value,
        start: 'top top',
        end: '+=140%',
        scrub: 1,
        pin: true,
        anticipatePin: 1
      }
    })

    timeline.to(
      heroCard.value,
      {
        width: '92%',
        height: '86%',
        borderRadius: 42,
        y: '6vh',
        backgroundColor: '#1D1D1F',
        ease: 'none'
      },
      0
    )

    timeline.to(
      heroImage.value,
      {
        scale: 1.08,
        opacity: 0.34,
        ease: 'none'
      },
      0
    )

    timeline.to(
      heroBorder.value,
      {
        opacity: 1,
        ease: 'none'
      },
      0.45
    )
  }, heroContainer.value)

  requestAnimationFrame(() => {
    ScrollTrigger.refresh()
  })
})

onUnmounted(() => {
  ctx?.revert()
})
</script>
