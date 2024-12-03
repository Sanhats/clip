import sys
import os
import subprocess
import json
from pathlib import Path

def ensure_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("ffmpeg is available")
            return True
    except:
        print("ffmpeg is not available in PATH")
        return False

def process_video(input_path, debug=True):
    if not ensure_ffmpeg():
        print("Error: ffmpeg is required but not found")
        return None

    try:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}_highlights.mp4")
        temp_output = os.path.join(os.path.dirname(input_path), f"{base_name}_temp.mp4")

        # Step 1: Detect faces and output to JSON
        face_detection_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', "select='gt(scene,0.001)',select='eq(pict_type,I)',scale=640:360,fps=1,select='not(mod(n,3))',showinfo,select='isnan(prev_selected_t)+gte(t-prev_selected_t,0.5)+lte(t-prev_selected_t,3)',face=frequency=10:search_scale=5:minsize=32,metadata=print:file=-",
            '-f', 'null',
            '-'
        ]

        face_detection_result = subprocess.run(face_detection_cmd, capture_output=True, text=True)
        face_data = face_detection_result.stderr

        # Parse face detection data
        face_timestamps = []
        for line in face_data.split('\n'):
            if 'pts_time' in line and 'face detected' in line:
                timestamp = float(line.split('pts_time:')[1].split()[0])
                face_timestamps.append(timestamp)

        if not face_timestamps:
            print("No faces detected in the video.")
            return None

        # Step 2: Create highlight clips
        highlight_filter = '+'.join([f"between(t,{t},{t+1})" for t in face_timestamps])
        highlight_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f"select='{highlight_filter}',setpts=N/FRAME_RATE/TB",
            '-af', f"aselect='{highlight_filter}',asetpts=N/SR/TB",
            '-y',
            temp_output
        ]

        subprocess.run(highlight_cmd, check=True)

        # Step 3: Optimize for compatibility
        optimize_cmd = [
            'ffmpeg',
            '-i', temp_output,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]

        subprocess.run(optimize_cmd, check=True)

        # Clean up temporary file
        os.remove(temp_output)

        # Verify output file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"Highlights saved to: {output_path}")
            return output_path
        else:
            print("Error: Output file is invalid or too small")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Error during video processing: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during video processing: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_video_debug.py <input_video_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = process_video(input_path, debug=True)
    
    if output_path:
        print(f"Highlights saved to: {output_path}")
    else:
        print("No significant highlights found or error occurred. Original video returned.")

