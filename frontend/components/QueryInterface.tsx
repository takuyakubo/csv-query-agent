'use client'

import { useState, useCallback } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface QueryInterfaceProps {
  sessionId: string
  onQuery: (query: string) => Promise<void>
  isLoading?: boolean
}

export function QueryInterface({ sessionId, onQuery, isLoading }: QueryInterfaceProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isLoading) {
      await onQuery(query)
      setQuery('')
    }
  }, [query, onQuery, isLoading])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }, [handleSubmit])

  return (
    <Card>
      <CardHeader>
        <CardTitle>CSVに質問する</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="例: 売上の合計を教えて、月別の売上を棒グラフで表示して..."
            className="min-h-[100px]"
            disabled={isLoading}
          />
          <Button 
            type="submit" 
            disabled={!query.trim() || isLoading}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                処理中...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                送信
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}