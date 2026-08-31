"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MATCH_API_BASE } from "@/lib/match-api";
import { storeSession } from "@/lib/auth";

export default function UserRegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({ name: "", email: "", password: "", phone: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!formData.name || !formData.email || !formData.password) {
      setError("Please fill in all required fields");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${MATCH_API_BASE}/auth/user/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          password: formData.password,
          phone: formData.phone || null,
        }),
      });

      if (!res.ok) {
        setError("Registration failed");
        return;
      }

      storeSession(await res.json());
      router.push("/request");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col gap-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold">Create Account</h1>
        <p className="text-sm text-muted-foreground">Sign up to find and request services</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create a new account</CardTitle>
          <CardDescription>Fill in your details to get started</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleRegister} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Full name *</label>
              <Input type="text" name="name" placeholder="John Doe" value={formData.name} onChange={handleChange} disabled={loading} />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Email *</label>
              <Input type="email" name="email" placeholder="your@email.com" value={formData.email} onChange={handleChange} disabled={loading} />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Password *</label>
              <Input type="password" name="password" placeholder="••••••••" value={formData.password} onChange={handleChange} disabled={loading} />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Phone (optional)</label>
              <Input type="tel" name="phone" placeholder="+94..." value={formData.phone} onChange={handleChange} disabled={loading} />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Creating account..." : "Create account"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/auth/login" className="underline hover:text-foreground">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
