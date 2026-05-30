import AppLayout from "@/components/layout/AppLayout.vue";
import { createRouter, createWebHistory } from "vue-router";
import ROUTES from "./routes";

export type ExtractRoutes<T> = T extends string ? T : T extends Record<string, any> ? ExtractRoutes<T[keyof T]> : never;

export type RoutePaths = ExtractRoutes<typeof ROUTES>;
export type CreateRouterRoutes = Parameters<typeof createRouter>[0]["routes"];

const routes: CreateRouterRoutes = [
	{
		path: ROUTES.default,
		component: AppLayout,
		children: [
			{
				path: ROUTES.knowledgeBase,
				name: "KnowledgeBase",
				component: () => import("@/pages/KnowledgeBase.vue"),
			},
		],
	},
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});

export default router;
