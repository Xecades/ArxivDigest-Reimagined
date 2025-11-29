import { ref, computed, watch, onMounted } from "vue";
import { loadDigestData, loadHistoryIndex } from "@/utils/digestLoader";
import type { DigestData, Paper } from "@/types/digest";

export function useDigest() {
    const digestData = ref<DigestData | null>(null);
    const loading = ref(true);
    const error = ref<string | null>(null);
    const currentStage = ref<string>("all");
    const selectedPaper = ref<Paper | null>(null);
    const showModal = ref(false);

    // History support
    const historyDates = ref<string[]>([]);
    const selectedDate = ref<string>(""); // Empty string means "Latest"
    const latestDateString = ref<string>("");

    // Helper to format date
    const formatDateFromTimestamp = (timestamp: string) => {
        const date = new Date(timestamp);
        const yyyy = date.getUTCFullYear();
        const mm = String(date.getUTCMonth() + 1).padStart(2, "0");
        const dd = String(date.getUTCDate()).padStart(2, "0");
        const hh = String(date.getUTCHours()).padStart(2, "0");
        const min = String(date.getUTCMinutes()).padStart(2, "0");
        const ss = String(date.getUTCSeconds()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}_${hh}-${min}-${ss}`;
    };

    // Load data
    const loadData = async (date?: string) => {
        loading.value = true;
        error.value = null;
        try {
            const data = await loadDigestData(date);
            digestData.value = data;

            // Reset stage selection logic when data changes
            if (digestData.value.metadata.stats.stage3_passed > 0) {
                currentStage.value = "3";
            } else if (digestData.value.metadata.stats.stage2_passed > 0) {
                currentStage.value = "2";
            } else if (digestData.value.metadata.stats.stage1_passed > 0) {
                currentStage.value = "1";
            } else {
                currentStage.value = "all";
            }
        } catch (e) {
            error.value = e instanceof Error ? e.message : "Failed to load digest data";
        } finally {
            loading.value = false;
        }
    };

    // Handle date change from navigator
    const handleDateChange = (newDate: string) => {
        if (historyDates.value.length > 0) {
            // If history exists, we rely on it.
            selectedDate.value = newDate;
        } else {
            // Fallback mode: if no history, we might be using digest.json
            if (newDate === latestDateString.value) {
                selectedDate.value = "";
            } else {
                selectedDate.value = ""; // Default to latest
            }
        }
    };

    // Watch for date changes
    watch(selectedDate, (newDate) => {
        loadData(newDate || undefined);
    });

    // Load initial data
    onMounted(async () => {
        // Load history index first
        historyDates.value = await loadHistoryIndex();
        // Sort dates descending (newest first)
        historyDates.value.sort((a, b) => b.localeCompare(a));

        if (historyDates.value.length > 0) {
            // If history exists, use the latest history file as the source of truth
            const latest = historyDates.value[0];
            if (latest) {
                selectedDate.value = latest;
                latestDateString.value = latest;
            }
        } else {
            // Fallback: Load digest.json if no history is available
            await loadData();
            if (digestData.value) {
                latestDateString.value = formatDateFromTimestamp(
                    digestData.value.metadata.timestamp,
                );
            }
        }
    });

    // Current displayed date (YYYY-MM-DD HH:MM:SS)
    const currentDigestDate = computed(() => {
        if (!digestData.value) return "";

        // If we are viewing a history file, selectedDate will be set
        if (selectedDate.value) return selectedDate.value;

        // If we are viewing latest, use the stored latestDateString or construct it
        if (latestDateString.value) return latestDateString.value;

        return formatDateFromTimestamp(digestData.value.metadata.timestamp);
    });

    // All available dates including the latest one
    const allAvailableDates = computed(() => {
        const dates = new Set([...historyDates.value]);
        if (latestDateString.value) {
            dates.add(latestDateString.value);
        } else if (currentDigestDate.value) {
            // Fallback if latestDateString not yet set but we have data
            dates.add(currentDigestDate.value);
        }
        return Array.from(dates).sort((a, b) => b.localeCompare(a));
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

    return {
        digestData,
        loading,
        error,
        currentStage,
        selectedPaper,
        showModal,
        historyDates,
        selectedDate,
        currentDigestDate,
        allAvailableDates,
        filteredPapers,
        stageName,
        handleDateChange,
        showConversation,
        closeModal,
    };
}
