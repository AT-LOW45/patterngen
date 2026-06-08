<template>
	<div class="flex flex-col gap-2 form-field justify-end" :class="additionalClasses">
		<div class="flex flex-col gap-1">
			<div class="flex items-center gap-2">
				<label class="text-slate-600">{{ label }}</label>
				<i v-if="tip && tip.showOnHover" v-tooltip.top="tip.message" class="pi pi-info-circle" />
				<span v-if="required" class="text-red-600">*</span>
			</div>
			<p v-if="tip && !tip.showOnHover" class="text-sm text-slate-500/90">
				{{ tip.message }}
			</p>
		</div>

		<!--default slot should contain input element -->
		<slot />

		<span v-if="errorMessage" class="text-red-600 -mt-2">{{ Array.isArray(errorMessage) ? errorMessage.join(", ") : errorMessage }}</span>
	</div>
</template>

<script lang="ts">
type FormFieldProps = {
	label: string;
	required?: boolean;
	tip?: { message: string; showOnHover?: boolean };
	additionalClasses?: string;
	errorMessage?: string | string[];
};
</script>

<script setup lang="ts">
defineProps<FormFieldProps>();
</script>
