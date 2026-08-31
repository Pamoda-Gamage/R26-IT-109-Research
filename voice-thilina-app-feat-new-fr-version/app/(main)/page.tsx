import Link from "next/link";
import {
  Mic,
  ArrowRight,
  MessageSquareText,
  BrainCircuit,
  MapPin,
  Zap,
  Droplet,
  Hammer,
  PaintBucket,
  Sprout,
  Snowflake,
  Tv,
  Laptop,
  Smartphone,
  Wifi,
  Car,
  Bug,
  Wrench,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

const STEPS = [
  {
    icon: MessageSquareText,
    title: "Speak your request",
    body: "Describe the problem in Sinhala, Tamil, English or a mix — a sentence is enough.",
  },
  {
    icon: BrainCircuit,
    title: "AI understands the situation",
    body: "It works out the service type, how urgent it is, and the context from your words or a photo.",
  },
  {
    icon: MapPin,
    title: "Get matched to a provider",
    body: "It ranks nearby professionals by ETA, availability, rating and reliability, and connects you.",
  },
];

const SERVICES = [
  { icon: Droplet, label: "Plumber" },
  { icon: Zap, label: "Electrician" },
  { icon: Wrench, label: "Mechanic" },
  { icon: Snowflake, label: "AC Technician" },
  { icon: Hammer, label: "Carpenter" },
  { icon: PaintBucket, label: "Painter" },
  { icon: Sprout, label: "Gardener" },
  { icon: Tv, label: "TV Repair" },
  { icon: Laptop, label: "Computer Repair" },
  { icon: Smartphone, label: "Phone Repair" },
  { icon: Wifi, label: "Network / Internet" },
  { icon: Car, label: "Battery / Jump Start" },
  { icon: Bug, label: "Pest Control" },
  { icon: Hammer, label: "Mason" },
];

export const metadata = {
  title: "Servio — Smart Local Services",
  description:
    "Find the right local service just by speaking. Servio understands your request, urgency and context, then matches you to the best nearby provider.",
};

export default function LandingPage() {
  return (
    <>
      {/* ---------------- HERO ---------------- */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 -top-40 h-[420px] bg-gradient-to-b from-secondary to-transparent" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-5 pb-20 pt-16 md:grid-cols-2 md:pt-24">
          <div>
            <h1 className="text-balance text-4xl font-bold leading-[1.1] tracking-tight text-[#082454] sm:text-5xl">
              Find the Right Local Service,{" "}
              <span className="text-primary">Just by Speaking.</span>
            </h1>
            <p className="mt-5 max-w-md text-[15px] leading-relaxed text-muted-foreground">
              Tell us what you need in Sinhala, Tamil, English, or mixed language. Servio
              understands your request, urgency, location and context, then matches you to the
              most suitable nearby service provider.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/request"
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition hover:bg-[#004fae]"
              >
                <Mic className="h-4 w-4" /> Speak Your Request
              </Link>
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 rounded-xl border border-[#9ec9eb] bg-white px-5 py-3 text-sm font-semibold text-[#0758ad] transition hover:border-[#1685ed] hover:bg-[#eaf5ff]"
              >
                Open the assistant chat <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>

          <div className="relative">
            <Card className="p-6">
              <CardContent className="p-0">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  How it works
                </p>
                <ol className="mt-4 flex flex-col gap-4">
                  {STEPS.map((step, i) => (
                    <li key={step.title} className="flex items-start gap-3">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-bold text-secondary-foreground">
                        {i + 1}
                      </span>
                      <div>
                        <p className="flex items-center gap-2 text-sm font-semibold text-[#082454]">
                          <step.icon className="h-4 w-4 text-primary" /> {step.title}
                        </p>
                        <p className="mt-0.5 text-[13px] leading-relaxed text-muted-foreground">
                          {step.body}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ---------------- SERVICES ---------------- */}
      <section id="services" className="mx-auto max-w-6xl px-5 pb-20">
        <h2 className="text-2xl font-bold tracking-tight text-[#082454]">
          One assistant for every local job
        </h2>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground">
          From a burst pipe to a broken laptop — describe it and Servio routes it to the right
          nearby professional.
        </p>
        <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {SERVICES.map((service) => (
            <div
              key={service.label}
              className="flex items-center gap-3 rounded-xl border border-[#d6e8f5] bg-white px-4 py-3 text-sm font-medium text-[#082454] shadow-sm"
            >
              <service.icon className="h-4 w-4 text-primary" /> {service.label}
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- RESEARCH CTA ---------------- */}
      <section id="how-it-works" className="border-t border-slate-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-4 px-5 py-14 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-[#082454]">
              Adaptive matching, in the open
            </h2>
            <p className="mt-1 max-w-lg text-sm text-muted-foreground">
              The ranking model learns from every selection. Watch its weight profiles converge
              live on the dashboard, or manage the provider directory as an admin.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/research-dashboard.html"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition hover:bg-[#004fae]"
            >
              Live dashboard <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/providers"
              className="inline-flex items-center gap-2 rounded-xl border border-[#9ec9eb] bg-white px-5 py-3 text-sm font-semibold text-[#0758ad] transition hover:border-[#1685ed] hover:bg-[#eaf5ff]"
            >
              Provider admin
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
