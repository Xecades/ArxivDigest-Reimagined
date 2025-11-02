<script setup lang="ts">
import { ref } from "vue";
import type { Message, UsageInfo } from "@/types/digest";
import { escapeHtml, formatCost } from "@/utils/formatters";

const props = defineProps<{
    title: string;
    score?: number;
    pass?: boolean;
    messages: Message[];
    usage?: UsageInfo | null;
    estimatedCost?: number | null;
    estimatedCostCurrency?: string | null;
    sectionId: string;
}>();

const collapsedMessages = ref<Set<string>>(new Set());

// Toggle message collapse
function toggleMessage(msgId: string) {
    if (collapsedMessages.value.has(msgId)) {
        collapsedMessages.value.delete(msgId);
    } else {
        collapsedMessages.value.add(msgId);
    }
}

// Render usage info
function renderUsage(): string {
    if (!props.usage) return "";

    const p =
        props.usage.prompt_tokens != null ? props.usage.prompt_tokens.toLocaleString() : "N/A";
    const c =
        props.usage.completion_tokens != null
            ? props.usage.completion_tokens.toLocaleString()
            : "N/A";
    const t = props.usage.total_tokens != null ? props.usage.total_tokens.toLocaleString() : "N/A";
    const costText =
        props.estimatedCost != null
            ? props.estimatedCost === 0
                ? "0.000000"
                : formatCost(props.estimatedCost)
            : "N/A";
    const costWithCurrency =
        costText === "N/A"
            ? "N/A"
            : props.estimatedCostCurrency
              ? `${props.estimatedCostCurrency} ${costText}`
              : costText;

    return `Tokens: ${p} + ${c} = ${t} · Cost: ${costWithCurrency}`;
}

// Format message content
function formatMessageContent(msg: Message): string {
    if (msg.role === "assistant") {
        return `<pre>${escapeHtml(msg.content)}</pre>`;
    }
    return escapeHtml(msg.content);
}
</script>

<template>
    <div v-if="messages && messages.length > 0" class="conversation-section">
        <div class="stage-header">
            <span>{{ title }}</span>
            <span v-if="score !== undefined" class="stage-score">
                Score: {{ score.toFixed(2) }}
                <FontAwesomeIcon
                    :icon="pass ? 'check' : 'xmark'"
                    :style="{ color: pass ? '#56ec78' : '#ff5757' }"
                />
            </span>
        </div>
        <div v-if="usage" class="usage-info" v-html="renderUsage()"></div>
        <div
            v-for="(msg, index) in messages"
            :key="`${sectionId}-${index}`"
            class="message"
            :class="`message-${msg.role}`"
        >
            <div class="message-role">
                <span>{{ msg.role.charAt(0).toUpperCase() + msg.role.slice(1) }}</span>
                <span
                    class="message-toggle"
                    :class="{
                        collapsed: collapsedMessages.has(`${sectionId}-${index}`),
                    }"
                    @click="toggleMessage(`${sectionId}-${index}`)"
                >
                    <FontAwesomeIcon icon="chevron-down" />
                </span>
            </div>
            <div
                class="message-content-wrapper"
                :class="{
                    collapsed: collapsedMessages.has(`${sectionId}-${index}`),
                }"
            >
                <div class="message-content" v-html="formatMessageContent(msg)"></div>
            </div>
        </div>
    </div>
</template>
