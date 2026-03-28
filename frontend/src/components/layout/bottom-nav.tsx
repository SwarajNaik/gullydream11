"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Trophy, PlusCircle, Wallet, User } from "lucide-react";

const tabs = [
  { href: "/home", icon: Home, label: "Home" },
  { href: "/my-matches", icon: Trophy, label: "Matches" },
  { href: "#", icon: PlusCircle, label: "", fab: true },
  { href: "/wallet", icon: Wallet, label: "Wallet" },
  { href: "/profile", icon: User, label: "Profile" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around border-t border-[#2A2A4A] bg-[#16213E] px-2 pb-[env(safe-area-inset-bottom,0px)]">
      {tabs.map((tab) => {
        const active = pathname === tab.href;
        const Icon = tab.icon;

        if (tab.fab) {
          return (
            <Link key="fab" href="/home" className="-mt-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#E94560] shadow-lg">
              <PlusCircle className="h-6 w-6 text-white" />
            </Link>
          );
        }

        return (
          <Link key={tab.href} href={tab.href} className={`flex flex-col items-center py-2 px-3 ${active ? "text-[#E94560]" : "text-[#666666]"}`}>
            <Icon className="h-5 w-5" />
            <span className="mt-0.5 text-[10px]">{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
