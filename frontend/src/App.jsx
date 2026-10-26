import { useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import OverviewPage from "@/pages/OverviewPage";
import AnalystPage from "@/pages/AnalystPage";
import DocumentsPage from "@/pages/DocumentsPage";
import { useDatasetQuery } from "@/services/queries";

export default function App() {
  const [active, setActive] = useState("Overview");
  const [initialQuestion, setInitialQuestion] = useState("");
  const { data } = useDatasetQuery();
  const recordCount = data?.kpis?.rows ?? data?.rows ?? 0;
  return <AppLayout active={active} setActive={setActive} recordCount={recordCount}>
    {active === "Overview" && <OverviewPage setActive={setActive} onAskQuestion={(question) => { setInitialQuestion(question); setActive("AI Analyst"); }}/>}
    {active === "AI Analyst" && <AnalystPage initialQuestion={initialQuestion} onQuestionConsumed={() => setInitialQuestion("")}/> }
    {active === "Documents" && <DocumentsPage/>}
  </AppLayout>;
}
