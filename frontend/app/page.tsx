'use client'

import { useState } from 'react'
import { FileUpload } from '@/components/FileUpload'
import { QueryInterface } from '@/components/QueryInterface'
import { ResultDisplay } from '@/components/ResultDisplay'
import { useApi } from '@/hooks/useApi'
import { FileText } from 'lucide-react'

interface SessionInfo {
  session_id: string
  filename: string
  columns: string[]
  rows: number
  columns_count: number
}

interface Result {
  success: boolean
  result?: string
  visualization?: string
  error?: string
  query: string
}

export default function Home() {
  const [session, setSession] = useState<SessionInfo | null>(null)
  const [results, setResults] = useState<Result[]>([])
  const { uploadCsv, queryCsv, isLoading, error } = useApi()

  const handleUpload = async (file: File) => {
    const response = await uploadCsv(file)
    if (response) {
      setSession(response)
      setResults([])
    }
  }

  const handleQuery = async (query: string) => {
    if (!session) return

    const response = await queryCsv(session.session_id, query)
    if (response) {
      setResults([response, ...results])
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-2">CSV Query Agent</h1>
            <p className="text-muted-foreground">
              CSVファイルをアップロードして、自然言語で質問してみましょう
            </p>
          </div>

          {!session ? (
            <FileUpload onUpload={handleUpload} isLoading={isLoading} />
          ) : (
            <>
              <div className="bg-muted/50 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileText className="w-6 h-6 text-primary" />
                  <div>
                    <p className="font-medium">{session.filename}</p>
                    <p className="text-sm text-muted-foreground">
                      {session.rows} 行 × {session.columns_count} 列
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setSession(null)
                    setResults([])
                  }}
                  className="text-sm text-muted-foreground hover:text-foreground"
                >
                  新しいファイルをアップロード
                </button>
              </div>

              <QueryInterface
                sessionId={session.session_id}
                onQuery={handleQuery}
                isLoading={isLoading}
              />

              <ResultDisplay results={results} />
            </>
          )}

          {error && (
            <div className="bg-destructive/10 text-destructive rounded-lg p-4">
              <p className="text-sm">{error}</p>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}