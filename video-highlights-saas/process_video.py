import cv2
import sys
import os

def process_video(input_path):
    # Open the video
    video = cv2.VideoCapture(input_path)
    
    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Output video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_path = os.path.splitext(input_path)[0] + '_highlights.mp4'
    out = cv2.VideoWriter(output_path, fourcc, fps, (int(video.get(3)), int(video.get(4))))
    
    frame_count = 0
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        # Process every 30th frame (adjust as needed)
        if frame_count % 30 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # If faces are detected, write this frame to the output
            if len(faces) > 0:
                out.write(frame)
        
        frame_count += 1
    
    video.release()
    out.release()
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_video.py <input_video_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = process_video(input_path)
    print(f"Processed video saved to: {output_path}")