export default function Skeleton({ className = "", variant = "text" }) {
  const base = "animate-pulse bg-slate-200 rounded-xl";
  const variants = {
    text: "h-4 w-full",
    title: "h-6 w-3/4",
    card: "h-48 w-full",
    avatar: "h-12 w-12 rounded-full",
    badge: "h-6 w-20 rounded-full",
    button: "h-12 w-full",
  };
  return <div className={`${base} ${variants[variant] || variant} ${className}`} />;
}

export function SchemeCardSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-6">
      <div className="flex items-start justify-between">
        <div className="h-12 w-12 rounded-xl bg-slate-200" />
        <div className="h-6 w-20 rounded-full bg-slate-200" />
      </div>
      <div className="mt-5 space-y-2">
        <div className="h-5 w-3/4 rounded bg-slate-200" />
        <div className="h-3 w-full rounded bg-slate-100" />
        <div className="h-3 w-5/6 rounded bg-slate-100" />
        <div className="h-3 w-2/3 rounded bg-slate-100" />
      </div>
      <div className="mt-6 space-y-3">
        <div className="h-3 w-1/2 rounded bg-slate-100" />
        <div className="h-3 w-1/3 rounded bg-slate-100" />
        <div className="h-3 w-1/2 rounded bg-slate-100" />
      </div>
      <div className="mt-8 h-12 w-full rounded-xl bg-slate-200" />
    </div>
  );
}

export function TableRowSkeleton({ cols = 6 }) {
  return (
    <tr className="border-b animate-pulse">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="p-4">
          <div className={`h-4 rounded bg-slate-200 ${i === 0 ? "w-3/4" : i < 3 ? "w-1/2" : "w-2/3"}`} />
        </td>
      ))}
    </tr>
  );
}

export function ReportSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="h-8 w-1/3 rounded bg-slate-200" />
      <div className="h-4 w-2/3 rounded bg-slate-100" />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
          <div className="h-6 w-1/2 rounded bg-slate-200" />
          <div className="space-y-2">
            <div className="h-3 w-full rounded bg-slate-100" />
            <div className="h-3 w-5/6 rounded bg-slate-100" />
          </div>
          <div className="flex gap-4">
            <div className="h-10 w-10 rounded-full bg-slate-200" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/3 rounded bg-slate-200" />
              <div className="h-3 w-full rounded bg-slate-100" />
            </div>
          </div>
          <div className="flex gap-4">
            <div className="h-10 w-10 rounded-full bg-slate-200" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/3 rounded bg-slate-200" />
              <div className="h-3 w-full rounded bg-slate-100" />
            </div>
          </div>
        </div>
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
          <div className="h-5 w-1/2 rounded bg-slate-200" />
          <div className="h-10 w-full rounded-xl bg-slate-200" />
          <div className="h-10 w-full rounded-xl bg-slate-200" />
          <div className="h-24 w-full rounded-xl bg-slate-200" />
        </div>
      </div>
    </div>
  );
}
