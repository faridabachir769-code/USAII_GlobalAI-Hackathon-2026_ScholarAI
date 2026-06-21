export default function PageHeader({
  title,
  subtitle,
}) {
  return (
    <div className="space-y-2">
      <h1 className="text-3xl font-bold text-slate-900">
        {title}
      </h1>

      <p className="text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}