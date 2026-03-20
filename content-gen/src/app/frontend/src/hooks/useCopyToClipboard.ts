import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Copy text to the clipboard and expose a transient `copied` flag.
 *
 * @param resetTimeout - Milliseconds before `copied` resets to `false` (default 2 000).
 * @returns `{ copied, copy }` — `copy(text)` writes to the clipboard and
 *          flips `copied` to `true` for `resetTimeout` ms.
 */
export function useCopyToClipboard(resetTimeout = 2000) {
  const [copied, setCopied] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  const copy = useCallback(
    (text: string) => {
      navigator.clipboard.writeText(text).catch(() => {
        // Clipboard write failure — non-critical
      });
      setCopied(true);
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(false), resetTimeout);
    },
    [resetTimeout],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => clearTimeout(timerRef.current);
  }, []);

  return { copied, copy };
}
