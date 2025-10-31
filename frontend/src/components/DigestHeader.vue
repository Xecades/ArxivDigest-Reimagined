<script setup lang="ts">
import { computed } from "vue";
import type { Metadata } from "@/types";

interface Props {
    metadata: Metadata;
}

const props = defineProps<Props>();

const formattedDate = computed(() => {
    const date = new Date(props.metadata.timestamp);
    return date.toLocaleString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
});
</script>

<template>
    <header class="bg-gradient-to-r from-primary to-primary-dark text-white py-8 px-6 text-center">
        <h1 class="text-4xl font-bold mb-3">🎓 {{ metadata.title }}</h1>
        <div class="text-white/90 text-sm">Created at {{ formattedDate }}</div>
    </header>
</template>
