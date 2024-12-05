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

        # Step 1: Detect scene changes
        scene_detection_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', "select='gt(scene,0.3)',showinfo",
            '-f', 'null',
            '-'
        ]

        print("Running scene detection command:")
        print(" ".join(scene_detection_cmd))
        scene_detection_result = subprocess.run(scene_detection_cmd, capture_output=True, text=True)
        scene_data = scene_detection_result.stderr

        # Parse scene detection data
        scene_timestamps = []
        for line in scene_data.split('\n'):
            if 'pts_time' in line:
                timestamp = float(line.split('pts_time:')[1].split()[0])
                scene_timestamps.append(timestamp)

        print(f"Detected {len(scene_timestamps)} scene changes at timestamps: {scene_timestamps}")

        if not scene_timestamps:
            print("No scene changes detected in the video.")
            print("Returning the original video.")
            subprocess.run(['ffmpeg', '-i', input_path, '-c', 'copy', output_path])
            return output_path

        # Step 2: Create highlight clips
        highlight_filter = '+'.join([f"between(t,{t},{t+3})" for t in scene_timestamps[:10]])  # Limit to 10 scenes
        highlight_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f"select='{highlight_filter}',setpts=N/FRAME_RATE/TB",
            '-af', f"aselect='{highlight_filter}',asetpts=N/SR/TB",
            '-y',
            temp_output
        ]

        print("Running highlight creation command:")
        print(" ".join(highlight_cmd))
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

        print("Running optimization command:")
        print(" ".join(optimize_cmd))
        subprocess.run(optimize_cmd, check=True)

        # Clean up temporary file
        if os.path.exists(temp_output):
            os.remove(temp_output)

        # Verify output file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"Highlights saved to: {output_path}")
            print(f"Output file size: {os.path.getsize(output_path)} bytes")
            return output_path
        else:
            print(f"Error: Output file is invalid or too small. Size: {os.path.getsize(output_path)} bytes")
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
        print(f"Video saved to: {output_path}")
    else:
        print("Error occurred during video processing.")

