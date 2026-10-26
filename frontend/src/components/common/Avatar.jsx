import { User } from "lucide-react";

export default function Avatar({ className = "" }) {
  return (
    <div
      className={`flex size-8 items-center justify-center rounded-full border border-violet-300/20 bg-violet-400/10 text-violet-200 ${className}`}
    >
      <User className="size-4" />
    </div>
  );
}
