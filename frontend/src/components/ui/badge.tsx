import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "red" | "green" | "yellow" | "live" | "wk" | "bat" | "ar" | "bowl";
  className?: string;
}

const variantStyles: Record<string, string> = {
  default: "bg-[#2A2A4A] text-[#9E9E9E]",
  red: "bg-[#E94560] text-white",
  green: "bg-[#00C853] text-white",
  yellow: "bg-[#FFD600] text-black",
  live: "bg-[#E94560] text-white animate-pulse",
  wk: "bg-[#FF6B6B]/20 text-[#FF6B6B]",
  bat: "bg-[#4ECDC4]/20 text-[#4ECDC4]",
  ar: "bg-[#45B7D1]/20 text-[#45B7D1]",
  bowl: "bg-[#96CEB4]/20 text-[#96CEB4]",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", variantStyles[variant], className)}>
      {children}
    </span>
  );
}

export function RoleBadge({ role }: { role: string }) {
  const v = role.toLowerCase() as "wk" | "bat" | "ar" | "bowl";
  return <Badge variant={v}>{role}</Badge>;
}
