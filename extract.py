from cv2 import (
    VideoCapture,
    resize,
    CAP_PROP_FRAME_WIDTH,
    CAP_PROP_FRAME_HEIGHT,
    CAP_PROP_FRAME_COUNT,
    CAP_PROP_FPS,
    cvtColor,
    COLOR_BGR2RGB,
    CAP_PROP_POS_MSEC,
    CAP_PROP_POS_FRAMES,
    INTER_AREA,
    ROTATE_90_COUNTERCLOCKWISE,
    ROTATE_90_CLOCKWISE,
    ROTATE_180,
    rotate
)
def extract_infos(video_file):
    video_capture = VideoCapture(video_file)
    camera_Width  = int(video_capture.get(CAP_PROP_FRAME_WIDTH))  
    camera_Height = int(video_capture.get(CAP_PROP_FRAME_HEIGHT))

    frameSize = (camera_Width, camera_Height)

    fps = video_capture.get(CAP_PROP_FPS) 
    print(fps)
    frame_count = int(video_capture.get(CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps

    video_capture.set(CAP_PROP_POS_FRAMES, 0) 
    ret, frameOrig = video_capture.read()
    frame = cvtColor(frameOrig, COLOR_BGR2RGB)

    return frame,camera_Width,camera_Height ,fps,frame_count,duration

    
def extract_images(video_file,settings_perso): 
    images = []
    settings = dict()
    error = False

    
    video_capture = VideoCapture(video_file)

    camera_Width  = int(video_capture.get(CAP_PROP_FRAME_WIDTH)) 
    camera_Height = int(video_capture.get(CAP_PROP_FRAME_HEIGHT)) 

    frameSize = (camera_Width, camera_Height)
    frameRatio= camera_Width/camera_Height
    # On applique le choix de l'utilisateur...
    if settings_perso[0] != camera_Width or settings_perso[1] != camera_Height:
        frameSize = (settings_perso[0],settings_perso[1])
        frameRatio = settings_perso[0]/settings_perso[1]
    

    # ... mais on s'assure que l'image soit quand même pas trop grande (pour la fluidité...)

    if frameSize[0] > 1280 or frameSize[1] > 720:
        frameSize = (settings_perso[0]//2,settings_perso[1]//2)


    fps = video_capture.get(CAP_PROP_FPS) 
    frame_count = int(video_capture.get(CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps
    maxFrames = settings_perso[2]
    frameRate = 1/maxFrames*duration
    increment = round(1/(maxFrames/frame_count))

    mytime = []
    if maxFrames < 150:
        i = 0
        while video_capture.isOpened():
            video_capture.set(CAP_PROP_POS_FRAMES, i) 
            ret, frameOrig = video_capture.read()
            if ret == True:
                # print(i)
                mytime.append(video_capture.get(CAP_PROP_POS_MSEC))
                frame = cvtColor(resize(frameOrig, frameSize,fx=0,fy=0, interpolation = INTER_AREA), COLOR_BGR2RGB)
                if settings_perso[3] == 90:
                    frame = rotate(frame, ROTATE_90_CLOCKWISE)
                elif settings_perso[3] == -90:
                    frame = rotate(frame, ROTATE_90_COUNTERCLOCKWISE)
                elif settings_perso[3] == 180:
                    frame = rotate(frame, ROTATE_180)
                images.append(frame)
                i+=increment
            else:
                break

        
        settings["nb_images"] = len(images)
        settings["fps"] = 1/frameRate
        settings["duration"] = duration
        settings["width"] = frameSize[0]
        settings["height"] = frameSize[1]
        video_capture.release()
        return images, settings, error, mytime
    else:
        error = True
        settings["nb_images"] = frame_count
        settings["fps"] = 1/frameRate
        settings["duration"] = duration
        settings["width"] = frameSize[0]
        settings["height"] = frameSize[1]
        return images, settings, error, mytime
