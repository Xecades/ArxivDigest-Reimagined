<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useDigest } from "@/composables/useDigest";
import { loadAuthorFeed } from "@/utils/digestLoader";
import { formatDate } from "@/utils/formatters";
import type { AuthorFeedData } from "@/types/authors";
import PaperCard from "@/components/PaperCard.vue";
import ConversationModal from "@/components/ConversationModal.vue";
import DateNavigator from "@/components/DateNavigator.vue";
import AuthorFeed from "@/components/AuthorFeed.vue";

const {
    digestData,
    error,
    currentStage,
    selectedPaper,
    showModal,
    currentDigestDate,
    allAvailableDates,
    filteredPapers,
    stageName,
    handleDateChange,
    showConversation,
    closeModal,
} = useDigest();

// Top-level view; mirrored in the URL hash so the Authors tab is linkable
type View = "digest" | "authors";
const currentView = ref<View>(window.location.hash === "#authors" ? "authors" : "digest");
const authorFeed = ref<AuthorFeedData | null>(null);

function setView(view: View) {
    currentView.value = view;
    const { pathname, search } = window.location;
    history.replaceState(null, "", pathname + search + (view === "authors" ? "#authors" : ""));
}

onMounted(async () => {
    authorFeed.value = await loadAuthorFeed();
    // No authors.json deployed: there is no Authors tab to show
    if (!authorFeed.value) currentView.value = "digest";
});
</script>

<template>
    <div v-if="error" class="error">
        <FontAwesomeIcon icon="times-circle" style="margin-right: 10px" />
        Error: {{ error }}
    </div>
    <div v-else-if="digestData" class="container">
        <header>
            <h1>{{ digestData.metadata.title }}</h1>
            <div v-if="currentView === 'authors' && authorFeed" class="header-controls">
                <span class="updated-label">
                    Updated {{ formatDate(authorFeed.metadata.timestamp) }}
                </span>
            </div>
            <div v-else class="header-controls">
                <span class="generated-label">Generated on</span>
                <DateNavigator
                    v-if="currentDigestDate"
                    :current-date="currentDigestDate"
                    :available-dates="allAvailableDates"
                    @change="handleDateChange"
                />
            </div>
        </header>

        <nav v-if="authorFeed" class="view-tabs">
            <button
                class="view-tab"
                :class="{ active: currentView === 'digest' }"
                @click="setView('digest')"
            >
                <FontAwesomeIcon icon="filter" />
                Daily Digest
            </button>
            <button
                class="view-tab"
                :class="{ active: currentView === 'authors' }"
                @click="setView('authors')"
            >
                <FontAwesomeIcon icon="users" />
                Subscribed ({{ authorFeed.papers.length }})
            </button>
        </nav>

        <AuthorFeed v-if="currentView === 'authors' && authorFeed" :feed="authorFeed" />

        <template v-else>
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
        </template>

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
