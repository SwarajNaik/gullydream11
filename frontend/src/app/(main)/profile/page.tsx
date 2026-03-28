"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ProfilePage() {
  const router = useRouter();
  const user = typeof window !== "undefined" ? JSON.parse(localStorage.getItem("auth_user") || "{}") : {};

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_user");
    router.push("/login");
  };

  return (
    <div className="px-4 pt-6">
      <div className="flex flex-col items-center mb-6">
        <div className="h-20 w-20 rounded-full bg-[#0F3460] border-2 border-[#E94560] flex items-center justify-center text-2xl font-bold">
          {(user.display_name || "?")[0]}
        </div>
        <h1 className="mt-3 text-xl font-bold">{user.display_name || "Player"}</h1>
        <p className="text-sm text-[#9E9E9E]">@{user.username || "username"}</p>
        <p className="text-xs text-[#666666]">{user.email}</p>
      </div>

      <Card className="mb-4">
        <CardContent className="pt-4 grid grid-cols-2 gap-4">
          <div className="text-center"><p className="text-lg font-bold">0</p><p className="text-xs text-[#9E9E9E]">Matches</p></div>
          <div className="text-center"><p className="text-lg font-bold">0</p><p className="text-xs text-[#9E9E9E]">Contests</p></div>
          <div className="text-center"><p className="text-lg font-bold text-[#00C853]">₹0</p><p className="text-xs text-[#9E9E9E]">Winnings</p></div>
          <div className="text-center"><p className="text-lg font-bold">0</p><p className="text-xs text-[#9E9E9E]">Skill Score</p></div>
        </CardContent>
      </Card>

      <Button variant="destructive" className="w-full" onClick={handleLogout}>
        Logout
      </Button>
    </div>
  );
}
