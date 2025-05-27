import { useState, useCallback } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UploadResponse {
  session_id: string
  filename: string
  columns: string[]
  rows: number
  columns_count: number
}

interface QueryResponse {
  success: boolean
  result?: string
  visualization?: string
  error?: string
  query: string
}

export function useApi() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const uploadCsv = useCallback(async (file: File): Promise<UploadResponse | null> => {
    setIsLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  const queryCsv = useCallback(async (sessionId: string, query: string): Promise<QueryResponse | null> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          query: query,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Query failed')
      }

      const data = await response.json()
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  return {
    uploadCsv,
    queryCsv,
    isLoading,
    error,
  }
}