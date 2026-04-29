import type React from "react";
import { forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Table = forwardRef<HTMLTableElement, React.TableHTMLAttributes<HTMLTableElement>>(({ className, ...props }, ref) => (
  <div className="w-full overflow-hidden rounded-lg border border-border bg-surface-1">
    <table ref={ref} className={cn("w-full caption-bottom text-sm", className)} {...props} />
  </div>
));

Table.displayName = "Table";

export const TableHeader = forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(({ className, ...props }, ref) => (
  <thead ref={ref} className={cn("border-b border-divider", className)} {...props} />
));

TableHeader.displayName = "TableHeader";

export const TableBody = forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(({ className, ...props }, ref) => (
  <tbody ref={ref} className={cn("[&_tr:last-child]:border-0", className)} {...props} />
));

TableBody.displayName = "TableBody";

export const TableRow = forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(({ className, ...props }, ref) => (
  <tr ref={ref} className={cn("border-b border-divider transition-colors hover:bg-surface-2", className)} {...props} />
));

TableRow.displayName = "TableRow";

export const TableHead = forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(({ className, ...props }, ref) => (
  <th ref={ref} className={cn("h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-text-tertiary", className)} {...props} />
));

TableHead.displayName = "TableHead";

export const TableCell = forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(({ className, ...props }, ref) => (
  <td ref={ref} className={cn("px-4 py-3 align-middle text-sm text-text-primary", className)} {...props} />
));

TableCell.displayName = "TableCell";
