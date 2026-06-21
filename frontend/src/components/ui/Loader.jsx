export default function Loader({
  size = "md",
  text = "",
}) {
  const sizes = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-10 w-10",
  };

  return (
    <div className="flex items-center justify-center gap-3">
      <div
        className={`
          animate-spin rounded-full
          border-2 border-slate-300 border-t-slate-900
          ${sizes[size]}
        `}
      />

      {text && (
        <span className="text-sm text-slate-600">
          {text}
        </span>
      )}
    </div>
  );
}