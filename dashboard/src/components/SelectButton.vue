<script setup lang="ts">
import { ref } from "vue";
type Option = string;
type Options = Option[] | Record<any, Option>;

interface Props {
  options: Options;
  value: string;
}

interface Emits {
  (event: "update:value", value: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const value = ref<string>(props.value);

function setValue(_value: string) {
  value.value = _value;
  emit("update:value", _value);
}
</script>

<template>
  <div>
    <button
      v-for="option in options"
      :key="option"
      class="button-select-option"
      :disabled="value === option"
      @click="setValue(option)"
    >
      {{ option }}
    </button>
  </div>
</template>
