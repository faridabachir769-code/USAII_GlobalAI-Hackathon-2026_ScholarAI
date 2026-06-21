import clsx from "clsx";

export default function Input({
  label,
  error,
  className = "",
  ...props
}) {
  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}

      <input
        {...props}
        className={clsx(
          "h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none transition-all",
          "focus:border-blue-500 focus:ring-2 focus:ring-blue-100",
          error && "border-red-500",
          className
        )}
      />

      {error && (
        <p className="text-sm text-red-500">
          {error}
        </p>
      )}
    </div>
  );
}