import { Paperclip, Send } from "lucide-react";

export default function ChatComposer({ value, onChange, onSubmit, loading }) {
  return (
    <div className="chat-composer">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (
            e.key === "Enter" &&
            !e.shiftKey &&
            !e.nativeEvent.isComposing &&
            e.keyCode !== 229
          ) {
            e.preventDefault();
            onSubmit(value);
          }
        }}
        placeholder="Ask about your business..."
        rows={2}
      />
      <div className="flex items-center justify-between">
        <button className="icon-button">
          <Paperclip />
        </button>
        <button
          onClick={() => onSubmit(value)}
          disabled={loading || !value.trim()}
          className="send-button"
        >
          <Send />
        </button>
      </div>
    </div>
  );
}
