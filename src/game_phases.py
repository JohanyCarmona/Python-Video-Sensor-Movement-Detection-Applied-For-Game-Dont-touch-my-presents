# importing OpenCV, time and Pandas library
import cv2, time, pandas
# importing datetime class from datetime library
from datetime import datetime

import sys
import time
import pygame

from src.components.game_status import GameStatus
from src.components.hand import Hand
from src.components.hand_side import HandSide
from src.components.player import Player
from src.components.scoreboard import Scoreboard
from src.global_state import GlobalState
from src.services.music_service import MusicService
from src.services.visualization_service import VisualizationService
from src.utils.tools import update_background_using_scroll, update_press_key, is_close_app_event

GlobalState.load_main_screen()
VisualizationService.load_main_game_displays()
scoreboard = Scoreboard()

# Sprite Setup
P1 = Player()
H1 = Hand(HandSide.RIGHT)
H2 = Hand(HandSide.LEFT)

# Sprite Groups
hands = pygame.sprite.Group()
hands.add(H1)
hands.add(H2)
all_sprites = pygame.sprite.Group()
all_sprites.add(P1)
all_sprites.add(H1)
all_sprites.add(H2)

def main_menu_phase():
    
    scoreboard.reset_current_score()
    events = pygame.event.get()

    for event in events:
        if is_close_app_event(event):
            GlobalState.GAME_STATE = GameStatus.GAME_END
            return

        if event.type == pygame.KEYDOWN:
            GlobalState.GAME_STATE = GameStatus.GAMEPLAY

    GlobalState.SCROLL = update_background_using_scroll(GlobalState.SCROLL)
    VisualizationService.draw_background_with_scroll(GlobalState.SCREEN, GlobalState.SCROLL)
    GlobalState.PRESS_Y = update_press_key(GlobalState.PRESS_Y)
    VisualizationService.draw_main_menu(GlobalState.SCREEN, scoreboard.get_max_score(), GlobalState.PRESS_Y)


def gameplay_phase(video, static_back, static_datetime, static_small_centroid, DELAY, CONTOUR_RECTANGLE, MINIMUM_CONTOUR_TYPE):
    events = pygame.event.get()

    for event in events:
        if is_close_app_event(event):
            game_over()
            return
    
    # Infinite while loop to treat stack of image as video
    deadline = time.time()
    movement_direction = None
    position_vector = None
    image_size = None
    normalized_position = None

    while time.time() - deadline < DELAY and  movement_direction == None and position_vector == None:
        # Reading frame(image) from video
        check, frame = video.read()
        
        # Converting color image to gray_scale image
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Converting gray scale image to GaussianBlur 
        # so that change can be find easily
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # In first iteration we assign the value 
        # of static_back to our first frame
        if static_back is None:
            static_back = gray
            image_size = [len(static_back),len(static_back[0])]
            static_datetime =time.time()
            continue

        # Difference between static background 
        # and current frame(which is GaussianBlur)
        diff_frame = cv2.absdiff(static_back, gray)


        # If change in between static background and
        # current frame is greater than 30 it will show white color(255)
        thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations = 2)

        # Finding contour of moving object
        cnts,_ = cv2.findContours(thresh_frame.copy(), 
                           cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        centroid = []
        area = []
        for contour in cnts:
            if cv2.contourArea(contour) < CONTOUR_RECTANGLE:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            
            # making green rectangle around the moving object
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            #Getting the centroid & area of each contour
            centroid.append([x+w/2, y+h/2])
            area.append(w*h)
            
        #Getting index of contour with less area
        if len(area) > 0:
            if MINIMUM_CONTOUR_TYPE:
                index = area.index(min(area))
            else:
                index = area.index(max(area))
            del area
            small_centroid = centroid[index]
            del centroid

            # In first iteration we assign the value 
            # of static_small_centroid to our first frame
            if static_small_centroid is None:
                static_small_centroid = small_centroid
                static_datetime =time.time()
                image_size = [len(static_back),len(static_back[0])]
                normalized_position = [small_centroid[0]/image_size[0],small_centroid[1]/image_size[1]]
                continue
            else:
                #Checking direction after delay
                if time.time() - static_datetime > DELAY:
                    horizontal_right = small_centroid[0] - static_small_centroid[0] < 0
                    vertical_up = small_centroid[1] - static_small_centroid[1] < 0
                    movement_direction = [horizontal_right, vertical_up]
                    static_small_centroid = small_centroid
                    static_datetime =time.time()
                    static_back = gray
                    image_size = [len(static_back),len(static_back[0])]
                    normalized_position = [small_centroid[0]/image_size[0],small_centroid[1]/image_size[1]]

        # Displaying image in gray_scale
        cv2.imshow("Gray Frame", gray)

        # Displaying the difference in currentframe to
        # the staticframe(very first_frame)
        cv2.imshow("Difference Frame", diff_frame)

        # Displaying the black and white image in which if
        # intensity difference greater than 30 it will appear white
        cv2.imshow("Threshold Frame", thresh_frame)

        # Displaying color frame with contour of motion of object
        cv2.imshow("Color Frame", frame)

        key = cv2.waitKey(1)
        # if q entered whole process will stop
        if key == ord('q'):
            break
        
    P1.update(movement_direction, normalized_position)
    H1.move(scoreboard, P1.player_position)
    H2.move(scoreboard, P1.player_position)

    GlobalState.SCROLL = update_background_using_scroll(GlobalState.SCROLL)
    VisualizationService.draw_background_with_scroll(GlobalState.SCREEN, GlobalState.SCROLL)

    P1.draw(GlobalState.SCREEN)
    H1.draw(GlobalState.SCREEN)
    H2.draw(GlobalState.SCREEN)
    scoreboard.draw(GlobalState.SCREEN)

    if pygame.sprite.spritecollide(P1, hands, False, pygame.sprite.collide_mask):
        scoreboard.update_max_score()
        MusicService.play_slap_sound()
        time.sleep(0.5)
        game_over()
    return static_back, static_datetime, static_small_centroid

def exit_game_phase():
    video.release()
    # Destroying all the windows
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()

def game_over():
    P1.reset()
    H1.reset()
    H2.reset()
    GlobalState.GAME_STATE = GameStatus.MAIN_MENU
    time.sleep(0.5)
