/**
 * Escape HTML special characters
 */
export function escapeHtml(text: string): string {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format field name from snake_case to Title Case
 */
export function formatFieldName(name: string): string {
    return name
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

/**
 * Format cost number to 6 decimal places
 */
export function formatCost(cost: number | null | undefined): string {
    if (cost === null || cost === undefined) return "N/A";
    try {
        return cost.toFixed(6);
    } catch {
        return String(cost);
    }
}

/**
 * Format date from ISO string
 */
export function formatDate(isoString: string): string {
    try {
        const date = new Date(isoString);
        return date.toLocaleString("en-US", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
        });
    } catch {
        return isoString;
    }
}
