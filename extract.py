from cv2 import (
    VideoCapture,
    VideoWriter,
    VideoWriter_fourcc,
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
    rotate,
    flip,
    CAP_PROP_EXPOSURE,
    CAP_PROP_AUTO_EXPOSURE,
    CAP_PROP_SETTINGS,
)

from datetime import datetime
import os, sys

from numpy import log as ln

def extract_infos(video_file):
    video_capture = VideoCapture(video_file)
    camera_Width  = int(video_capture.get(CAP_PROP_FRAME_WIDTH))  
    camera_Height = int(video_capture.get(CAP_PROP_FRAME_HEIGHT))

    frameSize = (camera_Width, camera_Height)

    fps = video_capture.get(CAP_PROP_FPS) 
    frame_count = int(video_capture.get(CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps

    video_capture.set(CAP_PROP_POS_FRAMES, 0) 
    ret, frameOrig = video_capture.read()
    if ret:
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

def webcam_init(camera_id, params=None):
    
    cap = VideoCapture(camera_id)
    ret_val , cap_for_exposure = cap.read()

    if params!=None:
        
        cap.set(CAP_PROP_FRAME_HEIGHT, params["res_height"])
        cap.set(CAP_PROP_FRAME_WIDTH,  params["res_width"])
        cap.set(CAP_PROP_FPS,  params["fps"])
        params["res_height"] = cap.get(CAP_PROP_FRAME_HEIGHT)
        params["res_width"] = cap.get(CAP_PROP_FRAME_WIDTH)
        params["fps"] = cap.get(CAP_PROP_FPS)

    else:   
        
        params = {}
        cap.set(CAP_PROP_AUTO_EXPOSURE, 3)
        fps = cap.get(CAP_PROP_FPS)
        res_height = cap.get(CAP_PROP_FRAME_HEIGHT)
        res_width = cap.get(CAP_PROP_FRAME_WIDTH)
        cap.set(CAP_PROP_AUTO_EXPOSURE, 3) # D'abord mode auto
        #exposition = cap.get(CAP_PROP_EXPOSURE)

        
        if sys.platform == "win32":
            exposition = -4
            exposition = 2**exposition*1000
        else :
            exposition = 60

        
        cap.set(CAP_PROP_EXPOSURE, exposition)

        luminosite = 100
        cap.set(10,luminosite)

        contraste = 30
        cap.set(11, contraste)

        saturation = 100
        cap.set(12,saturation)

        gamma = 0
        cap.set(22,gamma)

        nettete = 128
        cap.set(20,nettete)

        blanc = 5500
        cap.set(44,0) # Passage en mode manuel
        cap.set(45,blanc)

        teinte = 0
        cap.set(13, teinte)

        params["fps"],params["res_width"],params["res_height"],params["exposition"], params["luminosite"], params["contraste"], params["saturation"], params["gamma"], params["nettete"], params["blanc"], params["teinte"] = int(fps), int(res_width), int(res_height),int(exposition), int(luminosite), int(contraste), int(saturation), int(gamma), int(nettete), int(blanc), int(teinte)
        #print(params)
    
    return cap, params

def set_property(property, value, cap):
    if property == "luminosite":
        cap.set(10, value)
    elif property == "contraste":
        cap.set(11, value)
    elif property == "saturation":
        cap.set(12, value)
    elif property == "gamma":
        cap.set(22, value)
    elif property == "nettete":
        cap.set(20, value)
    elif property == "blanc":
        cap.set(45, value)
    elif property == "teinte":
        cap.set(13, value)
    
    # print("FPS", cap.get(5))
    # print("BRIGHTNESS", cap.get(10))
    # print("CONTRAST", cap.get(11))
    # print("SATURATION", cap.get(12))
    # print("EXPOSURE", cap.get(15))
    # print("GAMMA", cap.get(22))
    # print("GAIN", cap.get(14))
    # print("FOCUS", cap.get(28)) 

    return cap

def set_exposition(value, check, cap):
    if not check:
        cap.set(CAP_PROP_AUTO_EXPOSURE, 1) # mode manuel
        if sys.platform == "win32":
            cap.set(CAP_PROP_EXPOSURE, int(ln(value*0.001)/ln(2)))
        else:
            cap.set(CAP_PROP_EXPOSURE, value) 
    else:
        cap.set(CAP_PROP_AUTO_EXPOSURE, 3) # mode auto
    return cap

# def set_res(cap, width, height):

#     cap.set(CAP_PROP_FRAME_WIDTH, width)
#     cap.set(CAP_PROP_FRAME_WIDTH, height)
#     new_width = cap.get(CAP_PROP_FRAME_WIDTH)
#     new_height = cap.get(CAP_PROP_FRAME_HEIGHT)
#     return cap, new_width, new_height

def webcam_get_image(cap):
    ret, image = cap.read()
    if ret != False:
        image = flip(image, 1)
    return ret, image

def webcam_init_capture(fps, application_path, width, height):
    now = datetime.now()

    dt_string = now.strftime("%d%m%Y_%H_%M_%S")
    fourcc = VideoWriter_fourcc(*'MJPG')
    path = str(os.path.join(application_path,'videos','WebcamVid_'+dt_string+'.avi'))
    out1 = VideoWriter(path, apiPreference = 0, fourcc = fourcc, fps = fps, frameSize =(int(width),int(height)))
    return out1, path

def webcam_write_image(out1, image):
    out1.write(image)

def webcam_end_capture(out1):
    out1.release()

def release_cap(cap):
    if cap != None:
        cap.release()

def list_webcam_ports():

    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < 3:
        camera = VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            #print("Port %s is not working." %dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                #print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
                working_ports.append(dev_port)
            else:
                #print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
                available_ports.append(dev_port)
        dev_port +=1
    #print(working_ports)
    return working_ports
        
# def changeBrightness(value, cap):
#     brightness = 
#     brightness = (brightness - 0)/(255 - 0)
#     print(brightness)
#     cap.set(10,brightness)

# def changeContrast(x, cap):
#     contrast = 
#     contrast = (contrast - 0)/(255 - 0)
#     print(contrast)
#     cap.set(11,contrast)

