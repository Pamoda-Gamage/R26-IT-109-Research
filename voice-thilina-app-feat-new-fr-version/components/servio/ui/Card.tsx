import type { ComponentPropsWithoutRef, ElementType, ReactNode } from "react";

/**
 * Shared card shell for the Servio site. Every panel/card previously repeated
 * `rounded-2xl border border-(--servio-border) bg-(--servio-surface) ...`
 * by hand, which let paddings/radii drift between components — this is the
 * one place that pattern now lives.
 */

type CardPadding = "none" | "tight" | "normal" | "roomy";

const PADDING: Record<CardPadding, string> = {
  none: "",
  tight: "p-2.5",
  normal: "p-4",
  roomy: "p-5 sm:p-6",
};

type CardOwnProps = {
  padding?: CardPadding;
  /** Adds a hover lift + focus ring for cards that act as links/buttons. */
  interactive?: boolean;
  /** Drop the border (e.g. tinted panels that sit on their own background). */
  bordered?: boolean;
  /**
   * Background class, e.g. "bg-(--servio-primary-soft)" for a tinted panel.
   * A dedicated prop (rather than passing it via `className`) because
   * Tailwind utilities of equal specificity are resolved by stylesheet
   * order, not by where they appear in the class string — appending a bg-*
   * class after the default one in `className` isn't guaranteed to win.
   */
  bg?: string;
  className?: string;
  children?: ReactNode;
};

type CardProps<E extends ElementType> = CardOwnProps & {
  as?: E;
} & Omit<ComponentPropsWithoutRef<E>, keyof CardOwnProps | "as">;

export default function Card<E extends ElementType = "div">({
  as,
  padding = "normal",
  interactive = false,
  bordered = true,
  bg = "bg-(--servio-surface)",
  className = "",
  children,
  ...rest
}: CardProps<E>) {
  const As = (as ?? "div") as ElementType;
  return (
    <As
      className={[
        "rounded-2xl shadow-(--servio-shadow)",
        bg,
        bordered ? "border border-(--servio-border)" : "",
        PADDING[padding],
        interactive
          ? "servio-focus transition hover:-translate-y-0.5 hover:shadow-lg"
          : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </As>
  );
}
