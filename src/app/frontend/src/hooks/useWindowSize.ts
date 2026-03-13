import { useState, useEffect } from 'react';

/**
 * Returns the current window inner-width, updating on resize.
 * Falls back to 1200 during SSR.
 */
export function useWindowSize(): number {
  const [windowWidth, setWindowWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1200,
  );

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowWidth;
}
