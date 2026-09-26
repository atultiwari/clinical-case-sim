import js from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";
import tseslint from "typescript-eslint";

export default defineConfig([
  globalIgnores(["coverage/**", ".next/**", "next-env.d.ts"]),
  js.configs.recommended,
  ...tseslint.configs.strict,
  {
    rules: {
      "no-console": ["error", { allow: ["error"] }],
    },
  },
]);
