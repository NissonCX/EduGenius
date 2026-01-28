/**
 * Chat Type Definitions
 */
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatResponse {
  content: string
  done?: boolean
}
