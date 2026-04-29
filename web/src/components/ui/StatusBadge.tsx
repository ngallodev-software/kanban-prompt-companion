import { Badge } from "@/components/ui/Badge";

export type StatusTone = "blue" | "green" | "orange" | "red" | "purple" | "cyan";

const toneColor: Record<StatusTone, string> = {
  blue: "var(--status-blue)",
  green: "var(--status-green)",
  orange: "var(--status-orange)",
  red: "var(--status-red)",
  purple: "var(--status-purple)",
  cyan: "var(--status-cyan)",
};

export function StatusBadge({ label, tone = "blue" }: { label: string; tone?: StatusTone }) {
  return <Badge variant="outline" style={{ borderColor: toneColor[tone], color: toneColor[tone] }}>{label}</Badge>;
}
