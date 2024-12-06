import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir, copyFile, stat } from 'fs/promises'
import { join, basename } from 'path'
import { exec } from 'child_process'
import { promisify } from 'util'
import { existsSync } from 'fs'

const execAsync = promisify(exec)

async function ensureTestVideo() {
  const publicDir = join(process.cwd(), 'public')
  const tmpDir = join(process.cwd(), 'tmp')
  const testVideoPath = join(publicDir, 'test-video.mp4')
  
  await mkdir(publicDir, { recursive: true })
  await mkdir(tmpDir, { recursive: true })

  if (!existsSync(testVideoPath)) {
    try {
      await execAsync(
        'ffmpeg -f lavfi -i testsrc=duration=120:size=1280x720:rate=30 ' +
        '-vf "drawtext=text=\'Test Video\':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" ' +
        `-y "${testVideoPath}"`
      )
      console.log('Created test video successfully')
    } catch (error) {
      console.error('Failed to create test video:', error)
      throw new Error('Failed to create test video')
    }
  }

  return testVideoPath
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
    await mkdir(tmpDir, { recursive: true })

    let videoPath: string
    let originalFilename: string

    if (useTestVideo) {
      try {
        const testVideoPath = await ensureTestVideo()
        originalFilename = 'test-video.mp4'
        videoPath = join(tmpDir, originalFilename)
        await copyFile(testVideoPath, videoPath)
      } catch (error) {
        console.error('Failed to setup test video:', error)
        return NextResponse.json(
          { 
            success: false, 
            error: 'Failed to setup test video',
            details: error
          },
          { status: 500 }
        )
      }
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
      console.log(`Processing video: ${videoPath}`)
      const { stdout, stderr } = await execAsync(`python process_video_debug.py "${videoPath}"`)
      console.log('Processing output:', stdout)
      if (stderr) console.error('Processing errors:', stderr)
      
      const highlightsFilename = basename(videoPath, '.mp4') + '_highlights.mp4'
      const highlightsPath = join(tmpDir, highlightsFilename)
      
      if (existsSync(highlightsPath)) {
        const stats = await stat(highlightsPath)
        console.log(`Highlights file size: ${stats.size} bytes`)
        if (stats.size > 1000) {
          return NextResponse.json({ 
            success: true, 
            downloadUrl: `/api/download?file=${encodeURIComponent(highlightsFilename)}`,
            debug: {
              stdout,
              stderr
            }
          })
        } else {
          console.error('Generated file is too small:', stats.size, 'bytes')
        }
      } else {
        console.error('Highlights file not found:', highlightsPath)
      }
      
      // If we reach here, either the file doesn't exist or is too small
      // Return the original video instead
      console.log('Returning original video')
      return NextResponse.json({ 
        success: true, 
        noHighlights: true,
        message: "Failed to generate highlights. Original video returned.",
        downloadUrl: `/api/download?file=${encodeURIComponent(originalFilename)}`,
        debug: {
          stdout,
          stderr
        }
      })
    } catch (error) {
      console.error('Error processing video:', error)
      return NextResponse.json(
        { 
          success: false, 
          error: 'Failed to process video', 
          details: error,
          message: 'An error occurred during video processing. Please check the server logs for more information.'
        },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error('Error in process-video route:', error)
    return NextResponse.json({
      success: false,
      error: 'Internal server error',
      details: error,
      message: 'An unexpected error occurred. Please try again later or contact support.'
    }, { status: 500 })
  }
}

