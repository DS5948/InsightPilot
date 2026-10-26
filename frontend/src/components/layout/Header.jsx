import { ChevronDown, Menu, X } from "lucide-react";
import Brand from "@/components/layout/Brand";

export default function Header({ active, onMenuClick, isMenuOpen }) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-white/[0.07] px-5 sm:px-8">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="text-slate-400 lg:hidden"
          aria-label={isMenuOpen ? "Close sidebar" : "Open sidebar"}
        >
          {isMenuOpen ? <X /> : <Menu />}
        </button>

        <div className="lg:hidden">
          <Brand />
        </div>

        <div className="hidden text-sm text-slate-500 sm:block">
          Workspace <span className="mx-2 text-slate-700">/</span>{" "}
          <span className="text-slate-200">{active}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="hidden items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300 hover:bg-white/5 sm:flex">
          <div className="size-2 rounded-full bg-emerald-400" />
          All systems operational
          <ChevronDown className="size-3.5" />
        </button>
      </div>
    </header>
  );
}
