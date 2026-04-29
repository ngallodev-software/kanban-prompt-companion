import type React from "react";
import { forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Card = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-lg border border-border bg-surface-1 shadow-sm", className)} {...props} />
));

Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col gap-1.5 border-b border-divider px-4 py-3", className)} {...props} />
));

CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(({ className, ...props }, ref) => (
  <h3 ref={ref} className={cn("text-sm font-semibold tracking-tight text-text-primary", className)} {...props} />
));

CardTitle.displayName = "CardTitle";

export const CardDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(({ className, ...props }, ref) => (
  <p ref={ref} className={cn("text-sm leading-6 text-text-secondary", className)} {...props} />
));

CardDescription.displayName = "CardDescription";

export const CardContent = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("px-4 py-4", className)} {...props} />
));

CardContent.displayName = "CardContent";

export const CardFooter = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex items-center border-t border-divider px-4 py-3", className)} {...props} />
));

CardFooter.displayName = "CardFooter";
