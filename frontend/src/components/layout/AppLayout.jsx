import { useState } from "react";

import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function AppLayout({
  active,
  setActive,
  recordCount,
  children,
}) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="h-screen overflow-hidden bg-[#080d14]">
      <Sidebar
        active={active}
        setActive={setActive}
        recordCount={recordCount}
        isMenuOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
      />
      <main className="h-screen overflow-y-auto lg:ml-64">
        <Header
          active={active}
          isMenuOpen={isMenuOpen}
          onMenuClick={() => setIsMenuOpen((open) => !open)}
        />
        {children}
      </main>
    </div>
  );
}
