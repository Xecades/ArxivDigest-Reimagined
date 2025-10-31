<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useDigestData } from "@/composables";
import { DigestHeader, StageSelector, PaperCard, ConversationModal } from "@/components";
import type { Paper } from "@/types";

const {
    data,
    loading,
    error,
    filteredPapers,
    defaultStage,
    loadData,
    setStage,
    currentStage,
    getStageCount,
} = useDigestData();

const selectedPaper = ref<Paper | null>(null);
const showModal = ref(false);

onMounted(async () => {
    await loadData();
    if (data.value) {
        setStage(defaultStage.value);
    }
});

const counts = computed(() => ({
    all: getStageCount("all"),
    stage1: getStageCount("1"),
    stage2: getStageCount("2"),
    stage3: getStageCount("3"),
}));

function handleStageChange(stage: "all" | "1" | "2" | "3") {
    setStage(stage);
}

function handleViewConversation(paperId: string) {
    const paper = filteredPapers.value.find((p) => p.arxiv_id === paperId);
    if (paper) {
        selectedPaper.value = paper;
        showModal.value = true;
    }
}

function closeModal() {
    showModal.value = false;
}
</script>

<template>
    <div class="min-h-screen p-4 sm:p-6 lg:p-8">
        <div class="max-w-7xl mx-auto bg-white rounded-xl shadow-2xl overflow-hidden">
            <!-- Loading State -->
            <div v-if="loading" class="flex items-center justify-center h-96">
                <div class="text-center">
                    <div
                        class="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"
                    ></div>
                    <p class="mt-4 text-gray-600">Loading digest data...</p>
                </div>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="flex items-center justify-center h-96">
                <div class="text-center text-red-600">
                    <svg
                        class="mx-auto h-16 w-16 mb-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                    <p class="text-xl font-semibold">Error loading data</p>
                    <p class="mt-2 text-gray-600">{{ error.message }}</p>
                </div>
            </div>

            <!-- Main Content -->
            <template v-else-if="data">
                <DigestHeader :metadata="data.metadata" />

                <StageSelector
                    :current-stage="currentStage"
                    :counts="counts"
                    @change="handleStageChange"
                />

                <div class="px-6 py-8">
                    <!-- Stats Bar -->
                    <div class="flex justify-between items-center mb-6 text-sm text-gray-600">
                        <div>
                            Total:
                            <span class="font-bold text-primary">{{ filteredPapers.length }}</span>
                        </div>
                        <div>
                            Showing:
                            <span class="font-semibold">{{
                                currentStage === "all" ? "All Papers" : `Stage ${currentStage}+`
                            }}</span>
                        </div>
                    </div>

                    <!-- Papers List -->
                    <div v-if="filteredPapers.length > 0">
                        <PaperCard
                            v-for="paper in filteredPapers"
                            :key="paper.arxiv_id"
                            :paper="paper"
                            @view-conversation="handleViewConversation"
                        />
                    </div>

                    <!-- Empty State -->
                    <div v-else class="text-center py-20">
                        <div class="text-6xl mb-4">📭</div>
                        <h2 class="text-2xl font-semibold text-gray-700 mb-2">No papers found</h2>
                        <p class="text-gray-500">Try selecting a different filter</p>
                    </div>
                </div>

                <!-- Footer -->
                <footer class="bg-gray-50 py-6 px-6 text-center text-sm text-gray-600 border-t">
                    <p class="mb-2 font-semibold">
                        {{ data.metadata.title }} | Three-Stage Progressive Filtering System
                    </p>
                    <p>
                        Stage 1: Title + Categories | Stage 2: + Authors + Abstract | Stage 3: +
                        Full Paper Analysis
                    </p>
                </footer>

                <!-- Conversation Modal -->
                <ConversationModal :paper="selectedPaper" :show="showModal" @close="closeModal" />
            </template>
        </div>
    </div>
</template>
