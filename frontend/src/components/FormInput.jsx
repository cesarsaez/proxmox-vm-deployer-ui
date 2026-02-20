import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'

export default function FormInput({
  label,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  helper,
  min,
  max,
  disabled = false
}) {
  const [showHelper, setShowHelper] = useState(false)

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label htmlFor={name} className="block text-sm font-medium text-dark-text">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
        {helper && (
          <div className="relative">
            <button
              type="button"
              onMouseEnter={() => setShowHelper(true)}
              onMouseLeave={() => setShowHelper(false)}
              className="text-dark-muted hover:text-dark-text"
            >
              <QuestionMarkCircleIcon className="h-5 w-5" />
            </button>
            {showHelper && (
              <div className="absolute right-0 mt-2 w-64 bg-dark-surface border border-dark-border rounded-lg p-3 shadow-lg z-10">
                <p className="text-sm text-dark-muted">{helper}</p>
              </div>
            )}
          </div>
        )}
      </div>
      <input
        type={type}
        name={name}
        id={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        min={min}
        max={max}
        disabled={disabled}
        className="
          w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg
          text-dark-text placeholder-dark-muted
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed
        "
      />
    </div>
  )
}
