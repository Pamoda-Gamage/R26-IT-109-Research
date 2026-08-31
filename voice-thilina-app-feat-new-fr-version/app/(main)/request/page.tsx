import UnifiedRequest from "../../../components/request/UnifiedRequest";

export const metadata = {
  title: "Speak Your Request",
  description:
    "Describe what you need by voice, text or photo — Servio classifies it and matches you to a nearby provider.",
};

export default function RequestPage() {
  return <UnifiedRequest />;
}
