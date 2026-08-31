"use client";

import Image from "next/image";
import Link from "next/link";
import { LayoutDashboard, LogOut, Menu, X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import LanguageMenu from "./servio/LanguageMenu";
import { clearSession, isAuthed } from "@/lib/auth";

const links = [
  { label: "Home", href: "/" },
  { label: "Assistant", href: "/request" },
  { label: "Chat", href: "/chat" },
  { label: "Providers", href: "/providers" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Docs", href: "/docs" },
];

function Brand() {
  return (
    <Link href="/" className="relative block h-12 w-[150px] shrink-0 overflow-hidden" aria-label="Servio home">
      <Image
        src="/servio-logo.png"
        alt="Servio"
        width={150}
        height={150}
        priority
        className="absolute left-0 top-[-48px] h-[150px] w-[150px] max-w-none"
      />
    </Link>
  );
}

export default function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [authed, setAuthed] = useState(false);

  // localStorage isn't available during SSR; sync on mount and on route change
  // (login/logout redirect through a navigation).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAuthed(isAuthed());
  }, [pathname]);

  const handleLogout = () => {
    clearSession();
    setAuthed(false);
    setOpen(false);
    router.push("/");
  };

  return (
    <header className="site-header">
      <div className="site-container flex h-[76px] items-center justify-between gap-5">
        <Brand />

        <nav className="hidden items-center gap-7 lg:flex" aria-label="Main navigation">
          {links.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link key={link.label} href={link.href} className={`nav-link ${active ? "nav-link-active" : ""}`}>
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden items-center gap-4 md:flex">
          <LanguageMenu />
          {authed ? (
            <>
              <Link
                href="/dashboard"
                className="flex items-center gap-1.5 text-sm font-medium text-[#003e92] hover:text-[#087cf0]"
              >
                <LayoutDashboard size={16} /> Account
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-[#087cf0]"
              >
                <LogOut size={16} /> Logout
              </button>
            </>
          ) : (
            <Link href="/auth/login" className="text-sm font-medium text-[#003e92] hover:text-[#087cf0]">
              Login
            </Link>
          )}
          <Link href="/request" className="servio-button">
            Find a Service
          </Link>
        </div>

        <button
          type="button"
          className="rounded-lg p-2 text-[#003e92] hover:bg-blue-50 lg:hidden"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {open && (
        <nav className="border-t border-slate-100 bg-white px-5 py-4 shadow-lg lg:hidden" aria-label="Mobile navigation">
          <div className="site-container flex flex-col gap-1">
            {links.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm text-slate-700 hover:bg-blue-50 hover:text-[#0059bf]"
              >
                {link.label}
              </Link>
            ))}
            <div className="mt-3 flex items-center gap-4 border-t border-slate-100 pt-4">
              {authed ? (
                <button type="button" onClick={handleLogout} className="px-3 text-sm font-medium text-slate-500">
                  Logout
                </button>
              ) : (
                <Link href="/auth/login" onClick={() => setOpen(false)} className="px-3 text-sm font-medium text-[#003e92]">
                  Login
                </Link>
              )}
              <Link href="/request" onClick={() => setOpen(false)} className="servio-button">
                Find a Service
              </Link>
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
