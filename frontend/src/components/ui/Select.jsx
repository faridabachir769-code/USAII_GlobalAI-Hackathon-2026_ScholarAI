import clsx from "clsx";

export default function Select({
  label,
  options = [],
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

      <select
        {...props}
        className={clsx(
          "h-12 w-full rounded-xl border border-slate-300 bg-white px-4 outline-none",
          "focus:border-blue-500 focus:ring-2 focus:ring-blue-100",
          className
        )}
      >
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
          >
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}