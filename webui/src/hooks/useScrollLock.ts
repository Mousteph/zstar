import { useEffect } from "react";

let lockCount = 0;
let savedOverflow = "";

function lockScroll() {
  if (lockCount === 0) {
    savedOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  }
  lockCount++;
}

function unlockScroll() {
  lockCount = Math.max(0, lockCount - 1);
  if (lockCount === 0) {
    document.body.style.overflow = savedOverflow;
    savedOverflow = "";
  }
}

export function useScrollLock(active: boolean): void {
  useEffect(() => {
    if (!active) {
      return;
    }

    lockScroll();

    return () => {
      unlockScroll();
    };
  }, [active]);
}
