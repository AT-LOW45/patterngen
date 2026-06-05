<template>
	<router-view></router-view>
	<ConfirmPopup group="resets" />
	<Toast />
</template>

<script setup lang="ts">
import { ConfirmPopup, Toast } from "primevue";
</script>
