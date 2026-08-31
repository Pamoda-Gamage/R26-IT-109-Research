import type { ReactNode } from "react";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";

export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main className="servio-page min-w-0 flex-1">{children}</main>
      <SiteFooter />
    </>
  );
}
