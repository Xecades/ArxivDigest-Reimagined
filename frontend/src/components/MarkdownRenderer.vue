<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import MarkdownIt from "markdown-it";
import markdownItKatex from "markdown-it-katex";
import markdownItPangu from "markdown-it-pangu-ts";

const props = withDefaults(
    defineProps<{
        content: string;
        inline?: boolean;
    }>(),
    { inline: false },
);

const renderedHtml = ref("");

// Initialize markdown-it with plugins
const md = new MarkdownIt({
    html: false, // Disable HTML tags for security
    breaks: true, // Convert \n to <br>
    linkify: true, // Auto-convert URLs to links
    typographer: true, // Enable smart quotes and other typographic features
})
    .use(markdownItKatex, {
        throwOnError: false,
        errorColor: "#cc0000",
    })
    .use(markdownItPangu);

function renderMarkdown() {
    try {
        if (props.inline) {
            renderedHtml.value = md.renderInline(props.content);
        } else {
            renderedHtml.value = md.render(props.content);
        }
    } catch (e) {
        console.error("Markdown rendering error:", e);
        renderedHtml.value = `<p>${props.content}</p>`;
    }
}

onMounted(() => {
    renderMarkdown();
});

watch(
    () => [props.content, props.inline],
    () => {
        renderMarkdown();
    },
);
</script>

<template>
    <div class="markdown-renderer" v-html="renderedHtml"></div>
</template>

<style>
/* Import KaTeX CSS (comes with markdown-it-katex) */
@import "katex/dist/katex.min.css";

.markdown-renderer {
    line-height: 1.7;
    color: #333;
    font-size: 0.9rem;
}

/* Paragraphs */
.markdown-renderer p {
    margin: 0.8em 0;
}

.markdown-renderer p:first-child {
    margin-top: 0;
}

.markdown-renderer p:last-child {
    margin-bottom: 0;
}

/* Lists */
.markdown-renderer ul,
.markdown-renderer ol {
    margin: 0.8em 0;
    padding-left: 2em;
}

.markdown-renderer li {
    margin: 0.3em 0;
}

.markdown-renderer ul ul,
.markdown-renderer ol ol,
.markdown-renderer ul ol,
.markdown-renderer ol ul {
    margin: 0.2em 0;
}

/* Headings */
.markdown-renderer h1,
.markdown-renderer h2,
.markdown-renderer h3,
.markdown-renderer h4,
.markdown-renderer h5,
.markdown-renderer h6 {
    margin: 1.5em 0 0.8em 0;
    font-weight: 600;
    line-height: 1.3;
    color: #1a202c;
}

.markdown-renderer h1:first-child,
.markdown-renderer h2:first-child,
.markdown-renderer h3:first-child {
    margin-top: 0;
}

.markdown-renderer h1 {
    font-size: 1.8em;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 0.3em;
}

.markdown-renderer h2 {
    font-size: 1.5em;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 0.3em;
}

.markdown-renderer h3 {
    font-size: 1.25em;
}

.markdown-renderer h4 {
    font-size: 1.1em;
}

.markdown-renderer h5,
.markdown-renderer h6 {
    font-size: 1em;
    color: #4a5568;
}

/* Code */
.markdown-renderer code {
    background-color: #f7fafc;
    border: 1px solid #e2e8f0;
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-family: "SFMono-Regular", "Consolas", "Liberation Mono", "Menlo", "Courier", monospace;
    font-size: 0.88em;
    color: #d73a49;
}

.markdown-renderer pre {
    background-color: #f7fafc;
    border: 1px solid #e2e8f0;
    padding: 1em;
    border-radius: 6px;
    overflow-x: auto;
    margin: 1em 0;
    line-height: 1.5;
}

.markdown-renderer pre code {
    background-color: transparent;
    border: none;
    padding: 0;
    color: #1a202c;
    font-size: 0.9em;
}

/* Blockquotes */
.markdown-renderer blockquote {
    border-left: 4px solid #667eea;
    padding-left: 1em;
    margin: 1em 0;
    color: #4a5568;
    background-color: #f7fafc;
    padding: 0.8em 1em;
    border-radius: 0 4px 4px 0;
}

.markdown-renderer blockquote p {
    margin: 0.5em 0;
}

/* Links */
.markdown-renderer a {
    color: #667eea;
    text-decoration: none;
    transition: color 0.2s ease;
}

.markdown-renderer a:hover {
    color: #5a67d8;
    text-decoration: underline;
}

/* Text formatting */
.markdown-renderer strong {
    font-weight: 600;
    color: #2d3748;
}

.markdown-renderer em {
    font-style: italic;
}

.markdown-renderer del {
    text-decoration: line-through;
    color: #718096;
}

/* Horizontal rule */
.markdown-renderer hr {
    border: none;
    border-top: 2px solid #e2e8f0;
    margin: 2em 0;
}

/* Tables */
.markdown-renderer table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    border-radius: 6px;
    overflow: hidden;
}

.markdown-renderer thead {
    background-color: #f7fafc;
}

.markdown-renderer th {
    padding: 0.5em 0.75em;
    text-align: left;
    font-weight: 600;
    color: #2d3748;
    border-bottom: 2px solid #cbd5e0;
    border-right: 1px solid #e2e8f0;
}

.markdown-renderer th:last-child {
    border-right: none;
}

.markdown-renderer td {
    padding: 0.5em 0.75em;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
}

.markdown-renderer td:last-child {
    border-right: none;
}

.markdown-renderer tr:last-child td {
    border-bottom: none;
}

.markdown-renderer tbody tr {
    transition: background-color 0.2s ease;
}

.markdown-renderer tbody tr:hover {
    background-color: #f7fafc;
}

.markdown-renderer tbody tr:nth-child(even) {
    background-color: #fafbfc;
}

.markdown-renderer tbody tr:nth-child(even):hover {
    background-color: #f1f3f5;
}

/* Table alignment */
.markdown-renderer th[align="center"],
.markdown-renderer td[align="center"] {
    text-align: center;
}

.markdown-renderer th[align="right"],
.markdown-renderer td[align="right"] {
    text-align: right;
}

/* Image */
.markdown-renderer img {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
    margin: 0.2em 0;
}

/* KaTeX display math centering */
.markdown-renderer .katex-display {
    margin: 1.2em 0;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 0.5em 0;
}

/* Inline KaTeX */
.markdown-renderer .katex {
    font-size: 1.05em;
}

/* Task lists */
.markdown-renderer input[type="checkbox"] {
    margin-right: 0.5em;
}

/* Better scrollbar for code blocks */
.markdown-renderer pre::-webkit-scrollbar {
    height: 8px;
}

.markdown-renderer pre::-webkit-scrollbar-track {
    background: #e2e8f0;
    border-radius: 4px;
}

.markdown-renderer pre::-webkit-scrollbar-thumb {
    background: #cbd5e0;
    border-radius: 4px;
}

.markdown-renderer pre::-webkit-scrollbar-thumb:hover {
    background: #a0aec0;
}
</style>
