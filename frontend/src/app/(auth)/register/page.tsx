"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { useRegister } from "@/hooks/api/use-auth";

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegister();
  const [form, setForm] = useState({ display_name: "", email: "", username: "", password: "", confirm: "" });
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) { setError("Passwords don't match"); return; }
    if (form.password.length < 6) { setError("Password must be 6+ chars"); return; }

    register.mutate(form, {
      onSuccess: (data: any) => {
        const d = data?.data;
        if (d?.access_token) {
          localStorage.setItem("access_token", d.access_token);
          localStorage.setItem("auth_user", JSON.stringify(d));
          window.location.href = "/home";
        }
      },
      onError: (err: any) => setError(err.message || "Registration failed"),
    });
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Display Name" value={form.display_name} onChange={e => setForm(p => ({ ...p, display_name: e.target.value }))} required />
          <Input label="Email" type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} required />
          <Input label="Username" value={form.username} onChange={e => setForm(p => ({ ...p, username: e.target.value }))} required />
          <Input label="Password" type="password" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} required />
          <Input label="Confirm Password" type="password" value={form.confirm} onChange={e => setForm(p => ({ ...p, confirm: e.target.value }))} required />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button type="submit" className="w-full" disabled={register.isPending}>
            {register.isPending ? "Creating Account..." : "Register"}
          </Button>
          <p className="text-center text-sm text-[#9E9E9E]">
            Already have an account? <Link href="/login" className="text-[#E94560]">Login</Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
