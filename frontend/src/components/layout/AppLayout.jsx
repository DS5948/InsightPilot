import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function AppLayout({ active, setActive, recordCount, children }) {
  return (
    <div className="app-shell">
      <Sidebar active={active} setActive={setActive} recordCount={recordCount} />
      <main className="min-w-0 flex-1">
        <Header active={active} />
        {children}
      </main>
    </div>
  );
}
