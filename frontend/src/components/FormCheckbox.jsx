export default function FormCheckbox({
  label,
  name,
  checked,
  onChange,
  description,
  disabled = false
}) {
  return (
    <div className="flex items-start">
      <div className="flex items-center h-5">
        <input
          type="checkbox"
          name={name}
          id={name}
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          className="
            h-4 w-4 rounded border-dark-border bg-dark-bg
            text-blue-500 focus:ring-2 focus:ring-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
          "
        />
      </div>
      <div className="ml-3 text-sm">
        <label htmlFor={name} className="font-medium text-dark-text">
          {label}
        </label>
        {description && (
          <p className="text-dark-muted">{description}</p>
        )}
      </div>
    </div>
  )
}
