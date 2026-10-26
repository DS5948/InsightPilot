export default function SuggestionChips({ prompts, onSelect }) {
  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {prompts.map((p) => (
        <button key={p} onClick={() => onSelect(p)} className="suggestion">
          {p}
        </button>
      ))}
    </div>
  );
}
