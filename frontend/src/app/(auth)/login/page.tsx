"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { useLogin } from "@/hooks/api/use-auth";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const [form, setForm] = useState({ email_or_username: "", password: "" });
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    login.mutate(form, {
      onSuccess: (data: any) => {
        const d = data?.data;
        if (d?.access_token) {
          localStorage.setItem("access_token", d.access_token);
          localStorage.setItem("auth_user", JSON.stringify(d));
          window.location.href = "/home";
        } else {
          setError("Login failed — no token received");
        }
      },
      onError: (err: any) => {
        setError(err.message || "Invalid credentials");
      },
    });
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Email or Username" value={form.email_or_username} onChange={e => setForm(p => ({ ...p, email_or_username: e.target.value }))} required />
          <Input label="Password" type="password" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} required />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button type="submit" className="w-full" disabled={login.isPending}>
            {login.isPending ? "Logging in..." : "Login"}
          </Button>
          <p className="text-center text-sm text-[#9E9E9E]">
            New here? <Link href="/register" className="text-[#E94560]">Register</Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
