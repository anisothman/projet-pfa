"use client";

import { motion } from "framer-motion";

type Mood = "idle" | "thinking" | "happy" | "sleeping";

export function Mascot({ mood = "idle", size = 48 }: { mood?: Mood; size?: number }) {
  const animate =
    mood === "thinking"
      ? { rotate: [0, -6, 6, 0] }
      : mood === "happy"
        ? { y: [0, -6, 0] }
        : mood === "sleeping"
          ? { opacity: [0.6, 1, 0.6] }
          : { y: [0, -3, 0] };

  return (
    <motion.div
      style={{ width: size, height: size }}
      animate={animate}
      transition={{ duration: mood === "thinking" ? 1.2 : 2.4, repeat: Infinity, ease: "easeInOut" }}
      aria-hidden
    >
      <svg viewBox="0 0 64 64" width={size} height={size} role="img" aria-label="Localis mascot">
        <defs>
          <radialGradient id="mascot-body" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#a78bfa" />
            <stop offset="100%" stopColor="#7c3aed" />
          </radialGradient>
        </defs>
        <circle cx="32" cy="32" r="26" fill="url(#mascot-body)" />
        {mood === "sleeping" ? (
          <>
            <path d="M19 30 q4 -2 8 0" stroke="#fff" strokeWidth="2" fill="none" strokeLinecap="round" />
            <path d="M37 30 q4 -2 8 0" stroke="#fff" strokeWidth="2" fill="none" strokeLinecap="round" />
            <text x="44" y="22" fontSize="10" fill="#fff">z</text>
          </>
        ) : (
          <>
            <circle cx="23" cy="29" r="3.2" fill="#fff" />
            <circle cx="41" cy="29" r="3.2" fill="#fff" />
            <circle cx="23" cy="29" r="1.4" fill="#1b1033" />
            <circle cx="41" cy="29" r="1.4" fill="#1b1033" />
          </>
        )}
        {mood === "happy" ? (
          <path d="M22 40 Q32 48 42 40" stroke="#fff" strokeWidth="2.4" fill="none" strokeLinecap="round" />
        ) : mood === "thinking" ? (
          <path d="M22 42 L42 42" stroke="#fff" strokeWidth="2.4" fill="none" strokeLinecap="round" />
        ) : (
          <path d="M24 41 Q32 44 40 41" stroke="#fff" strokeWidth="2.2" fill="none" strokeLinecap="round" />
        )}
      </svg>
    </motion.div>
  );
}
