<script setup lang="ts">
import { computed } from "vue";
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from "@headlessui/vue";
import {
    ChevronLeftIcon,
    ChevronRightIcon,
    CalendarDaysIcon,
    ChevronUpDownIcon,
    CheckIcon,
} from "@heroicons/vue/20/solid";

const props = defineProps<{
    currentDate: string; // YYYY-MM-DD_HH-MM-SS
    availableDates: string[];
}>();

const emit = defineEmits<{
    (e: "change", date: string): void;
}>();

// Format date for display (YYYY-MM-DD HH:MM:SS)
const formatDate = (dateStr: string) => {
    // Expecting YYYY-MM-DD_HH-MM-SS
    const parts = dateStr.split("_");
    if (parts.length === 2 && parts[1]) {
        const date = parts[0];
        const time = parts[1].replace(/-/g, ":");
        return `${date} ${time}`;
    }
    return dateStr;
};

// Combine current date into the list if not present, and sort
const allDates = computed(() => {
    const dates = new Set([...props.availableDates, props.currentDate]);
    return Array.from(dates).sort((a, b) => b.localeCompare(a));
});

const currentIndex = computed(() => {
    return allDates.value.indexOf(props.currentDate);
});

const hasPrev = computed(() => {
    return currentIndex.value !== -1 && currentIndex.value < allDates.value.length - 1;
});

const hasNext = computed(() => {
    return currentIndex.value !== -1 && currentIndex.value > 0;
});

const prevDate = computed(() => {
    if (!hasPrev.value) return null;
    return allDates.value[currentIndex.value + 1] || null;
});

const nextDate = computed(() => {
    if (!hasNext.value) return null;
    return allDates.value[currentIndex.value - 1] || null;
});

function navigate(date: string | null) {
    if (date) {
        emit("change", date);
    }
}
</script>

<template>
    <div class="date-navigator">
        <!-- Previous Button -->
        <button
            class="nav-btn"
            :disabled="!hasPrev"
            @click="navigate(prevDate)"
            title="Previous Digest"
        >
            <ChevronLeftIcon class="icon" />
        </button>

        <!-- Date Selector -->
        <Listbox
            :model-value="currentDate"
            @update:model-value="(date) => navigate(date as string)"
            as="div"
            class="date-listbox"
        >
            <div class="relative">
                <ListboxButton class="listbox-btn">
                    <CalendarDaysIcon class="icon-sm text-white" />
                    <span class="date-text">{{ formatDate(currentDate) }}</span>
                    <ChevronUpDownIcon class="icon-xs text-secondary" />
                </ListboxButton>

                <transition
                    enter-active-class="transition duration-100 ease-out"
                    enter-from-class="transform scale-95 opacity-0"
                    enter-to-class="transform scale-100 opacity-100"
                    leave-active-class="transition duration-75 ease-in"
                    leave-from-class="transform scale-100 opacity-100"
                    leave-to-class="transform scale-95 opacity-0"
                >
                    <ListboxOptions class="listbox-options">
                        <ListboxOption
                            v-for="date in allDates"
                            :key="date"
                            :value="date"
                            as="template"
                            v-slot="{ active, selected }"
                        >
                            <li
                                :class="[
                                    'listbox-option',
                                    active ? 'bg-accent-light text-accent' : 'text-primary',
                                ]"
                            >
                                <span
                                    :class="[
                                        'block truncate',
                                        selected ? 'font-medium' : 'font-normal',
                                    ]"
                                >
                                    {{ formatDate(date) }}
                                </span>
                                <span v-if="selected" class="check-icon-container">
                                    <CheckIcon class="icon-xs" aria-hidden="true" />
                                </span>
                            </li>
                        </ListboxOption>
                    </ListboxOptions>
                </transition>
            </div>
        </Listbox>

        <!-- Next Button -->
        <button
            class="nav-btn"
            :disabled="!hasNext"
            @click="navigate(nextDate)"
            title="Next Digest"
        >
            <ChevronRightIcon class="icon" />
        </button>
    </div>
</template>

<style scoped>
.date-navigator {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.nav-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: rgba(255, 255, 255, 0.8);
    cursor: pointer;
    transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
}

.nav-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

.date-listbox {
    position: relative;
    min-width: 180px;
}

.relative {
    position: relative;
}

.listbox-btn {
    position: relative;
    width: 100%;
    cursor: pointer;
    border-radius: 0.5rem;
    background: transparent;
    padding: 0.25rem 0.5rem;
    padding-right: 0.5rem;
    text-align: left;
    border: 1px solid transparent;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: inherit;
    font-size: 0.95rem;
    color: #fff;
    transition: all 0.2s;
}

.listbox-btn:hover {
    background: rgba(255, 255, 255, 0.1);
}

.listbox-btn:active {
    outline: none;
    background: rgba(255, 255, 255, 0.15);
}

.date-text {
    font-weight: 600;
    color: #fff;
}

.listbox-options {
    position: absolute;
    margin-top: 0.5rem;
    max-height: 15rem;
    width: 100%;
    overflow: auto;
    border-radius: 0.5rem;
    background: var(--white);
    padding: 0.25rem 0;
    font-size: 0.9rem;
    box-shadow:
        0 10px 15px -3px rgba(0, 0, 0, 0.1),
        0 4px 6px -2px rgba(0, 0, 0, 0.05);
    z-index: 50;
    color: var(--text-color);
}

.listbox-options:focus {
    outline: none;
}

.listbox-option {
    position: relative;
    cursor: pointer;
    user-select: none;
    padding: 0.5rem 1rem;
    padding-right: 2rem;
    color: var(--text-color);
    transition: background-color 0.1s;
}

.bg-accent-light {
    background-color: #eff6ff; /* blue-50 */
}

.text-accent {
    color: var(--accent-color);
}

.text-white {
    color: #ffffff;
}

.text-primary {
    color: var(--primary-color);
}

.text-secondary {
    color: rgba(255, 255, 255, 0.7);
}

.font-medium {
    font-weight: 500;
}

.font-normal {
    font-weight: 400;
}

.check-icon-container {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    display: flex;
    align-items: center;
    padding-right: 0.75rem;
    color: var(--accent-color);
}

.icon {
    width: 1.25rem;
    height: 1.25rem;
}

.icon-sm {
    width: 1rem;
    height: 1rem;
}

.icon-xs {
    width: 0.875rem;
    height: 0.875rem;
}

/* Scrollbar for options */
.listbox-options::-webkit-scrollbar {
    width: 6px;
}

.listbox-options::-webkit-scrollbar-track {
    background: transparent;
}

.listbox-options::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}

.listbox-options::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>
