"use client";

import { ReactNode } from "react";

const GOLD_BRIGHT = "#e8d48b";
const MUTED = "#9a8f7c";

type PremiumHeroProps = {
  title: string;
  subtitle: string;
  imageUrl: string;
  children?: ReactNode;
};

export function PremiumHero({ title, subtitle, imageUrl, children }: PremiumHeroProps) {
  return (
    <div className="relative h-72 w-full overflow-hidden">
      <img
        src={imageUrl}
        alt={title}
        className="h-full w-full object-cover opacity-40"
      />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#0b0b0b]" />
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4">
        <h1 className="font-serif text-5xl md:text-6xl" style={{ color: GOLD_BRIGHT }}>
          {title}
        </h1>
        <p className="mt-4 max-w-2xl text-sm md:text-base" style={{ color: MUTED }}>
          {subtitle}
        </p>
        {children}
      </div>
    </div>
  );
}
