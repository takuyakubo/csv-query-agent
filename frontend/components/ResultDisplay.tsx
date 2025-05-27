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
                    <div className="text-sm text-muted-foreground mb-2">
                      画像データ長: {result.visualization.length}文字
                    </div>
                    <div className="text-xs text-muted-foreground mb-2 break-all">
                      開始: {result.visualization.substring(0, 100)}...
                    </div>
                    {result.visualization.startsWith('data:image/png;base64,') ? (
                      <img
                        src={result.visualization}
                        alt="Visualization"
                        className="max-w-full h-auto rounded-lg shadow-md"
                        onError={(e) => {
                          console.error('Image load error:', e)
                          console.log('Full image src length:', result.visualization?.length)
                          console.log('Image src start:', result.visualization?.substring(0, 200))
                        }}
                        onLoad={() => console.log('Image loaded successfully')}
                      />
                    ) : (
                      <div className="bg-yellow-100 p-4 rounded-lg">
                        <p className="text-sm">画像データの形式が正しくありません</p>
                        <p className="text-xs break-all">{result.visualization}</p>
                      </div>
                    )}
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