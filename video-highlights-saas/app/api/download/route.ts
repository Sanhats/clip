import { NextRequest, NextResponse } from 'next/server'
import { createReadStream, existsSync, statSync } from 'fs'
import { join } from 'path'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const fileName = searchParams.get('file')

    if (!fileName) {
      return NextResponse.json(
        { error: 'No file specified' },
        { status: 400 }
      )
    }

    const filePath = join(process.cwd(), 'tmp', decodeURIComponent(fileName))

    if (!existsSync(filePath)) {
      console.error('File not found:', filePath)
      return NextResponse.json(
        { error: 'File not found' },
        { status: 404 }
      )
    }

    try {
      const stats = statSync(filePath)
      const stream = createReadStream(filePath)

      return new NextResponse(stream, {
        headers: {
          'Content-Type': 'video/mp4',
          'Content-Length': stats.size.toString(),
          'Content-Disposition': `attachment; filename="${encodeURIComponent(fileName)}"`,
          'Accept-Ranges': 'bytes',
        },
      })
    } catch (error) {
      console.error('Error reading file:', error)
      return NextResponse.json(
        { error: 'Error reading file' },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error('Error in download route:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

