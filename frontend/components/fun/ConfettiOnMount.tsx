"use client";

import { useEffect } from "react";
import confetti from "canvas-confetti";

export function ConfettiOnMount() {
  useEffect(() => {
    const duration = 900;
    const end = Date.now() + duration;
    const colors = ["#7c3aed", "#a78bfa", "#fbbf24", "#34d399"];

    (function frame() {
      confetti({
        particleCount: 2,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors,
      });
      confetti({
        particleCount: 2,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors,
      });
      if (Date.now() < end) requestAnimationFrame(frame);
    })();
  }, []);

  return null;
}
