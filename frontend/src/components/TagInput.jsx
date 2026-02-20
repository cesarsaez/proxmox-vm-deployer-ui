import { useState } from 'react'
import { XMarkIcon, PlusIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline'

export default function TagInput({ tags = [], onChange, disabled = false, helper }) {
  const [inputValue, setInputValue] = useState('')
  const [showHelper, setShowHelper] = useState(false)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault()
      addTag(inputValue.trim())
    } else if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
      // Remove last tag on backspace if input is empty
      removeTag(tags.length - 1)
    }
  }

  const addTag = (tag) => {
    // Validate tag (alphanumeric, hyphens, underscores)
    const validTag = tag.replace(/[^a-zA-Z0-9-_]/g, '')
    if (validTag && !tags.includes(validTag)) {
      onChange([...tags, validTag])
      setInputValue('')
    }
  }

  const removeTag = (index) => {
    const newTags = tags.filter((_, i) => i !== index)
    onChange(newTags)
  }

  const handleAddClick = () => {
    if (inputValue.trim()) {
      addTag(inputValue.trim())
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-medium text-dark-text">
          Tags
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

      <div className={`
        min-h-[42px] px-3 py-2 bg-dark-bg border border-dark-border rounded-lg
        focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}>
        <div className="flex flex-wrap gap-2">
          {/* Existing Tags */}
          {tags.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium bg-blue-900/30 text-blue-400 border border-blue-700"
            >
              {tag}
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeTag(index)}
                  className="ml-1.5 hover:text-blue-300"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              )}
            </span>
          ))}

          {/* Input for New Tags */}
          {!disabled && (
            <div className="flex items-center flex-1 min-w-[120px]">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={tags.length === 0 ? "Type a tag and press Enter..." : "Add tag..."}
                disabled={disabled}
                className="
                  flex-1 bg-transparent border-none outline-none
                  text-dark-text placeholder-dark-muted
                  text-sm
                "
              />
              {inputValue && (
                <button
                  type="button"
                  onClick={handleAddClick}
                  className="ml-2 text-blue-500 hover:text-blue-400"
                  title="Add tag"
                >
                  <PlusIcon className="h-5 w-5" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tag Count */}
      {tags.length > 0 && (
        <p className="mt-1 text-xs text-dark-muted">
          {tags.length} tag{tags.length !== 1 ? 's' : ''}
        </p>
      )}

      {/* Hint */}
      {!disabled && tags.length === 0 && (
        <p className="mt-1 text-xs text-dark-muted">
          Press Enter or click + to add tags. Use alphanumeric characters, hyphens, and underscores.
        </p>
      )}
    </div>
  )
}
