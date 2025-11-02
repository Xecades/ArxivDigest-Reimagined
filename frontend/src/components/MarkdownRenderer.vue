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
    line-height: 1.6;
}

.markdown-renderer p {
    margin: 0.5em 0;
}

.markdown-renderer ul,
.markdown-renderer ol {
    margin: 0.5em 0;
    padding-left: 1.5em;
}

.markdown-renderer li {
    margin: 0.25em 0;
}

.markdown-renderer h1,
.markdown-renderer h2,
.markdown-renderer h3,
.markdown-renderer h4,
.markdown-renderer h5,
.markdown-renderer h6 {
    margin: 1em 0 0.5em 0;
    font-weight: 600;
}

.markdown-renderer h1 {
    font-size: 1.5em;
}

.markdown-renderer h2 {
    font-size: 1.3em;
}

.markdown-renderer h3 {
    font-size: 1.1em;
}

.markdown-renderer code {
    background-color: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: "Courier New", Courier, monospace;
    font-size: 0.9em;
}

.markdown-renderer pre {
    background-color: #f4f4f4;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
}

.markdown-renderer pre code {
    background-color: transparent;
    padding: 0;
}

.markdown-renderer blockquote {
    border-left: 4px solid #ddd;
    padding-left: 1em;
    margin: 1em 0;
    color: #666;
}

.markdown-renderer a {
    color: #667eea;
    text-decoration: none;
}

.markdown-renderer a:hover {
    text-decoration: underline;
}

.markdown-renderer strong {
    font-weight: 600;
}

.markdown-renderer em {
    font-style: italic;
}

/* KaTeX display math centering */
.markdown-renderer .katex-display {
    margin: 1em 0;
    overflow-x: auto;
    overflow-y: hidden;
}
</style>
