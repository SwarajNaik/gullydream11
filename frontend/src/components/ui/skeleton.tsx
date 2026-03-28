import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded bg-[#0F3460]", className)} />;
}

export function MatchCardSkeleton() {
  return (
    <div className="rounded-[12px] bg-[#0F3460] border border-[#2A2A4A] p-4 space-y-3">
      <Skeleton className="h-4 w-16" />
      <div className="flex justify-between">
        <Skeleton className="h-6 w-20" />
        <Skeleton className="h-6 w-8" />
        <Skeleton className="h-6 w-20" />
      </div>
      <Skeleton className="h-4 w-24 mx-auto" />
    </div>
  );
}
