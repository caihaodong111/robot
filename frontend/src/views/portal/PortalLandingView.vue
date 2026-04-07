<template>
  <div class="min-h-screen bg-benz-black text-benz-light">
    <div
      class="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_top,rgba(0,255,255,0.1),transparent_25%),radial-gradient(circle_at_bottom_right,rgba(0,113,227,0.18),transparent_30%)]"
      aria-hidden="true"
    ></div>

    <PortalHeader />

    <main class="relative z-10 overflow-x-hidden">
      <HeroSection />
      <Dashboard />
      <PeopleEntry />
    </main>
  </div>
</template>

<script setup>
import PortalHeader from '@/components/portal/PortalHeader.vue'
import HeroSection from '@/components/portal/HeroSection.vue'
import Dashboard from '@/components/portal/Dashboard.vue'
import PeopleEntry from '@/components/portal/PeopleEntry.vue'
</script>
