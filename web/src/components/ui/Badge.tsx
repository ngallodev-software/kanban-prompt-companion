import type React from "react";
import { forwardRef } from "react";

import { cn } from "@/lib/cn";

type BadgeVariant = "default" | "secondary" | "outline" | "danger";

const variantClassName: Record<BadgeVariant, string> = {
  default: "border-transparent bg-accent text-accent-fg",
  secondary: "border border-border bg-surface-2 text-text-primary",
  outline: "border border-border bg-transparent text-text-secondary",
  danger: "border-transparent bg-status-red text-white",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
}

export const Badge = forwardRef<HTMLDivElement, BadgeProps>(({ className, variant = "default", ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium leading-none",
        variantClassName[variant],
        className,
      )}
      {...props}
    />
  );
});

Badge.displayName = "Badge";
