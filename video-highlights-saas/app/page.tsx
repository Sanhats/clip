'use client'

import { useState } from 'react'
import axios from 'axios'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string | null>(null)
  const [isDevelopment, setIsDevelopment] = useState(false)
  const [noHighlights, setNoHighlights] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setProcessing(true)
    setDebugInfo(null)
    setNoHighlights(false)
    
    const formData = new FormData()
    
    if (isDevelopment) {
      formData.append('useTestVideo', 'true')
    } else if (file) {
      formData.append('video', file)
    }

    try {
      const response = await axios.post('/api/process-video', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      setDownloadUrl(response.data.downloadUrl)
      setNoHighlights(response.data.noHighlights || false)
      if (response.data.debug) {
        setDebugInfo(response.data.debug.stdout)
      }
    } catch (error) {
      console.error('Error processing video:', error)
      setDebugInfo(error instanceof Error ? error.message : 'An error occurred')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">Video Highlights Generator</h1>
      
      <div className="mb-4 flex items-center gap-2">
        <input
          type="checkbox"
          id="devMode"
          checked={isDevelopment}
          onChange={(e) => setIsDevelopment(e.target.checked)}
          className="rounded border-gray-300"
        />
        <label htmlFor="devMode">Use test video (Development Mode)</label>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 w-full max-w-md">
        {!isDevelopment && (
          <input
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            className="block w-full text-sm text-slate-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-violet-50 file:text-violet-700
              hover:file:bg-violet-100
            "
          />
        )}
        <button
          type="submit"
          disabled={(!file && !isDevelopment) || processing}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {processing ? 'Processing...' : 'Generate Highlights'}
        </button>
      </form>

      {noHighlights && (
        <div className="mt-4 p-4 bg-yellow-100 text-yellow-800 rounded-lg w-full max-w-md">
          No significant highlights found. The original video is available for download.
        </div>
      )}

      {downloadUrl && (
        <a
          href={downloadUrl}
          download
          className="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Download Video
        </a>
      )}

      {debugInfo && (
        <div className="mt-4 p-4 bg-gray-100 rounded-lg w-full max-w-md">
          <h2 className="font-semibold mb-2">Debug Information:</h2>
          <pre className="whitespace-pre-wrap text-sm">{debugInfo}</pre>
        </div>
      )}
    </main>
  )
}

