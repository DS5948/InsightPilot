import Brand from "@/components/layout/Brand";
import DataHealthCard from "@/components/layout/DataHealthCard";
import { navItems } from "@/constants/navigation";

export default function Sidebar({
  active,
  setActive,
  recordCount,
  isMenuOpen,
  onClose,
}) {
  return (
    <>
      {/* Mobile backdrop */}
      {isMenuOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={onClose}
          aria-label="Close sidebar"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 shrink-0 flex-col overflow-y-auto border-r border-white/[0.07] bg-[#0b1017] p-5 transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMenuOpen
            ? "translate-x-0"
            : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <Brand />

        <div className="mt-10 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-600">
          Workspace
        </div>

        <nav className="mt-3 flex flex-col gap-1">
          {navItems.map(({ name, icon: Icon }) => (
            <button
              key={name}
              onClick={() => {
                setActive(name);
                onClose?.();
              }}
              className={`nav-item ${
                active === name ? "nav-item-active" : ""
              }`}
            >
              <Icon />

              {name}

              {name === "AI Analyst" && (
                <span className="ml-auto rounded-full bg-cyan-400/10 px-1.5 py-0.5 text-[9px] text-cyan-300">
                  BETA
                </span>
              )}
            </button>
          ))}
        </nav>

        <DataHealthCard synced={recordCount} />
      </aside>
    </>
  );
}
