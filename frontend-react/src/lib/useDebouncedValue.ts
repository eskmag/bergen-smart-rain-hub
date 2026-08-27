import { useEffect, useState } from 'react'

/**
 * Returns `value` only after it has stopped changing for `delayMs`.
 *
 * Used to collapse a burst of calculator input changes (dragging the 199-step
 * tank slider, rapid clicks on the people stepper) into a single API request.
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])

  return debounced
}
