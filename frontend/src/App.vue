<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { loadDigestData } from "@/utils/digestLoader";
import type { DigestData, Paper } from "@/types/digest";
import { formatDate } from "@/utils/formatters";
import PaperCard from "@/components/PaperCard.vue";
import ConversationModal from "@/components/ConversationModal.vue";

const digestData = ref<DigestData | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const currentStage = ref<string>("all");
const selectedPaper = ref<Paper | null>(null);
const showModal = ref(false);

// Load data on mount
onMounted(async () => {
    try {
        digestData.value = await loadDigestData();
        // Set default stage to highest non-empty stage
        if (digestData.value.metadata.stats.stage3_passed > 0) {
            currentStage.value = "3";
        } else if (digestData.value.metadata.stats.stage2_passed > 0) {
            currentStage.value = "2";
        } else if (digestData.value.metadata.stats.stage1_passed > 0) {
            currentStage.value = "1";
        }
    } catch (e) {
        error.value = e instanceof Error ? e.message : "Failed to load digest data";
    } finally {
        loading.value = false;
    }
});

// Filtered papers based on current stage
const filteredPapers = computed(() => {
    if (!digestData.value) return [];
    if (currentStage.value === "all") return digestData.value.papers;

    const minStage = parseInt(currentStage.value);
    return digestData.value.papers.filter((paper) => paper.max_stage >= minStage);
});

// Stage names for display
const stageName = computed(() => {
    const names: Record<string, string> = {
        all: "All Papers",
        "1": "Stage 1+",
        "2": "Stage 2+",
        "3": "Stage 3",
    };
    return names[currentStage.value] || "All Papers";
});

// Format timestamp
const formattedTimestamp = computed(() => {
    if (!digestData.value) return "";
    return formatDate(digestData.value.metadata.timestamp);
});

// Show conversation modal
function showConversation(paper: Paper) {
    selectedPaper.value = paper;
    showModal.value = true;
}

// Close conversation modal
function closeModal() {
    showModal.value = false;
    selectedPaper.value = null;
}
</script>

<template>
    <div v-if="error" class="error">
        <FontAwesomeIcon icon="times-circle" style="margin-right: 10px" />
        Error: {{ error }}
    </div>
    <div v-else-if="digestData" class="container">
        <header>
            <h1>
                🎓
                {{ digestData.metadata.title }}
            </h1>
            <div class="timestamp">Generated on {{ formattedTimestamp }}</div>
        </header>

        <div class="controls">
            <div class="stage-selector">
                <button
                    class="stage-btn"
                    :class="{ active: currentStage === 'all' }"
                    @click="currentStage = 'all'"
                >
                    All Papers ({{ digestData.metadata.stats.total_papers }})
                </button>
                <button
                    class="stage-btn"
                    :class="{ active: currentStage === '1' }"
                    @click="currentStage = '1'"
                >
                    Stage 1+ ({{ digestData.metadata.stats.stage1_passed }})
                </button>
                <button
                    class="stage-btn"
                    :class="{ active: currentStage === '2' }"
                    @click="currentStage = '2'"
                >
                    Stage 2+ ({{ digestData.metadata.stats.stage2_passed }})
                </button>
                <button
                    class="stage-btn"
                    :class="{ active: currentStage === '3' }"
                    @click="currentStage = '3'"
                >
                    Stage 3 ({{ digestData.metadata.stats.stage3_passed }})
                </button>
            </div>

            <div class="stats">
                <div class="stat">
                    <span>Total:</span>
                    <span class="stat-value">{{ filteredPapers.length }}</span>
                </div>
                <div class="stat">
                    <span>Showing:</span>
                    <span class="stat-value">{{ stageName }}</span>
                </div>
            </div>
        </div>

        <div class="papers-container">
            <div v-if="filteredPapers.length === 0" class="no-papers">
                <div class="no-papers-icon">📭</div>
                <h2>No papers found</h2>
                <p>Try selecting a different filter</p>
            </div>
            <PaperCard
                v-for="paper in filteredPapers"
                :key="paper.arxiv_id"
                :paper="paper"
                @show-conversation="showConversation"
            />
        </div>

        <footer>
            <p>{{ digestData.metadata.title }} | Three-Stage Progressive Filtering System</p>
            <p>
                Stage 1: Title + Categories | Stage 2: + Authors + Abstract | Stage 3: + Full Paper
                Analysis
            </p>
        </footer>

        <ConversationModal
            v-if="showModal && selectedPaper"
            :paper="selectedPaper"
            @close="closeModal"
        />
    </div>
</template>

<style scoped>
.error {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    font-size: 1.5em;
    color: #ff6b6b;
}
</style>
