<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { TransitionRoot, TransitionChild, Dialog, DialogPanel, DialogTitle } from "@headlessui/vue";
import { XMarkIcon, ChevronDownIcon } from "@heroicons/vue/24/solid";
import type { Paper } from "@/types";

interface Props {
    paper: Paper | null;
    show: boolean;
}

interface Emits {
    (e: "close"): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const collapsedMessages = ref<Set<string>>(new Set());

const title = computed(() => {
    if (!props.paper) return "";
    return props.paper.title.length > 60
        ? props.paper.title.substring(0, 60) + "..."
        : props.paper.title;
});

function closeModal() {
    emit("close");
}

function toggleMessage(messageId: string) {
    if (collapsedMessages.value.has(messageId)) {
        collapsedMessages.value.delete(messageId);
    } else {
        collapsedMessages.value.add(messageId);
    }
}

function isMessageCollapsed(messageId: string): boolean {
    return collapsedMessages.value.has(messageId);
}

function formatUsage(
    usage: unknown,
    cost: number | null | undefined,
    currency: string | null | undefined,
): string {
    if (!usage || typeof usage !== "object") return "";

    const u = usage as {
        prompt_tokens?: number | null;
        completion_tokens?: number | null;
        total_tokens?: number | null;
    };

    const p = u.prompt_tokens != null ? u.prompt_tokens.toLocaleString() : "N/A";
    const c = u.completion_tokens != null ? u.completion_tokens.toLocaleString() : "N/A";
    const t = u.total_tokens != null ? u.total_tokens.toLocaleString() : "N/A";
    const costText = cost != null ? (cost === 0 ? "0.000000" : cost.toFixed(6)) : "N/A";
    const costWithCurrency =
        costText === "N/A" ? "N/A" : currency ? `${currency} ${costText}` : costText;

    return `Tokens: ${p} + ${c} = ${t} · Cost: ${costWithCurrency}`;
}

// Reset collapsed messages when paper changes
watch(
    () => props.paper,
    () => {
        collapsedMessages.value.clear();
    },
);
</script>

<template>
    <TransitionRoot appear :show="show" as="template">
        <Dialog as="div" @close="closeModal" class="relative z-50">
            <TransitionChild
                as="template"
                enter="duration-300 ease-out"
                enter-from="opacity-0"
                enter-to="opacity-100"
                leave="duration-200 ease-in"
                leave-from="opacity-100"
                leave-to="opacity-0"
            >
                <div class="fixed inset-0 bg-black/50" />
            </TransitionChild>

            <div class="fixed inset-0 overflow-y-auto">
                <div class="flex min-h-full items-center justify-center p-4">
                    <TransitionChild
                        as="template"
                        enter="duration-300 ease-out"
                        enter-from="opacity-0 scale-95"
                        enter-to="opacity-100 scale-100"
                        leave="duration-200 ease-in"
                        leave-from="opacity-100 scale-100"
                        leave-to="opacity-0 scale-95"
                    >
                        <DialogPanel
                            class="w-full max-w-4xl transform overflow-hidden rounded-lg bg-white shadow-xl transition-all"
                        >
                            <!-- Header -->
                            <div
                                class="bg-gradient-to-r from-primary to-primary-dark text-white px-6 py-5 flex justify-between items-center"
                            >
                                <DialogTitle class="text-lg font-semibold">
                                    LLM Conversations - {{ title }}
                                </DialogTitle>
                                <button
                                    @click="closeModal"
                                    class="w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
                                >
                                    <XMarkIcon class="w-6 h-6" />
                                </button>
                            </div>

                            <!-- Body -->
                            <div class="p-6 max-h-[70vh] overflow-y-auto">
                                <div v-if="!paper" class="text-center text-gray-500 py-10">
                                    No paper selected
                                </div>
                                <div v-else>
                                    <!-- Stage 1 -->
                                    <div v-if="paper.stage1?.messages?.length" class="mb-6">
                                        <div
                                            class="bg-gradient-to-r from-primary to-primary-dark text-white px-4 py-2 rounded-lg mb-4 flex justify-between items-center"
                                        >
                                            <span class="font-semibold"
                                                >Stage 1: Quick Screening</span
                                            >
                                            <span class="text-lg">
                                                Score: {{ paper.stage1.score.toFixed(2) }}
                                                {{ paper.stage1.pass ? "✅" : "❌" }}
                                            </span>
                                        </div>
                                        <div
                                            v-if="paper.stage1.usage"
                                            class="text-sm text-gray-600 mb-3 px-3 py-2 bg-gray-50 rounded border-l-3 border-primary"
                                        >
                                            {{
                                                formatUsage(
                                                    paper.stage1.usage,
                                                    paper.stage1.estimated_cost,
                                                    paper.stage1.estimated_cost_currency,
                                                )
                                            }}
                                        </div>
                                        <div
                                            v-for="(msg, idx) in paper.stage1.messages"
                                            :key="`stage1-${idx}`"
                                            :class="[
                                                'mb-4 p-4 rounded-lg border-l-4',
                                                msg.role === 'user' && 'bg-blue-50 border-primary',
                                                msg.role === 'assistant' &&
                                                    'bg-gray-50 border-primary-dark',
                                                msg.role === 'system' &&
                                                    'bg-yellow-50 border-yellow-400',
                                            ]"
                                        >
                                            <div class="flex justify-between items-center mb-2">
                                                <span
                                                    class="font-semibold text-sm uppercase tracking-wide"
                                                    :class="[
                                                        msg.role === 'user' && 'text-primary',
                                                        msg.role === 'assistant' &&
                                                            'text-primary-dark',
                                                        msg.role === 'system' && 'text-yellow-600',
                                                    ]"
                                                >
                                                    {{ msg.role }}
                                                </span>
                                                <button
                                                    @click="toggleMessage(`stage1-${idx}`)"
                                                    class="text-gray-500 hover:text-gray-700"
                                                >
                                                    <ChevronDownIcon
                                                        :class="[
                                                            'w-5 h-5 transition-transform',
                                                            isMessageCollapsed(`stage1-${idx}`) &&
                                                                '-rotate-90',
                                                        ]"
                                                    />
                                                </button>
                                            </div>
                                            <div
                                                v-show="!isMessageCollapsed(`stage1-${idx}`)"
                                                class="text-gray-700 whitespace-pre-wrap leading-relaxed text-sm"
                                            >
                                                {{ msg.content }}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Stage 2 -->
                                    <div v-if="paper.stage2?.messages?.length" class="mb-6">
                                        <div
                                            class="bg-gradient-to-r from-primary to-primary-dark text-white px-4 py-2 rounded-lg mb-4 flex justify-between items-center"
                                        >
                                            <span class="font-semibold"
                                                >Stage 2: Refined Screening</span
                                            >
                                            <span class="text-lg">
                                                Score: {{ paper.stage2.score.toFixed(2) }}
                                                {{ paper.stage2.pass ? "✅" : "❌" }}
                                            </span>
                                        </div>
                                        <div
                                            v-if="paper.stage2.usage"
                                            class="text-sm text-gray-600 mb-3 px-3 py-2 bg-gray-50 rounded border-l-3 border-primary"
                                        >
                                            {{
                                                formatUsage(
                                                    paper.stage2.usage,
                                                    paper.stage2.estimated_cost,
                                                    paper.stage2.estimated_cost_currency,
                                                )
                                            }}
                                        </div>
                                        <div
                                            v-for="(msg, idx) in paper.stage2.messages"
                                            :key="`stage2-${idx}`"
                                            :class="[
                                                'mb-4 p-4 rounded-lg border-l-4',
                                                msg.role === 'user' && 'bg-blue-50 border-primary',
                                                msg.role === 'assistant' &&
                                                    'bg-gray-50 border-primary-dark',
                                                msg.role === 'system' &&
                                                    'bg-yellow-50 border-yellow-400',
                                            ]"
                                        >
                                            <div class="flex justify-between items-center mb-2">
                                                <span
                                                    class="font-semibold text-sm uppercase tracking-wide"
                                                    :class="[
                                                        msg.role === 'user' && 'text-primary',
                                                        msg.role === 'assistant' &&
                                                            'text-primary-dark',
                                                        msg.role === 'system' && 'text-yellow-600',
                                                    ]"
                                                >
                                                    {{ msg.role }}
                                                </span>
                                                <button
                                                    @click="toggleMessage(`stage2-${idx}`)"
                                                    class="text-gray-500 hover:text-gray-700"
                                                >
                                                    <ChevronDownIcon
                                                        :class="[
                                                            'w-5 h-5 transition-transform',
                                                            isMessageCollapsed(`stage2-${idx}`) &&
                                                                '-rotate-90',
                                                        ]"
                                                    />
                                                </button>
                                            </div>
                                            <div
                                                v-show="!isMessageCollapsed(`stage2-${idx}`)"
                                                class="text-gray-700 whitespace-pre-wrap leading-relaxed text-sm"
                                            >
                                                {{ msg.content }}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Stage 3 -->
                                    <div v-if="paper.stage3?.messages?.length" class="mb-6">
                                        <div
                                            class="bg-gradient-to-r from-primary to-primary-dark text-white px-4 py-2 rounded-lg mb-4 flex justify-between items-center"
                                        >
                                            <span class="font-semibold"
                                                >Stage 3: Deep Analysis</span
                                            >
                                            <span class="text-lg">
                                                Score: {{ paper.stage3.score.toFixed(2) }}
                                                {{ paper.stage3.pass ? "✅" : "❌" }}
                                            </span>
                                        </div>
                                        <div
                                            v-if="paper.stage3.usage"
                                            class="text-sm text-gray-600 mb-3 px-3 py-2 bg-gray-50 rounded border-l-3 border-primary"
                                        >
                                            {{
                                                formatUsage(
                                                    paper.stage3.usage,
                                                    paper.stage3.estimated_cost,
                                                    paper.stage3.estimated_cost_currency,
                                                )
                                            }}
                                        </div>
                                        <div
                                            v-for="(msg, idx) in paper.stage3.messages"
                                            :key="`stage3-${idx}`"
                                            :class="[
                                                'mb-4 p-4 rounded-lg border-l-4',
                                                msg.role === 'user' && 'bg-blue-50 border-primary',
                                                msg.role === 'assistant' &&
                                                    'bg-gray-50 border-primary-dark',
                                                msg.role === 'system' &&
                                                    'bg-yellow-50 border-yellow-400',
                                            ]"
                                        >
                                            <div class="flex justify-between items-center mb-2">
                                                <span
                                                    class="font-semibold text-sm uppercase tracking-wide"
                                                    :class="[
                                                        msg.role === 'user' && 'text-primary',
                                                        msg.role === 'assistant' &&
                                                            'text-primary-dark',
                                                        msg.role === 'system' && 'text-yellow-600',
                                                    ]"
                                                >
                                                    {{ msg.role }}
                                                </span>
                                                <button
                                                    @click="toggleMessage(`stage3-${idx}`)"
                                                    class="text-gray-500 hover:text-gray-700"
                                                >
                                                    <ChevronDownIcon
                                                        :class="[
                                                            'w-5 h-5 transition-transform',
                                                            isMessageCollapsed(`stage3-${idx}`) &&
                                                                '-rotate-90',
                                                        ]"
                                                    />
                                                </button>
                                            </div>
                                            <div
                                                v-show="!isMessageCollapsed(`stage3-${idx}`)"
                                                class="text-gray-700 whitespace-pre-wrap leading-relaxed text-sm"
                                            >
                                                {{ msg.content }}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- No conversation data -->
                                    <div
                                        v-if="
                                            !paper.stage1?.messages?.length &&
                                            !paper.stage2?.messages?.length &&
                                            !paper.stage3?.messages?.length
                                        "
                                        class="text-center text-gray-500 py-10"
                                    >
                                        No conversation data available (all results from cache)
                                    </div>
                                </div>
                            </div>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>
</template>
