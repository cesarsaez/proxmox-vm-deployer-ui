export default function TabButton({ active, onClick, icon: Icon, label, description }) {
  return (
    <button
      onClick={onClick}
      className={`
        py-4 px-1 border-b-2 font-medium text-sm flex items-center
        ${active
          ? 'border-blue-500 text-blue-500'
          : 'border-transparent text-dark-muted hover:text-dark-text hover:border-dark-border'
        }
      `}
    >
      <Icon className="h-5 w-5 mr-2" />
      <span>{label}</span>
      {description && (
        <span className="ml-2 text-xs bg-dark-bg px-2 py-1 rounded">
          {description}
        </span>
      )}
    </button>
  )
}
