import React, { useEffect, useRef, useState } from 'react'

type Message = {
  id: number
  sender: 'user' | 'bot'
  text: string
}

const API_BASE_URL = 'http://localhost:8000'

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [applicationId, setApplicationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const sendMessage = async () => {
    const trimmed = input.trim()
    if (!trimmed || loading || applicationId) return

    const userMessage: Message = {
      id: Date.now(),
      sender: 'user',
      text: trimmed,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: trimmed }),
      })

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`)
      }

      const data: {
        response: string
        form_complete: boolean
        application_id: string | null
      } = await res.json()

      const botMessage: Message = {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.response,
      }

      setMessages(prev => [...prev, botMessage])

      if (data.form_complete && data.application_id) {
        setApplicationId(data.application_id)
      }
    } catch (err) {
      const botMessage: Message = {
        id: Date.now() + 2,
        sender: 'bot',
        text:
          'Sorry, something went wrong while contacting the server. Please try again in a moment.',
      }
      setMessages(prev => [...prev, botMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleReset = async () => {
    setLoading(true)
    try {
      await fetch(`${API_BASE_URL}/reset`, {
        method: 'POST',
      })
      setMessages([])
      setApplicationId(null)
      setInput('')
    } catch {
      // even if reset fails, let user continue; optionally show error
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-root">
      <div className="chat-container">
        <header className="chat-header">
          <div>
            <h1>PM Mudra Loan Assistant</h1>
            <p>Fill your Mudra loan application through a simple chat.</p>
          </div>
          <button
            className="reset-button"
            onClick={handleReset}
            disabled={loading && !applicationId}
          >
            Reset
          </button>
        </header>

        <div className="chat-window">
          <div className="messages">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`message-row ${
                  msg.sender === 'user' ? 'message-row-user' : 'message-row-bot'
                }`}
              >
                <div
                  className={`message-bubble ${
                    msg.sender === 'user'
                      ? 'message-bubble-user'
                      : 'message-bubble-bot'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {applicationId && (
          <div className="success-banner">
            <div className="success-icon">✅</div>
            <div>
              <h2>Application Submitted Successfully!</h2>
              <p>Your Application ID is: {applicationId}</p>
              <p>Please save this ID for status tracking.</p>
            </div>
          </div>
        )}

        <div className="input-row">
          <input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || !!applicationId}
          />
          <button
            className="send-button"
            onClick={sendMessage}
            disabled={loading || !input.trim() || !!applicationId}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}

