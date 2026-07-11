import { useToast } from "primevue/usetoast";
import { Ref, ref, unref } from "vue";
import { z } from "zod/v4";

// `z.ZodType` is the modern base type for "any schema" — `ZodTypeAny` was moved to
// zod's deprecated `compat` shim in v4.
export type ZodErrorTree<T extends z.ZodType> = {
	errors: string[];
	properties?: {
		[K in keyof z.infer<T>]?: { errors: string[] };
	};
};

type ErrorToast = { errorToast: Pick<Parameters<ReturnType<typeof useToast>["add"]>[0], "detail" | "summary"> };

const useZodValidation = <T extends z.ZodType>(schemaParam: T | Ref<T>, toastData?: ErrorToast) => {
	const toast = useToast();

	// initialize to `null` so the ref type is `ZodErrorTree<T> | null` (not undefined)
	const validationErrors = ref<ZodErrorTree<T> | null>(null);
	const hasSubmittedOnceWithErrors = ref(false);
	const currentSchema = ref<T | null>(schemaParam ? (unref(schemaParam) as T) : null);

	const updateSchema = (newSchema: T) => (currentSchema.value = newSchema);

	const simpleValidate = (validationObject: unknown) => {
		const schema = currentSchema.value;
		if (!schema) {
			return;
		}

		const result = schema.safeParse(validationObject);

		if (!result.success) {
			const errors = z.treeifyError(result.error);

			if (hasSubmittedOnceWithErrors.value) {
				validationErrors.value = errors;
			}
		} else {
			validationErrors.value = null;
		}
	};

	const validate = (validationObject: unknown): boolean => {
		const schema = currentSchema.value;
		if (!schema) {
			return true; // nothing to validate against
		}

		const result = schema.safeParse(validationObject);

		if (!result.success) {
			hasSubmittedOnceWithErrors.value = true;
			const errors = z.treeifyError(result.error);
			validationErrors.value = errors;

			if (toastData) {
				toast.add({ severity: "error", summary: toastData.errorToast.summary, detail: toastData.errorToast.detail, life: 3000 });
			}

			return false;
		}

		validationErrors.value = null;
		hasSubmittedOnceWithErrors.value = false;
		return true;
	};

	return { validate, simpleValidate, updateSchema, validationErrors };
};

export default useZodValidation;
