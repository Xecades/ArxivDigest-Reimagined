<script setup lang="ts">
import { ref, computed } from "vue";
import type { Paper, BaseStageResult, Stage3Result } from "@/types/digest";
import { escapeHtml, formatFieldName } from "@/utils/formatters";
import MarkdownRenderer from "./MarkdownRenderer.vue";

const props = defineProps<{
    paper: Paper;
}>();

const emit = defineEmits<{
    showConversation: [paper: Paper];
}>();

const abstractExpanded = ref(false);

// Stage badges
const stageBadges = computed(() => {
    const badges = [];
    if (props.paper.max_stage >= 1) badges.push({ label: "Stage 1", class: "stage-1" });
    if (props.paper.max_stage >= 2) badges.push({ label: "Stage 2", class: "stage-2" });
    if (props.paper.max_stage >= 3) badges.push({ label: "Stage 3", class: "stage-3" });
    return badges;
});

// Main result to display
const mainResult = computed<BaseStageResult | Stage3Result>(() => {
    if (props.paper.stage3) return props.paper.stage3;
    if (props.paper.stage2) return props.paper.stage2;
    return props.paper.stage1;
});

// Check if stage 3
const isStage3 = computed(() => props.paper.stage3 !== null);

// Check if has abstract (stage 2+)
const hasAbstract = computed(() => props.paper.stage2 !== null || props.paper.stage3 !== null);

// Toggle abstract
function toggleAbstract() {
    abstractExpanded.value = !abstractExpanded.value;
}

// Custom fields for stage 3
const customFields = computed(() => {
    if (isStage3.value && props.paper.stage3?.custom_fields) {
        return Object.entries(props.paper.stage3.custom_fields);
    }
    return [];
});
</script>

<template>
    <div class="paper-card">
        <div class="paper-header">
            <div class="paper-title">
                <a :href="paper.abs_url" target="_blank" v-html="escapeHtml(paper.title)"></a>
            </div>
            <div class="stage-badges">
                <span
                    v-for="badge in stageBadges"
                    :key="badge.label"
                    class="stage-badge"
                    :class="badge.class"
                >
                    {{ badge.label }}
                </span>
            </div>
        </div>

        <div class="paper-meta">
            <div class="authors" :title="paper.authors.join(', ')">
                <strong><FontAwesomeIcon icon="users" class="meta-icon" />Authors:</strong>
                {{ paper.authors.join(", ") }}
            </div>
            <div v-if="paper.categories.length > 0" class="categories">
                <strong><FontAwesomeIcon icon="tags" class="meta-icon" />Categories:</strong>
                <span v-for="cat in paper.categories" :key="cat" class="category-tag">
                    {{ cat }}
                </span>
            </div>
        </div>

        <button
            v-if="hasAbstract"
            class="abstract-toggle"
            :class="{ expanded: abstractExpanded }"
            @click="toggleAbstract"
        >
            <FontAwesomeIcon
                icon="chevron-right"
                class="abstract-toggle-icon"
                :class="{ expanded: abstractExpanded }"
            />
            <span>Abstract</span>
        </button>
        <div v-if="hasAbstract" class="paper-abstract" :class="{ expanded: abstractExpanded }">
            <MarkdownRenderer :content="paper.abstract" :inline="true" />
        </div>

        <div v-if="isStage3 && paper.stage3" class="scores">
            <div class="score-item">
                <span class="score-label">Overall:</span>
                <div class="score-bar">
                    <div
                        class="score-fill"
                        :style="{ width: paper.stage3.score * 100 + '%' }"
                    ></div>
                </div>
                <span class="score-value">{{ paper.stage3.score.toFixed(2) }}</span>
            </div>
            <div class="score-item">
                <span class="score-label">Novelty:</span>
                <div class="score-bar">
                    <div
                        class="score-fill"
                        :style="{ width: paper.stage3.novelty_score * 100 + '%' }"
                    ></div>
                </div>
                <span class="score-value">{{ paper.stage3.novelty_score.toFixed(2) }}</span>
            </div>
            <div class="score-item">
                <span class="score-label">Impact:</span>
                <div class="score-bar">
                    <div
                        class="score-fill"
                        :style="{ width: paper.stage3.impact_score * 100 + '%' }"
                    ></div>
                </div>
                <span class="score-value">{{ paper.stage3.impact_score.toFixed(2) }}</span>
            </div>
            <div class="score-item">
                <span class="score-label">Quality:</span>
                <div class="score-bar">
                    <div
                        class="score-fill"
                        :style="{ width: paper.stage3.quality_score * 100 + '%' }"
                    ></div>
                </div>
                <span class="score-value">{{ paper.stage3.quality_score.toFixed(2) }}</span>
            </div>
        </div>

        <div v-if="mainResult.reasoning" class="reasoning">
            <div class="reasoning-title">Analysis:</div>
            <MarkdownRenderer :content="mainResult.reasoning" class="reasoning-text" />
        </div>

        <div v-if="customFields.length > 0" class="custom-fields">
            <div v-for="[key, value] in customFields" :key="key" class="custom-field">
                <div class="custom-field-title">{{ formatFieldName(key) }}:</div>
                <MarkdownRenderer :content="String(value)" class="custom-field-content" />
            </div>
        </div>

        <button class="conversation-btn" @click="emit('showConversation', paper)">
            <FontAwesomeIcon icon="comments" />
            <span>View LLM Conversations</span>
        </button>
    </div>
</template>

<style scoped>
.meta-icon {
    margin-right: 5px;
    width: 16px;
    line-height: 1em;
    text-align: center;
    color: var(--accent-color);
    vertical-align: middle;
}
</style>
