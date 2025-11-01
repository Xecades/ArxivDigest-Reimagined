import { z } from "zod";

// Message schema
const MessageSchema = z.object({
    role: z.enum(["system", "user", "assistant"]),
    content: z.string(),
});

// Usage info schema
const UsageSchema = z
    .object({
        prompt_tokens: z.number().nullable(),
        completion_tokens: z.number().nullable(),
        total_tokens: z.number().nullable(),
    })
    .nullable();

// Base stage result schema
const BaseStageResultSchema = z.object({
    pass: z.boolean(),
    score: z.number(),
    reasoning: z.string(),
    messages: z.array(MessageSchema),
    usage: UsageSchema,
    estimated_cost: z.number().nullable(),
    estimated_cost_currency: z.string().nullable(),
});

// Stage 3 result schema (extends base with additional fields)
const Stage3ResultSchema = BaseStageResultSchema.extend({
    novelty_score: z.number(),
    impact_score: z.number(),
    quality_score: z.number(),
    custom_fields: z.record(z.string()).optional(),
});

// Paper schema
const PaperSchema = z.object({
    arxiv_id: z.string(),
    title: z.string(),
    authors: z.array(z.string()),
    categories: z.array(z.string()),
    abstract: z.string(),
    pdf_url: z.string(),
    abs_url: z.string(),
    published: z.string(),
    max_stage: z.number(),
    stage1: BaseStageResultSchema,
    stage2: BaseStageResultSchema.nullable(),
    stage3: Stage3ResultSchema.nullable(),
});

// Metadata schema
const MetadataSchema = z.object({
    title: z.string(),
    timestamp: z.string(),
    user_prompt: z.string(),
    arxiv_config: z.object({
        categories: z.array(z.string()),
        max_results: z.number(),
    }),
    llm_config: z.object({
        model: z.string(),
        temperature: z.number(),
    }),
    stage_thresholds: z.object({
        stage1: z.number(),
        stage2: z.number(),
        stage3: z.number(),
    }),
    custom_fields: z.array(
        z.object({
            name: z.string(),
            description: z.string(),
        }),
    ),
    stats: z.object({
        total_papers: z.number(),
        stage1_passed: z.number(),
        stage2_passed: z.number(),
        stage3_passed: z.number(),
    }),
});

// Full digest schema
export const DigestSchema = z.object({
    metadata: MetadataSchema,
    papers: z.array(PaperSchema),
});

// TypeScript types inferred from schemas
export type Message = z.infer<typeof MessageSchema>;
export type UsageInfo = z.infer<typeof UsageSchema>;
export type BaseStageResult = z.infer<typeof BaseStageResultSchema>;
export type Stage3Result = z.infer<typeof Stage3ResultSchema>;
export type Paper = z.infer<typeof PaperSchema>;
export type Metadata = z.infer<typeof MetadataSchema>;
export type DigestData = z.infer<typeof DigestSchema>;
