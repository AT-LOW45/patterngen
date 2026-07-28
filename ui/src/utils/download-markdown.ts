/**
 * Trigger a browser download of `content` as a `.md` file.
 *
 * Purely client-side — the caller supplies markdown it already holds (the editor
 * buffer) or has fetched (`getRawRecord`). No backend endpoint is involved, so
 * there's nothing to keep in sync with the API.
 */
export const downloadMarkdown = (filename: string, content: string): void => {
	const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
	const url = URL.createObjectURL(blob);

	const anchor = document.createElement("a");
	anchor.href = url;
	anchor.download = filename.endsWith(".md") ? filename : `${filename}.md`;
	document.body.appendChild(anchor);
	anchor.click();
	anchor.remove();

	URL.revokeObjectURL(url);
};
