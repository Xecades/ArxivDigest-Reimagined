import { ref, computed, type Ref } from "vue";
import { DigestDataSchema, type DigestData } from "@/types";

export type StageFilter = "all" | "1" | "2" | "3";

export function useDigestData() {
    const data: Ref<DigestData | null> = ref(null);
    const loading = ref(false);
    const error: Ref<Error | null> = ref(null);
    const currentStage: Ref<StageFilter> = ref("all");

    // Load data from JSON
    async function loadData() {
        loading.value = true;
        error.value = null;

        try {
            const response = await fetch("/digest.json");
            if (!response.ok) {
                throw new Error(`Failed to fetch digest data: ${response.statusText}`);
            }

            const rawData = await response.json();

            // Validate with Zod
            const parsedData = DigestDataSchema.parse(rawData);
            data.value = parsedData;
        } catch (e) {
            error.value = e instanceof Error ? e : new Error(String(e));
            console.error("Failed to load digest data:", e);
        } finally {
            loading.value = false;
        }
    }

    // Computed: filtered papers based on current stage
    const filteredPapers = computed(() => {
        if (!data.value) return [];

        const { papers } = data.value;

        if (currentStage.value === "all") {
            return papers;
        }

        const minStage = parseInt(currentStage.value);
        return papers.filter((paper) => paper.max_stage >= minStage);
    });

    // Computed: stats for each stage
    const stats = computed(() => {
        if (!data.value) {
            return {
                total: 0,
                stage1: 0,
                stage2: 0,
                stage3: 0,
            };
        }

        return data.value.metadata.stats;
    });

    // Computed: default stage (highest non-empty stage)
    const defaultStage = computed((): StageFilter => {
        if (!data.value) return "all";

        const { stats } = data.value.metadata;
        if (stats.stage3_passed > 0) return "3";
        if (stats.stage2_passed > 0) return "2";
        if (stats.stage1_passed > 0) return "1";
        return "all";
    });

    // Set stage filter
    function setStage(stage: StageFilter) {
        currentStage.value = stage;
    }

    // Get stage name for display
    function getStageName(stage: StageFilter): string {
        const names: Record<StageFilter, string> = {
            all: "All Papers",
            "1": "Stage 1+",
            "2": "Stage 2+",
            "3": "Stage 3",
        };
        return names[stage];
    }

    // Get paper count for stage
    function getStageCount(stage: StageFilter): number {
        if (!data.value) return 0;

        const { stats } = data.value.metadata;

        switch (stage) {
            case "all":
                return stats.total_papers;
            case "1":
                return stats.stage1_passed;
            case "2":
                return stats.stage2_passed;
            case "3":
                return stats.stage3_passed;
            default:
                return 0;
        }
    }

    return {
        // State
        data,
        loading,
        error,
        currentStage,

        // Computed
        filteredPapers,
        stats,
        defaultStage,

        // Methods
        loadData,
        setStage,
        getStageName,
        getStageCount,
    };
}
