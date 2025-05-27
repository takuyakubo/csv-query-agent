'use client'

import { useState, useCallback } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>
  isLoading?: boolean
}

export function FileUpload({ onUpload, isLoading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState<File | null>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type === 'text/csv' || droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile)
      }
    }
  }, [])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }, [])

  const handleUpload = async () => {
    if (file) {
      await onUpload(file)
    }
  }

  const handleRemove = () => {
    setFile(null)
  }

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 transition-colors ${
            dragActive ? 'border-primary bg-primary/5' : 'border-muted'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".csv"
            onChange={handleChange}
            disabled={isLoading}
          />
          
          {!file ? (
            <label
              htmlFor="file-upload"
              className="flex flex-col items-center justify-center cursor-pointer"
            >
              <Upload className="w-12 h-12 text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground mb-2">
                ドラッグ&ドロップまたはクリックしてCSVファイルをアップロード
              </p>
              <p className="text-xs text-muted-foreground">
                最大10MBまでのCSVファイルに対応
              </p>
            </label>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="w-8 h-8 text-primary" />
                <div>
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRemove}
                  disabled={isLoading}
                >
                  <X className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  onClick={handleUpload}
                  disabled={isLoading}
                >
                  {isLoading ? 'アップロード中...' : 'アップロード'}
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}