import { z } from "zod";

// ============================================
// Message Schema
// ============================================

export const MessageSchema = z.object({
    role: z.enum(["system", "user", "assistant"]),
    content: z.string(),
});

export type Message = z.infer<typeof MessageSchema>;

// ============================================
// Usage & Cost Schemas
// ============================================

export const UsageSchema = z
    .object({
        prompt_tokens: z.number().nullable().optional(),
        completion_tokens: z.number().nullable().optional(),
        total_tokens: z.number().nullable().optional(),
    })
    .nullable()
    .optional();

export type Usage = z.infer<typeof UsageSchema>;

// ============================================
// Stage Result Schemas
// ============================================

export const BaseStageResultSchema = z.object({
    pass: z.boolean(),
    score: z.number(),
    reasoning: z.string(),
    messages: z.array(MessageSchema),
    usage: UsageSchema,
    estimated_cost: z.number().nullable().optional(),
    estimated_cost_currency: z.string().nullable().optional(),
});

export const Stage1ResultSchema = BaseStageResultSchema;

export const Stage2ResultSchema = BaseStageResultSchema;

export const Stage3ResultSchema = BaseStageResultSchema.extend({
    novelty_score: z.number(),
    impact_score: z.number(),
    quality_score: z.number(),
    custom_fields: z.record(z.any()).optional(),
});

export type Stage1Result = z.infer<typeof Stage1ResultSchema>;
export type Stage2Result = z.infer<typeof Stage2ResultSchema>;
export type Stage3Result = z.infer<typeof Stage3ResultSchema>;

// ============================================
// Paper Schema
// ============================================

export const PaperSchema = z.object({
    arxiv_id: z.string(),
    title: z.string(),
    authors: z.array(z.string()),
    categories: z.array(z.string()),
    abstract: z.string(),
    pdf_url: z.string(),
    abs_url: z.string(),
    published: z.string().optional(),
    max_stage: z.number(),
    stage1: Stage1ResultSchema,
    stage2: Stage2ResultSchema.nullable(),
    stage3: Stage3ResultSchema.nullable(),
});

export type Paper = z.infer<typeof PaperSchema>;

// ============================================
// Metadata Schema
// ============================================

export const MetadataSchema = z.object({
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
    custom_fields: z.array(z.string()),
    stats: z.object({
        total_papers: z.number(),
        stage1_passed: z.number(),
        stage2_passed: z.number(),
        stage3_passed: z.number(),
    }),
});

export type Metadata = z.infer<typeof MetadataSchema>;

// ============================================
// Digest Data Schema
// ============================================

export const DigestDataSchema = z.object({
    metadata: MetadataSchema,
    papers: z.array(PaperSchema),
});

export type DigestData = z.infer<typeof DigestDataSchema>;
