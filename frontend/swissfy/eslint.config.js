import js from '@eslint/js'
import { defineConfig, globalIgnores } from 'eslint/config'
import skipFormatting from 'eslint-config-prettier/flat'
import pluginImport from 'eslint-plugin-import-x'
import pluginOxlint from 'eslint-plugin-oxlint'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

export default defineConfig([
  {
    name: 'app/files-to-lint',
    files: ['**/*.{vue,js,mjs,jsx}'],
  },

  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),

  {
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
  },

  js.configs.recommended,
  {
    rules: {
      'no-empty': ['error', { allowEmptyCatch: true }],
    },
  },
  ...pluginVue.configs['flat/essential'],
  {
    plugins: { 'import-x': pluginImport },
    rules: {
      'import-x/order': [
        'error',
        {
          groups: ['builtin', 'external', 'internal', 'parent', 'sibling'],
          pathGroups: [
            { pattern: '@core/**', group: 'internal', position: 'before' },
            { pattern: '@/**', group: 'internal' },
          ],
          pathGroupsExcludedImportTypes: ['builtin'],
          alphabetize: { order: 'asc', caseInsensitive: true },
          'newlines-between': 'never',
        },
      ],
    },
  },

  {
    rules: {
      'vue/no-restricted-component-options': [
        'error',
        { name: 'setup', message: 'Create composables in data() instead.' },
        { name: 'mixins', message: 'Use a composable, a function in lib/ or a component.' },
      ],
      'no-restricted-globals': [
        'error',
        { name: 'setTimeout', message: 'Use a composable such as useTimeoutFn from @vueuse/core.' },
      ],
      'no-restricted-imports': [
        'error',
        { name: 'vue', importNames: ['nextTick'], message: 'Wait for the state, not a tick.' },
      ],
      'no-restricted-properties': [
        'error',
        { property: '$nextTick', message: 'Wait for the state, not a tick.' },
      ],
      'vue/order-in-components': 'error',
      'vue/attributes-order': ['error', { alphabetical: false }],
      'vue/no-template-shadow': 'error',
    },
  },
  ...pluginOxlint.buildFromOxlintConfigFile('.oxlintrc.json'),

  skipFormatting,
])
