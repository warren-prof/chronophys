from cv2 import (
    VideoCapture,
    resize,
    CAP_PROP_FRAME_WIDTH,
    CAP_PROP_FRAME_HEIGHT,
    CAP_PROP_FRAME_COUNT,
    CAP_PROP_FPS,
    cvtColor,
    COLOR_BGR2RGB
)

def extract_images(video_file): 
    images = []
    settings = dict()
    error = False
    
    video_capture = VideoCapture(video_file)

    camera_Width  = int(video_capture.get(CAP_PROP_FRAME_WIDTH))
    camera_Height = int(video_capture.get(CAP_PROP_FRAME_HEIGHT))
    frameSize = (camera_Width, camera_Height)
    fps = video_capture.get(CAP_PROP_FPS) 
    frame_count = int(video_capture.get(CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps
    
    if int(video_capture.get(CAP_PROP_FRAME_COUNT)) < 150:
        i = 0
        while video_capture.isOpened():
            ret, frameOrig = video_capture.read()
            if ret == True:
                frame = cvtColor(resize(frameOrig, frameSize), COLOR_BGR2RGB)
                images.append(frame)

            else:
                break

        
        settings["nb_images"] = frame_count
        settings["fps"] = fps
        settings["duration"] = duration
        settings["width"] = camera_Width
        settings["height"] = camera_Height
        video_capture.release()
        return images, settings, error
    else:
        error = True
        settings["nb_images"] = frame_count
        settings["fps"] = fps
        settings["duration"] = duration
        settings["width"] = camera_Width
        settings["height"] = camera_Height
        return images, settings, error
