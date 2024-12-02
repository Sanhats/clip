import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir, copyFile } from 'fs/promises'
import { join, basename } from 'path'
import { exec } from 'child_process'
import { promisify } from 'util'
import { existsSync } from 'fs'

const execAsync = promisify(exec)

async function ensureDir(dirPath: string) {
  if (!existsSync(dirPath)) {
    await mkdir(dirPath, { recursive: true })
  }
}

function sanitizeFilename(filename: string) {
  return filename
    .replace(/[^a-zA-Z0-9.-]/g, '_')
    .replace(/ /g, '_')
    .toLowerCase()
}

export async function POST(req: NextRequest) {
  try {
    const data = await req.formData()
    const useTestVideo = data.get('useTestVideo') === 'true'
    const file: File | null = useTestVideo ? null : (data.get('video') as unknown as File)

    const tmpDir = join(process.cwd(), 'tmp')
    await ensureDir(tmpDir)

    let videoPath: string
    let originalFilename: string

    if (useTestVideo) {
      const testVideoPath = join(process.cwd(), 'public', 'test-video.mp4')
      originalFilename = 'test-video.mp4'
      videoPath = join(tmpDir, originalFilename)
      
      if (!existsSync(testVideoPath)) {
        return NextResponse.json(
          { success: false, error: 'Test video not found' },
          { status: 404 }
        )
      }

      await copyFile(testVideoPath, videoPath)
    } else {
      if (!file) {
        return NextResponse.json(
          { success: false, error: 'No file provided' },
          { status: 400 }
        )
      }

      originalFilename = file.name
      const sanitizedFilename = sanitizeFilename(file.name)
      videoPath = join(tmpDir, sanitizedFilename)

      const bytes = await file.arrayBuffer()
      const buffer = Buffer.from(bytes)
      await writeFile(videoPath, buffer)
    }

    try {
      const { stdout, stderr } = await execAsync(`python process_video_debug.py "${videoPath}"`)
      console.log('Processing output:', stdout)
      if (stderr) console.error('Processing errors:', stderr)
      
      const highlightsFilename = basename(videoPath, '.mp4') + '_highlights.mp4'
      const highlightsPath = join(tmpDir, highlightsFilename)
      
      if (existsSync(highlightsPath)) {
        return NextResponse.json({ 
          success: true, 
          downloadUrl: `/api/download?file=${encodeURIComponent(highlightsFilename)}`,
          debug: {
            stdout,
            stderr
          }
        })
      } else {
        return NextResponse.json({ 
          success: true, 
          noHighlights: true,
          message: "No significant highlights found. Original video returned.",
          downloadUrl: `/api/download?file=${encodeURIComponent(originalFilename)}`,
          debug: {
            stdout,
            stderr
          }
        })
      }
    } catch (error) {
      console.error('Error processing video:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to process video', details: error },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error('Error handling upload:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error', details: error },
      { status: 500 }
    )
  }
}

