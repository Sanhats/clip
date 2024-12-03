'use client'

import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import axios from 'axios'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [error, setError] = useState<{
    message: string;
    instructions?: string[];
  } | null>(null)
  const [isDevelopment, setIsDevelopment] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setProcessing(true)
    setError(null)
    setDownloadUrl(null)
    
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
      
      if (response.data.downloadUrl) {
        setDownloadUrl(response.data.downloadUrl)
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        setError({
          message: error.response.data.error || 'An error occurred while processing the video',
          instructions: error.response.data.instructions
        })
      } else {
        setError({
          message: 'An unexpected error occurred'
        })
      }
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

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg w-full max-w-md">
          <div className="flex items-center gap-2 text-red-700 mb-2">
            <AlertCircle className="h-5 w-5" />
            <h3 className="font-semibold">Error</h3>
          </div>
          <p className="text-red-600 mb-2">{error.message}</p>
          {error.instructions && (
            <div className="text-sm text-red-600">
              <p className="font-semibold mb-1">To fix this:</p>
              <ul className="list-disc pl-5 space-y-1">
                {error.instructions.map((instruction, index) => (
                  <li key={index}>{instruction}</li>
                ))}
              </ul>
            </div>
          )}
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
    </main>
  )
}

