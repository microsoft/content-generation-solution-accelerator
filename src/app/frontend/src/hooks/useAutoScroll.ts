import { useEffect, useRef } from 'react';

/**
 * Scrolls a sentinel element into view whenever any dependency changes.
 *
 * @param deps - React dependency list that triggers the scroll.
 * @returns A ref to attach to a zero-height element at the bottom of the
 *          scrollable container (the "scroll anchor").
 *
 * @example
 * ```tsx
 * const endRef = useAutoScroll([messages, isLoading]);
 * return (
 *   <div style={{ overflowY: 'auto' }}>
 *     {messages.map(m => <Message key={m.id} {...m} />)}
 *     <div ref={endRef} />
 *   </div>
 * );
 * ```
 */
export function useAutoScroll(deps: React.DependencyList) {
  const endRef = useRef<HTMLDivElement>(null);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, deps);

  return endRef;
}
