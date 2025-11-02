declare module "markdown-it-katex" {
    import type MarkdownIt from "markdown-it";

    interface KatexOptions {
        throwOnError?: boolean;
        errorColor?: string;
    }

    function markdownItKatex(md: MarkdownIt, options?: KatexOptions): void;

    export = markdownItKatex;
}
