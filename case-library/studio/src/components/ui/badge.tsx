import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

// shadcn/ui Badge, with tones for statuses and licence flags.
const badgeVariants = cva(
  "inline-flex items-center whitespace-nowrap rounded-md border px-1.5 py-0.5 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "border-neutral-300 bg-neutral-100 text-neutral-800",
        info: "border-sky-200 bg-sky-50 text-sky-800",
        success: "border-emerald-200 bg-emerald-50 text-emerald-800",
        warning: "border-amber-200 bg-amber-50 text-amber-900",
        danger: "border-red-300 bg-red-50 text-red-700",
        muted: "border-neutral-200 bg-white text-neutral-500",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>;

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span data-slot="badge" className={cn(badgeVariants({ tone }), className)} {...props} />;
}
