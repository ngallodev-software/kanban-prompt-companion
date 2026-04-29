import type React from "react";
import { forwardRef } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "default" | "secondary" | "ghost" | "outline" | "danger";
type ButtonSize = "sm" | "md" | "lg" | "icon";

const baseClassName =
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-0 " +
  "disabled:pointer-events-none disabled:opacity-50";

const variantClassName: Record<ButtonVariant, string> = {
  default: "bg-accent text-accent-fg hover:bg-accent-hover shadow-sm",
  secondary: "bg-surface-2 text-text-primary hover:bg-surface-3 border border-border",
  ghost: "bg-transparent text-text-secondary hover:bg-surface-2 hover:text-text-primary",
  outline: "border border-border bg-surface-1 text-text-primary hover:bg-surface-2",
  danger: "bg-status-red text-white hover:opacity-90",
};

const sizeClassName: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4",
  lg: "h-11 px-5 text-base",
  icon: "h-9 w-9",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", type = "button", ...props }, ref) => {
    return <button ref={ref} type={type} className={cn(baseClassName, variantClassName[variant], sizeClassName[size], className)} {...props} />;
  },
);

Button.displayName = "Button";
