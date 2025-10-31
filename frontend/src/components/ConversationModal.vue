<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import type { Paper, Message, UsageInfo } from "@/types/digest";
import { escapeHtml, formatCost } from "@/utils/formatters";

const props = defineProps<{
    paper: Paper;
}>();

const emit = defineEmits<{
    close: [];
}>();

const collapsedMessages = ref<Set<string>>(new Set());

// Format title for modal
const modalTitle = computed(() => {
    const title = props.paper.title;
    return title.length > 60 ? title.substring(0, 60) + "..." : title;
});

// Toggle message collapse
function toggleMessage(msgId: string) {
    if (collapsedMessages.value.has(msgId)) {
        collapsedMessages.value.delete(msgId);
    } else {
        collapsedMessages.value.add(msgId);
    }
}

// Render usage info
function renderUsage(
    usage: UsageInfo,
    estimatedCost: number | null | undefined,
    currency: string | null | undefined,
): string {
    if (!usage) return "";

    const p = usage.prompt_tokens != null ? usage.prompt_tokens.toLocaleString() : "N/A";
    const c = usage.completion_tokens != null ? usage.completion_tokens.toLocaleString() : "N/A";
    const t = usage.total_tokens != null ? usage.total_tokens.toLocaleString() : "N/A";
    const costText =
        estimatedCost != null
            ? estimatedCost === 0
                ? "0.000000"
                : formatCost(estimatedCost)
            : "N/A";
    const costWithCurrency =
        costText === "N/A" ? "N/A" : currency ? `${currency} ${costText}` : costText;

    return `Tokens: ${p} + ${c} = ${t} · Cost: ${costWithCurrency}`;
}

// Format message content
function formatMessageContent(msg: Message): string {
    if (msg.role === "assistant") {
        return `<pre style="margin: 0; white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 0.9em;">${escapeHtml(msg.content)}</pre>`;
    }
    return escapeHtml(msg.content);
}

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
                    LLM Conversations - {{ modalTitle }}
                </div>
                <button class="modal-close" @click="emit('close')">
                    <FontAwesomeIcon icon="times" />
                </button>
            </div>
            <div class="modal-body">
                <!-- Stage 1 -->
                <div
                    v-if="paper.stage1.messages && paper.stage1.messages.length > 0"
                    class="conversation-section"
                >
                    <div class="stage-header">
                        <span>Stage 1: Quick Screening</span>
                        <span class="stage-score">
                            Score: {{ paper.stage1.score.toFixed(2) }}
                            {{ paper.stage1.pass ? "✅" : "❌" }}
                        </span>
                    </div>
                    <div
                        v-if="paper.stage1.usage"
                        class="usage-info"
                        v-html="
                            renderUsage(
                                paper.stage1.usage,
                                paper.stage1.estimated_cost,
                                paper.stage1.estimated_cost_currency,
                            )
                        "
                    ></div>
                    <div
                        v-for="(msg, index) in paper.stage1.messages"
                        :key="`stage1-${index}`"
                        class="message"
                        :class="`message-${msg.role}`"
                    >
                        <div class="message-role">
                            <span>{{ msg.role.charAt(0).toUpperCase() + msg.role.slice(1) }}</span>
                            <span
                                class="message-toggle"
                                :class="{
                                    collapsed: collapsedMessages.has(`stage1-${index}`),
                                }"
                                @click="toggleMessage(`stage1-${index}`)"
                            >
                                <FontAwesomeIcon icon="chevron-down" />
                            </span>
                        </div>
                        <div
                            class="message-content-wrapper"
                            :class="{
                                collapsed: collapsedMessages.has(`stage1-${index}`),
                            }"
                        >
                            <div class="message-content" v-html="formatMessageContent(msg)"></div>
                        </div>
                    </div>
                </div>

                <!-- Stage 2 -->
                <div
                    v-if="paper.stage2 && paper.stage2.messages && paper.stage2.messages.length > 0"
                    class="conversation-section"
                >
                    <div class="stage-header">
                        <span>Stage 2: Refined Screening</span>
                        <span class="stage-score">
                            Score: {{ paper.stage2.score.toFixed(2) }}
                            {{ paper.stage2.pass ? "✅" : "❌" }}
                        </span>
                    </div>
                    <div
                        v-if="paper.stage2.usage"
                        class="usage-info"
                        v-html="
                            renderUsage(
                                paper.stage2.usage,
                                paper.stage2.estimated_cost,
                                paper.stage2.estimated_cost_currency,
                            )
                        "
                    ></div>
                    <div
                        v-for="(msg, index) in paper.stage2.messages"
                        :key="`stage2-${index}`"
                        class="message"
                        :class="`message-${msg.role}`"
                    >
                        <div class="message-role">
                            <span>{{ msg.role.charAt(0).toUpperCase() + msg.role.slice(1) }}</span>
                            <span
                                class="message-toggle"
                                :class="{
                                    collapsed: collapsedMessages.has(`stage2-${index}`),
                                }"
                                @click="toggleMessage(`stage2-${index}`)"
                            >
                                <FontAwesomeIcon icon="chevron-down" />
                            </span>
                        </div>
                        <div
                            class="message-content-wrapper"
                            :class="{
                                collapsed: collapsedMessages.has(`stage2-${index}`),
                            }"
                        >
                            <div class="message-content" v-html="formatMessageContent(msg)"></div>
                        </div>
                    </div>
                </div>

                <!-- Stage 3 -->
                <div
                    v-if="paper.stage3 && paper.stage3.messages && paper.stage3.messages.length > 0"
                    class="conversation-section"
                >
                    <div class="stage-header">
                        <span>Stage 3: Deep Analysis</span>
                        <span class="stage-score">
                            Score: {{ paper.stage3.score.toFixed(2) }}
                            {{ paper.stage3.pass ? "✅" : "❌" }}
                        </span>
                    </div>
                    <div
                        v-if="paper.stage3.usage"
                        class="usage-info"
                        v-html="
                            renderUsage(
                                paper.stage3.usage,
                                paper.stage3.estimated_cost,
                                paper.stage3.estimated_cost_currency,
                            )
                        "
                    ></div>
                    <div
                        v-for="(msg, index) in paper.stage3.messages"
                        :key="`stage3-${index}`"
                        class="message"
                        :class="`message-${msg.role}`"
                    >
                        <div class="message-role">
                            <span>{{ msg.role.charAt(0).toUpperCase() + msg.role.slice(1) }}</span>
                            <span
                                class="message-toggle"
                                :class="{
                                    collapsed: collapsedMessages.has(`stage3-${index}`),
                                }"
                                @click="toggleMessage(`stage3-${index}`)"
                            >
                                <FontAwesomeIcon icon="chevron-down" />
                            </span>
                        </div>
                        <div
                            class="message-content-wrapper"
                            :class="{
                                collapsed: collapsedMessages.has(`stage3-${index}`),
                            }"
                        >
                            <div class="message-content" v-html="formatMessageContent(msg)"></div>
                        </div>
                    </div>
                </div>

                <!-- No conversation data -->
                <p
                    v-if="
                        (!paper.stage1.messages || paper.stage1.messages.length === 0) &&
                        (!paper.stage2 ||
                            !paper.stage2.messages ||
                            paper.stage2.messages.length === 0) &&
                        (!paper.stage3 ||
                            !paper.stage3.messages ||
                            paper.stage3.messages.length === 0)
                    "
                    style="text-align: center; color: #999; padding: 40px"
                >
                    No conversation data available (all results from cache)
                </p>
            </div>
        </div>
    </div>
</template>
