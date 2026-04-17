"use client";

import { useEffect, useState } from "react";
import confetti from "canvas-confetti";
import { Mascot } from "./Mascot";

const KONAMI = [
  "ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown",
  "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight",
  "b", "a",
];

export function EasterEgg() {
  const [active, setActive] = useState(false);

  useEffect(() => {
    let index = 0;
    const onKey = (e: KeyboardEvent) => {
      const expected = KONAMI[index];
      if (e.key === expected) {
        index++;
        if (index === KONAMI.length) {
          setActive(true);
          confetti({ particleCount: 200, spread: 120, origin: { y: 0.3 } });
          setTimeout(() => setActive(false), 4000);
          index = 0;
        }
      } else {
        index = 0;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!active) return null;
  return (
    <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center">
      <div className="animate-spin" style={{ animationDuration: "1.4s" }}>
        <Mascot mood="happy" size={160} />
      </div>
    </div>
  );
}
