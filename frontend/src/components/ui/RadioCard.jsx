import clsx from "clsx";

export default function RadioCard({
  title,
  description,
  icon: Icon,
  selected,
  onClick,
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "w-full rounded-2xl border p-5 text-left transition-all duration-200",
        selected
          ? "border-blue-600 bg-blue-50"
          : "border-slate-200 bg-white hover:border-blue-400"
      )}
    >
      {Icon && (
        <Icon
          className="mb-4 text-blue-600"
          size={30}
        />
      )}

      <h3 className="font-semibold text-slate-900">
        {title}
      </h3>

      <p className="mt-1 text-sm text-slate-500">
        {description}
      </p>
    </button>
  );
}