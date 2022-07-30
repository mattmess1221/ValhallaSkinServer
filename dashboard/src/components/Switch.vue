<script setup lang="ts">
defineProps<{ value: string }>();
</script>

<template>
  <div>
    <slot :name="value"></slot>
  </div>
</template>
