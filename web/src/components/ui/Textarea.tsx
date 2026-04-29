import type React from "react";
import { forwardRef } from "react";

import { cn } from "@/lib/cn";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-24 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-text-primary shadow-sm transition-colors",
        "placeholder:text-text-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-0",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
});

Textarea.displayName = "Textarea";
