"use client";

import { BottomNav } from "@/components/layout/bottom-nav";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#1A1A2E] pb-20">
      {children}
      <BottomNav />
    </div>
  );
}
