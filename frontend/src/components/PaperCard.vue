<script setup lang="ts">
import { ref, computed } from "vue";
import type { Paper } from "@/types";
import { ChevronRightIcon } from "@heroicons/vue/24/solid";

interface Props {
    paper: Paper;
}

interface Emits {
    (e: "view-conversation", paperId: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const showAbstract = ref(false);

const stageBadges = computed(() => {
    const badges = [];
    if (props.paper.max_stage >= 1)
        badges.push({ stage: 1, label: "Stage 1", color: "bg-green-100 text-green-800" });
    if (props.paper.max_stage >= 2)
        badges.push({ stage: 2, label: "Stage 2", color: "bg-blue-100 text-blue-800" });
    if (props.paper.max_stage >= 3)
        badges.push({ stage: 3, label: "Stage 3", color: "bg-red-100 text-red-800" });
    return badges;
});

const mainResult = computed(() => {
    if (props.paper.stage3) return props.paper.stage3;
    if (props.paper.stage2) return props.paper.stage2;
    return props.paper.stage1;
});

const showScores = computed(() => props.paper.stage3 !== null);

const showCustomFields = computed(() => {
    return (
        props.paper.stage3?.custom_fields &&
        Object.keys(props.paper.stage3.custom_fields).length > 0
    );
});

function toggleAbstract() {
    showAbstract.value = !showAbstract.value;
}

function formatFieldName(name: string): string {
    return name
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

function handleViewConversation() {
    emit("view-conversation", props.paper.arxiv_id);
}
</script>

<template>
    <div
        class="bg-white border border-gray-200 rounded-lg p-6 mb-5 transition-all duration-200 hover:shadow-lg hover:-translate-y-1"
    >
        <!-- Header -->
        <div class="flex justify-between items-start gap-4 mb-4">
            <h2 class="text-xl font-semibold text-gray-900 flex-1">
                <a
                    :href="paper.abs_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="hover:text-primary transition-colors"
                >
                    {{ paper.title }}
                </a>
            </h2>
            <div class="flex gap-2 flex-shrink-0">
                <span
                    v-for="badge in stageBadges"
                    :key="badge.stage"
                    :class="['px-3 py-1 rounded-full text-xs font-semibold', badge.color]"
                >
                    {{ badge.label }}
                </span>
            </div>
        </div>

        <!-- Meta -->
        <div class="text-sm text-gray-600 mb-4">
            <div class="mb-2"><strong>Authors:</strong> {{ paper.authors.join(", ") }}</div>
            <div class="flex flex-wrap gap-2">
                <strong>Categories:</strong>
                <span
                    v-for="category in paper.categories"
                    :key="category"
                    class="bg-gray-100 px-2 py-1 rounded text-xs"
                >
                    {{ category }}
                </span>
            </div>
        </div>

        <!-- Abstract Toggle (if stage 2+) -->
        <div v-if="paper.stage2 || paper.stage3" class="mb-4">
            <button
                @click="toggleAbstract"
                class="flex items-center gap-2 text-primary font-semibold text-sm hover:text-primary-dark transition-colors"
            >
                <ChevronRightIcon
                    :class="['w-4 h-4 transition-transform', showAbstract && 'rotate-90']"
                />
                <span>Abstract</span>
            </button>
            <div v-show="showAbstract" class="mt-3 text-gray-700 leading-relaxed animate-fade-in">
                {{ paper.abstract }}
            </div>
        </div>

        <!-- Scores (Stage 3) -->
        <div v-if="showScores && paper.stage3" class="mb-4 flex flex-wrap gap-4">
            <div
                v-for="(score, label) in {
                    Overall: paper.stage3.score,
                    Novelty: paper.stage3.novelty_score,
                    Impact: paper.stage3.impact_score,
                    Quality: paper.stage3.quality_score,
                }"
                :key="label"
                class="flex items-center gap-2"
            >
                <span class="font-semibold text-gray-600 text-sm">{{ label }}:</span>
                <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        class="h-full bg-gradient-to-r from-primary to-primary-dark"
                        :style="{ width: `${score * 100}%` }"
                    ></div>
                </div>
                <span class="font-bold text-primary text-sm">{{ score.toFixed(2) }}</span>
            </div>
        </div>

        <!-- Reasoning -->
        <div
            v-if="mainResult.reasoning"
            class="mb-4 bg-gray-50 border-l-4 border-primary p-4 rounded"
        >
            <div class="font-semibold text-primary mb-2">Analysis:</div>
            <div class="text-gray-700 leading-relaxed">{{ mainResult.reasoning }}</div>
        </div>

        <!-- Custom Fields (Stage 3) -->
        <div v-if="showCustomFields && paper.stage3" class="mb-4">
            <div v-for="(value, key) in paper.stage3.custom_fields" :key="key" class="mb-3">
                <div class="font-semibold text-primary text-sm mb-1">
                    {{ formatFieldName(key) }}:
                </div>
                <div class="text-gray-700 leading-relaxed">{{ value }}</div>
            </div>
        </div>

        <!-- View Conversation Button -->
        <button
            @click="handleViewConversation"
            class="bg-gradient-to-r from-primary to-primary-dark text-white px-4 py-2 rounded-full text-sm font-semibold hover:shadow-lg transition-all duration-200 flex items-center gap-2"
        >
            <span>💬</span>
            <span>View LLM Conversations</span>
        </button>
    </div>
</template>
