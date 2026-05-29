import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { askApi } from '../services/api'
import type { AskResponse } from '../types/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  meta?: {
    provider: string
    confidence: string
    sources: string[]
    chunks_used: number
  }
}

const CONFIDENCE_COLOR: Record<string, string> = {
  high:   'text-green-400',
  medium: 'text-yellow-400',
  low:    'text-gray-500',
}

const PROVIDER_ICON: Record<string, string> = {
  ollama:      '🦙 Ollama',
  gemini:      '✨ Gemini',
  search_only: '🔍 Search only',
  none:        '—',
}

const SAMPLE_QUESTIONS = [
  'What does this project do?',
  'How is authentication handled?',
  'Where is the database connection set up?',
  'What are the main entry points?',
  'How does error handling work?',
]

export default function AskPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const repoId = Number(id)

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (q?: string) => {
    const question = (q ?? input).trim()
    if (!question || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const result: AskResponse = await askApi.ask(repoId, question)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.answer,
        meta: {
          provider:    result.provider,
          confidence:  result.confidence,
          sources:     result.sources,
          chunks_used: result.chunks_used,
        },
      }])
    } catch (e: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${e?.response?.data?.detail ?? 'Request failed. Is the repo ready?'}`,
      }])
    } finally {
      setLoading(false)
      textareaRef.current?.focus()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-800 flex-shrink-0">
        <button onClick={() => navigate(`/repo/${id}`)} className="text-gray-500 hover:text-white text-xs">
          ←
        </button>
        <div>
          <h1 className="text-white font-semibold text-sm">Ask about this Repo</h1>
          <p className="text-gray-500 text-xs">AI answers from your actual code — no hallucination</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="max-w-xl mx-auto mt-8">
            <div className="text-center mb-8">
              <div className="text-4xl mb-3">💬</div>
              <h2 className="text-white font-semibold mb-1">Ask anything about this codebase</h2>
              <p className="text-gray-400 text-sm">
                Questions are answered using code retrieved from the repo — the AI only sees relevant snippets.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-2">
              {SAMPLE_QUESTIONS.map(q => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-left card hover:border-gray-600 transition-colors text-sm text-gray-300 hover:text-white"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl ${msg.role === 'user' ? 'ml-12' : 'mr-12'}`}>
              {/* Bubble */}
              <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-brand-500 text-white rounded-tr-sm'
                  : 'bg-gray-800 text-gray-200 rounded-tl-sm'
              }`}>
                {msg.content}
              </div>

              {/* Meta (assistant only) */}
              {msg.meta && (
                <div className="mt-1.5 flex flex-wrap gap-2 text-xs text-gray-600 px-1">
                  <span>{PROVIDER_ICON[msg.meta.provider] ?? msg.meta.provider}</span>
                  <span className={CONFIDENCE_COLOR[msg.meta.confidence]}>
                    {msg.meta.confidence} confidence
                  </span>
                  <span>{msg.meta.chunks_used} chunk{msg.meta.chunks_used !== 1 ? 's' : ''} used</span>
                  {msg.meta.sources.length > 0 && (
                    <details className="cursor-pointer">
                      <summary className="hover:text-gray-400 list-none">
                        {msg.meta.sources.length} source{msg.meta.sources.length > 1 ? 's' : ''} ›
                      </summary>
                      <div className="mt-1 pl-2 space-y-0.5">
                        {msg.meta.sources.map((s, si) => (
                          <div key={si} className="text-gray-500 font-mono">{s}</div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-gray-800 bg-gray-950">
        <div className="flex gap-3 max-w-3xl mx-auto">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
            placeholder="Ask about the codebase… (Enter to send, Shift+Enter for newline)"
            rows={2}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 resize-none transition-colors"
          />
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            className="btn-primary px-5 self-end"
          >
            Send
          </button>
        </div>
        <p className="text-center text-xs text-gray-700 mt-2">
          Answers are grounded in your code. Sources always shown.
        </p>
      </div>
    </div>
  )
}
