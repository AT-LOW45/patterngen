import { z } from "zod/v4";

// Validation rules for the Create ADR form. Only the fields the template marks as
// required are enforced; everything else is optional and validated leniently.
// Extra keys on the form object (context, alternatives, custom sections, etc.) are
// ignored by safeParse, so the whole `form` can be passed straight in.
export const adrSchema = z.object({
	title: z.string().trim().min(1, { message: "Title is required." }),
	status: z.string().min(1, { message: "Status is required." }),
	scope: z.string().trim().min(1, { message: "Scope is required." }),
	decision: z.string().trim().min(1, { message: "Decision is required." }),
});

export type AdrSchema = z.infer<typeof adrSchema>;
