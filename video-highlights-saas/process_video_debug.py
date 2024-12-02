import cv2
import numpy as np
import sys
import os
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips

def process_video(input_path, debug=True):
    video = cv2.VideoCapture(input_path)
    
    if not video.isOpened():
        print("Error: Could not open video file")
        return None
    
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if debug:
        print(f"Video Properties:")
        print(f"FPS: {fps}")
        print(f"Total Frames: {total_frames}")
        print(f"Resolution: {width}x{height}")
        print(f"Duration: {total_frames/fps:.2f} seconds")
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(os.path.dirname(input_path), f"{base_name}_highlights.mp4")
    
    selected_frames = []
    frame_count = 0
    faces_detected = 0
    start_time = time.time()
    
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        if frame_count % 30 == 0:  # Process every 30th frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) > 0:
                faces_detected += 1
                selected_frames.append(frame_count)
                if debug:
                    print(f"Frame {frame_count}: Found {len(faces)} faces")
        
        frame_count += 1
        
        if debug and frame_count % 300 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"Progress: {progress:.1f}%")
    
    video.release()
    
    processing_time = time.time() - start_time
    
    if debug:
        print(f"\nProcessing Complete:")
        print(f"Total frames processed: {frame_count}")
        print(f"Frames with faces: {faces_detected}")
        print(f"Frames selected for highlight: {len(selected_frames)}")
        print(f"Processing time: {processing_time:.2f} seconds")
    
    # If less than 1% of frames were selected, return None to indicate no significant highlights
    if len(selected_frames) < (total_frames * 0.01):
        print("Not enough highlights found. Returning original video.")
        return None
    
    # Use moviepy to extract clips and preserve audio
    video = VideoFileClip(input_path)
    clips = [video.subclip(t/fps, t/fps + 1) for t in selected_frames]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    
    print(f"Highlights saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_video_debug.py <input_video_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = process_video(input_path, debug=True)
    
    if output_path:
        print(f"Highlights saved to: {output_path}")
    else:
        print("No significant highlights found. Original video returned.")

