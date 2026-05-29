const STATUS_STYLES: Record<string, string> = {
  QUEUED:      'bg-gray-700 text-gray-300',
  SANITIZING:  'bg-yellow-900 text-yellow-300',
  INDEXING:    'bg-blue-900 text-blue-300',
  PARSING:     'bg-blue-900 text-blue-300',
  GRAPHING:    'bg-purple-900 text-purple-300',
  EMBEDDING:   'bg-indigo-900 text-indigo-300',
  SUMMARIZING: 'bg-indigo-900 text-indigo-300',
  READY:       'bg-green-900 text-green-300',
  FAILED:      'bg-red-900 text-red-300',
  STALE:       'bg-orange-900 text-orange-300',
}

const STATUS_DOTS: Record<string, string> = {
  QUEUED:      '⏳',
  SANITIZING:  '🔒',
  INDEXING:    '📥',
  PARSING:     '🔬',
  GRAPHING:    '🕸',
  EMBEDDING:   '🧠',
  SUMMARIZING: '📝',
  READY:       '✅',
  FAILED:      '❌',
  STALE:       '⚠️',
}

export default function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? 'bg-gray-700 text-gray-300'
  const dot = STATUS_DOTS[status] ?? '•'
  return (
    <span className={`badge ${style}`}>
      <span className="mr-1">{dot}</span>
      {status}
    </span>
  )
}
