import { CheckCircle2, XCircle } from "lucide-react";

import Card from "../ui/Card";

export default function ComparisonCard({
  title,
  description,
  isMatch = true,
}) {
  const Icon = isMatch ? CheckCircle2 : XCircle;
  const iconColor = isMatch
    ? "text-green-600"
    : "text-red-500";

  return (
    <Card className="p-5">
      <div className="flex gap-3">
        <Icon className={`mt-1 ${iconColor}`} size={20} />

        <div>
          <h4 className="font-semibold text-slate-900">
            {title}
          </h4>

          <p className="mt-1 text-sm text-slate-500">
            {description}
          </p>
        </div>
      </div>
    </Card>
  );
}
