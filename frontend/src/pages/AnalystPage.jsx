import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import ChatWelcome from "@/components/analyst/ChatWelcome";
import ChatMessage from "@/components/analyst/ChatMessage";
import TypingIndicator from "@/components/analyst/TypingIndicator";
import SuggestionChips from "@/components/analyst/SuggestionChips";
import ChatComposer from "@/components/analyst/ChatComposer";
import { suggestedPrompts } from "@/constants/prompts";
import { useChatMutation } from "@/services/queries";

export default function AnalystPage({ initialQuestion = "", onQuestionConsumed }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const chat = useChatMutation();
  const scrollRef = useRef(null);
  const consumedQuestion = useRef("");

  // Keep the newest message in view; only the message list scrolls, not the page.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages.length, chat.isPending]);

  const ask = async (text) => {
    const question = text.trim();
    if (!question || chat.isPending) return;
    setMessages((current) => [...current, { role: "user", text: question }]);
    setInput("");
    try {
      const result = await chat.mutateAsync({ question, mode: "auto" });
      setMessages((current) => [...current, {
        role: "assistant",
        text: result.answer || "The API returned no answer.",
        sources: result.sources || [],
        route: result.route,
        warnings: result.warnings || [],
        chart: result.chart || null,
      }]);
    } catch (error) {
      setMessages((current) => [...current, { role: "assistant", text: `Unable to get an answer: ${error.message}` }]);
    }
  };

  useEffect(() => {
    if (initialQuestion && consumedQuestion.current !== initialQuestion) {
      consumedQuestion.current = initialQuestion;
      ask(initialQuestion);
      onQuestionConsumed?.();
    }
  }, [initialQuestion]);

  return (
    <div className="flex h-[calc(100dvh-4rem)] flex-col overflow-hidden p-5 sm:p-8">
      <PageHeader
        className="mb-6 flex shrink-0 items-start justify-between"
        eyebrow="Intelligence layer"
        title="AI Analyst"
        description="Ask questions about your active dataset and indexed business documents."
        action={<button onClick={() => setMessages([])} className="button-secondary"><X data-icon="inline-start" /> Clear</button>}
      />
      <div className="mx-auto flex min-h-0 w-full max-w-4xl flex-1 flex-col">
        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto py-4 pr-1">
          {messages.length === 0 ? <ChatWelcome /> : messages.map((message, index) => <ChatMessage key={index} role={message.role} text={message.text} sources={message.sources} route={message.route} warnings={message.warnings} chart={message.chart} />)}
          {chat.isPending && <TypingIndicator />}
        </div>
        {messages.length === 0 && <SuggestionChips prompts={suggestedPrompts} onSelect={ask} />}
        <ChatComposer value={input} onChange={setInput} onSubmit={ask} loading={chat.isPending} />
        <div className="mt-3 shrink-0 text-center text-[10px] text-slate-600">AI-generated insights may be incomplete. Verify important decisions against source data.</div>
      </div>
    </div>
  );
}