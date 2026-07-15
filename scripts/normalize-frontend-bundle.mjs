import { readFile, writeFile } from "node:fs/promises";

const path = "custom_components/urdb/frontend/urdb-card.js";
const bundle = await readFile(path, "utf8");
await writeFile(path, bundle.replace(/[ \t]+$/gm, ""), "utf8");
