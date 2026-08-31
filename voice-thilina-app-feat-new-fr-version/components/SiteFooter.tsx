import Image from "next/image";
import Link from "next/link";

const links = [
  { label: "Home", href: "/" },
  { label: "Assistant", href: "/request" },
  { label: "Chat", href: "/chat" },
  { label: "Providers", href: "/providers" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Docs", href: "/docs" },
];

export default function SiteFooter() {
  return (
    <footer className="site-footer" id="about">
      <div className="site-container py-6 sm:py-7">
        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="relative block h-9 w-[112px] shrink-0 overflow-hidden" aria-label="Servio home">
              <Image src="/servio-logo.png" alt="Servio" width={112} height={112} className="absolute left-0 top-[-36px] h-28 w-28 max-w-none" />
            </Link>
            <span className="hidden h-7 w-px bg-slate-200 sm:block" aria-hidden="true" />
            <p className="hidden max-w-xs text-xs leading-5 text-slate-500 sm:block">
              Smart local services, matched to your needs — by voice, text or photo.
            </p>
          </div>

          <nav aria-label="Footer navigation">
            <ul className="flex flex-wrap gap-x-5 gap-y-2 md:justify-end">
              {links.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-sm font-medium text-slate-600 transition-colors hover:text-blue-600">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>

      <div className="border-t border-slate-100 bg-slate-50/60">
        <div className="site-container flex flex-col gap-1.5 py-3 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Servio. All rights reserved.</p>
          <p>Verified providers · Intelligent matching · Local service</p>
        </div>
      </div>
    </footer>
  );
}
