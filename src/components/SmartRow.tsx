type SmartRowProps = {
  items: string[];
};

export function SmartRow({ items }: SmartRowProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-card px-6 py-4 text-sm text-muted-foreground shadow-sm">
      <span className="text-xs font-semibold uppercase tracking-[0.2em] text-foreground">
        Active focus
      </span>
      {items.map((item) => (
        <span
          key={item}
          className="rounded-full border border-border bg-background px-3 py-1 text-xs text-foreground"
        >
          {item}
        </span>
      ))}
    </div>
  );
}
