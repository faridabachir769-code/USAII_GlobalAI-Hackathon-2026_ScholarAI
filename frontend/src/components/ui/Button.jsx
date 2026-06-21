import clsx from "clsx";

export default function Button({
  children,
  type = "button",
  variant = "primary",
  fullWidth = false,
  disabled = false,
  onClick,
  className = "",
}) {
  const variants = {
    primary:
      "bg-slate-900 text-white hover:bg-slate-800",

    secondary:
      "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50",

    outline:
      "border border-blue-600 text-blue-600 hover:bg-blue-50",

    danger:
      "bg-red-600 text-white hover:bg-red-700",
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={clsx(
        "h-12 rounded-xl px-6 font-medium transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        fullWidth && "w-full",
        className
      )}
    >
      {children}
    </button>
  );
}