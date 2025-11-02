import { DigestSchema, type DigestData } from "@/types/digest";

/**
 * Load and validate digest data from JSON file
 */
export async function loadDigestData(): Promise<DigestData> {
    try {
        const response = await fetch("./digest.json");
        if (!response.ok) {
            throw new Error(`Failed to fetch digest.json: ${response.statusText}`);
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
