import cv2
import pygame
from src.components.game_status import GameStatus
from src.config import Config
from src.game_phases import main_menu_phase, gameplay_phase, exit_game_phase
from src.global_state import GlobalState
from src.services.music_service import MusicService

pygame.init()
FramePerSec = pygame.time.Clock()

DELAY = 0.021 #0.034 #0.100
CONTOUR_RECTANGLE = 3400 #5000 #10000
MINIMUM_CONTOUR_TYPE = False


def update_game_display():
    pygame.display.update()
    FramePerSec.tick(Config.FPS)

def main():

    # Capturing video
    video = cv2.VideoCapture(0)
    
    #Temporal static variables
    static_back = None
    static_datetime = None
    static_small_centroid = None
    
    while True:
        
        if GlobalState.GAME_STATE == GameStatus.MAIN_MENU:
            main_menu_phase()
            
        elif GlobalState.GAME_STATE == GameStatus.GAMEPLAY:
            static_back, static_datetime, static_small_centroid = gameplay_phase(video, 
                                                                                 static_back, 
                                                                                 static_datetime, 
                                                                                 static_small_centroid,
                                                                                 DELAY, 
                                                                                 CONTOUR_RECTANGLE, 
                                                                                 MINIMUM_CONTOUR_TYPE
                                                                                )
        elif GlobalState.GAME_STATE == GameStatus.GAME_END:
            exit_game_phase()

        MusicService.start_background_music()
        update_game_display()

if __name__ == "__main__":
    main()