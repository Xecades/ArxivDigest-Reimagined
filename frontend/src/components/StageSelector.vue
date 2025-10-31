<script setup lang="ts">
import type { StageFilter } from "@/composables";

interface Props {
    currentStage: StageFilter;
    counts: {
        all: number;
        stage1: number;
        stage2: number;
        stage3: number;
    };
}

interface Emits {
    (e: "change", stage: StageFilter): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const stages: Array<{ value: StageFilter; label: string; key: keyof Props["counts"] }> = [
    { value: "all", label: "All Papers", key: "all" },
    { value: "1", label: "Stage 1+", key: "stage1" },
    { value: "2", label: "Stage 2+", key: "stage2" },
    { value: "3", label: "Stage 3", key: "stage3" },
];

function handleStageChange(stage: StageFilter) {
    emit("change", stage);
}
</script>

<template>
    <div class="bg-gray-50 border-b border-gray-200 py-5 px-6">
        <div class="max-w-7xl mx-auto">
            <div class="flex flex-wrap gap-3 justify-center">
                <button
                    v-for="stage in stages"
                    :key="stage.value"
                    @click="handleStageChange(stage.value)"
                    :class="[
                        'px-5 py-2.5 rounded-full font-semibold text-sm transition-all duration-200',
                        'border-2 border-primary',
                        currentStage === stage.value
                            ? 'bg-primary text-white shadow-lg'
                            : 'bg-white text-primary hover:bg-primary/10',
                    ]"
                >
                    {{ stage.label }} ({{ counts[stage.key] }})
                </button>
            </div>
        </div>
    </div>
</template>
