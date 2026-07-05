import { useToast } from "primevue/usetoast";
import { Ref, ref, unref } from "vue";
import { ZodTypeAny, z } from "zod/v4";

export type ZodErrorTree<T extends z.ZodTypeAny> = {
	errors: string[];
	properties?: {
		[K in keyof z.infer<T>]?: { errors: string[] };
	};
};

type ErrorToast = { errorToast: Pick<Parameters<ReturnType<typeof useToast>["add"]>[0], "detail" | "summary"> };

const useZodValidation = <T extends ZodTypeAny>(schemaParam: T | Ref<T>, toastData?: ErrorToast) => {
	const toast = useToast();

	// initialize to `null` so the ref type is `ZodErrorTree<T> | null` (not undefined)
	const validationErrors = ref<ZodErrorTree<T> | null>(null);
	const hasSubmittedOnceWithErrors = ref(false);
	const currentSchema = ref<T | null>(schemaParam ? (unref(schemaParam) as T) : null);

	const updateSchema = (newSchema: T) => (currentSchema.value = newSchema);

	const simpleValidate = (validationObject: unknown) => {
		const result = currentSchema.value.safeParse(validationObject);

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
		const result = currentSchema.value.safeParse(validationObject);

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
