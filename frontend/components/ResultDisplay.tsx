'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'

interface Result {
  success: boolean
  result?: string
  visualization?: string
  error?: string
  query: string
}

interface ResultDisplayProps {
  results: Result[]
}

export function ResultDisplay({ results }: ResultDisplayProps) {
  if (results.length === 0) {
    return null
  }

  return (
    <div className="space-y-4">
      {results.map((result, index) => (
        <Card key={index}>
          <CardHeader>
            <CardTitle className="text-lg">
              質問: {result.query}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {result.success ? (
              <div className="space-y-4">
                {result.result && (
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap bg-muted p-4 rounded-lg overflow-x-auto">
                      {result.result}
                    </pre>
                  </div>
                )}
                {result.visualization && (
                  <div className="mt-4">
                    <img
                      src={result.visualization}
                      alt="Visualization"
                      className="max-w-full h-auto rounded-lg shadow-md"
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-start space-x-2 text-destructive">
                <AlertCircle className="w-5 h-5 mt-0.5" />
                <p className="text-sm">{result.error || 'エラーが発生しました'}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}