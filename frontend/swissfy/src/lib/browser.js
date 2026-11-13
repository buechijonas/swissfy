import { useDocumentVisibility, usePreferredReducedMotion } from '@vueuse/core'

export const documentVisibility = useDocumentVisibility()

export const reducedMotion = usePreferredReducedMotion()
