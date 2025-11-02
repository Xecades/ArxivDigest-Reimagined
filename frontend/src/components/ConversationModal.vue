<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import type { Paper } from "@/types/digest";
import ConversationSection from "./ConversationSection.vue";

const props = defineProps<{ paper: Paper }>();
const emit = defineEmits<{ close: [] }>();

// Handle click outside modal
function handleBackdropClick(e: MouseEvent) {
    if ((e.target as HTMLElement).classList.contains("modal")) {
        emit("close");
    }
}

// Handle escape key
function handleEscape(e: KeyboardEvent) {
    if (e.key === "Escape") {
        emit("close");
    }
}

// Lock body scroll when modal is open
onMounted(() => {
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleEscape);
});

onUnmounted(() => {
    document.body.style.overflow = "";
    window.removeEventListener("keydown", handleEscape);
});
</script>

<template>
    <div class="modal show" @click="handleBackdropClick">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">
                    <FontAwesomeIcon icon="comments" style="margin-right: 10px" />
                    {{ props.paper.title }}
                </div>
                <button class="modal-close" @click="emit('close')">
                    <FontAwesomeIcon icon="times" />
                </button>
            </div>
            <div class="modal-body">
                <!-- Stage 1 -->
                <ConversationSection
                    title="Stage 1: Quick Screening"
                    :score="paper.stage1.score"
                    :pass="paper.stage1.pass"
                    :messages="paper.stage1.messages"
                    :usage="paper.stage1.usage"
                    :estimated-cost="paper.stage1.estimated_cost"
                    :estimated-cost-currency="paper.stage1.estimated_cost_currency"
                    section-id="stage1"
                />

                <!-- Stage 2 -->
                <ConversationSection
                    v-if="paper.stage2"
                    title="Stage 2: Refined Screening"
                    :score="paper.stage2.score"
                    :pass="paper.stage2.pass"
                    :messages="paper.stage2.messages"
                    :usage="paper.stage2.usage"
                    :estimated-cost="paper.stage2.estimated_cost"
                    :estimated-cost-currency="paper.stage2.estimated_cost_currency"
                    section-id="stage2"
                />

                <!-- Stage 3 -->
                <ConversationSection
                    v-if="paper.stage3"
                    title="Stage 3: Deep Analysis"
                    :score="paper.stage3.score"
                    :pass="paper.stage3.pass"
                    :messages="paper.stage3.messages"
                    :usage="paper.stage3.usage"
                    :estimated-cost="paper.stage3.estimated_cost"
                    :estimated-cost-currency="paper.stage3.estimated_cost_currency"
                    section-id="stage3"
                />

                <!-- Highlight (Abstract Highlighting) -->
                <ConversationSection
                    v-if="paper.highlight"
                    title="Abstract Highlighting"
                    :messages="paper.highlight.messages"
                    :usage="paper.highlight.usage"
                    :estimated-cost="paper.highlight.estimated_cost"
                    :estimated-cost-currency="paper.highlight.estimated_cost_currency"
                    section-id="highlight"
                />
            </div>
        </div>
    </div>
</template>
