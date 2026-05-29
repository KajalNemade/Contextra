import { useState, useRef } from 'react'

interface Props {
  onSearch: (q: string) => void
  loading?: boolean
  placeholder?: string
}

export default function SearchBar({ onSearch, loading = false, placeholder = 'Search code…' }: Props) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const submit = () => {
    const q = value.trim()
    if (q) onSearch(q)
  }

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">🔍</span>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && submit()}
          placeholder={placeholder}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
        />
      </div>
      <button
        onClick={submit}
        disabled={loading || !value.trim()}
        className="btn-primary px-5"
      >
        {loading ? '…' : 'Search'}
      </button>
    </div>
  )
}
