import sys
import os
import subprocess
import json
from pathlib import Path
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

def ensure_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("ffmpeg is available")
            return True
    except:
        print("ffmpeg is not available in PATH")
        return False

def get_video_info(input_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', input_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def detect_scene_changes(input_path, threshold=0.1):
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-filter_complex', f"select='gt(scene,{threshold})',metadata=print:file=-",
        '-f', 'null',
        '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    scene_changes = []
    for line in result.stderr.split('\n'):
        if 'pts_time' in line:
            timestamp = float(line.split('pts_time:')[1].split()[0])
            scene_changes.append(timestamp)
    print(f"Scene detection output: {result.stderr}")
    return scene_changes

def detect_audio_peaks(input_path, threshold=-20):
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-af', f"acompressor,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
        '-f', 'null',
        '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    audio_peaks = []
    for line in result.stderr.split('\n'):
        if 'lavfi.astats.Overall.RMS_level' in line:
            parts = line.split('=')
            if len(parts) == 3:
                timestamp, level = float(parts[1]), float(parts[2])
                if level > threshold:
                    audio_peaks.append(timestamp)
    print(f"Audio peak detection output: {result.stderr}")
    return audio_peaks

def process_video_segment(input_path, start_time, duration, output_path):
    cmd = [
        'ffmpeg',
        '-ss', str(start_time),
        '-i', input_path,
        '-t', str(duration),
        '-c', 'copy',
        '-y',
        output_path
    ]
    subprocess.run(cmd, check=True)

def process_video(input_path, debug=True):
    if not ensure_ffmpeg():
        print("Error: ffmpeg is required but not found")
        return None

    try:
        video_info = get_video_info(input_path)
        duration = float(video_info['format']['duration'])
        print(f"Video duration: {duration} seconds")

        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}_highlights.mp4")
        temp_dir = os.path.join(os.path.dirname(input_path), 'temp_segments')
        os.makedirs(temp_dir, exist_ok=True)

        scene_changes = detect_scene_changes(input_path)
        audio_peaks = detect_audio_peaks(input_path)

        print(f"Detected {len(scene_changes)} scene changes and {len(audio_peaks)} audio peaks")

        # Combine and sort all important timestamps
        all_timestamps = sorted(set(scene_changes + audio_peaks))

        # If no timestamps were detected, use evenly spaced timestamps
        if not all_timestamps:
            print("No scene changes or audio peaks detected. Using evenly spaced timestamps.")
            all_timestamps = np.linspace(0, duration, 20).tolist()

        # Calculate highlight duration (20% of original video or at least 30 seconds)
        highlight_duration = max(duration * 0.2, 30)
        num_segments = int(highlight_duration / 3)  # 3-second segments

        # Select evenly distributed segments
        if len(all_timestamps) > num_segments:
            indices = np.linspace(0, len(all_timestamps) - 1, num_segments, dtype=int)
            selected_timestamps = [all_timestamps[i] for i in indices]
        else:
            selected_timestamps = all_timestamps

        print(f"Selected {len(selected_timestamps)} segments for highlights")

        # Process segments in parallel
        segment_files = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for i, timestamp in enumerate(selected_timestamps):
                segment_output = os.path.join(temp_dir, f"segment_{i:04d}.mp4")
                futures.append(executor.submit(process_video_segment, input_path, timestamp, 3, segment_output))
                segment_files.append(segment_output)

            for future in as_completed(futures):
                future.result()  # This will raise an exception if the task failed

        # Concatenate segments
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, 'w') as f:
            for segment in segment_files:
                f.write(f"file '{segment.replace(os.sep, '/')}'\n")

        print(f"Concat file contents:\n{open(concat_file, 'r').read()}")

        concat_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y',
            output_path
        ]
        concat_result = subprocess.run(concat_cmd, capture_output=True, text=True)
        if concat_result.returncode != 0:
            print(f"Error in concat command. Output: {concat_result.stdout}\nError: {concat_result.stderr}")
            raise subprocess.CalledProcessError(concat_result.returncode, concat_cmd)

        # Clean up temporary files
        for file in segment_files + [concat_file]:
            os.remove(file)
        os.rmdir(temp_dir)

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

