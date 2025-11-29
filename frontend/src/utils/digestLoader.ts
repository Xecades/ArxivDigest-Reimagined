import { DigestSchema, type DigestData } from "@/types/digest";

/**
 * Load and validate digest data from JSON file
 * @param date Optional date string (YYYY-MM-DD) to load specific history
 */
export async function loadDigestData(date?: string): Promise<DigestData> {
    try {
        // If date is provided, load from history folder, otherwise load default digest.json
        const url = date ? `./history/${date}.json` : "./digest.json";

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch digest data (${url}): ${response.statusText}`);
        }

        const rawData = await response.json();

        // Validate with Zod
        const validatedData = DigestSchema.parse(rawData);

        return validatedData;
    } catch (error) {
        console.error("Error loading digest data:", error);
        throw error;
    }
}

/**
 * Load the list of available history dates
 */
export async function loadHistoryIndex(): Promise<string[]> {
    try {
        const response = await fetch("./history/index.json");
        if (!response.ok) {
            // If index doesn't exist (e.g. first run or local dev), return empty array
            // This ensures graceful fallback to "latest only" mode
            if (response.status === 404) return [];
            throw new Error(`Failed to fetch history index: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        // Silently fail for history index to allow local development without errors
        console.debug("Could not load history index (running in local/latest-only mode):", error);
        return [];
    }
}
