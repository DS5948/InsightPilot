import { Upload } from "lucide-react";

export default function FileUploadButton({
  label,
  accept,
  multiple = false,
  onChange,
}) {
  return (
    <label className="button-primary cursor-pointer">
      <Upload data-icon="inline-start" />
      {label}
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={onChange}
      />
    </label>
  );
}
