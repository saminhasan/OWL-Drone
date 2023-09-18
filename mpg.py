import os
import cv2
import sys
import math
import time
import numpy as np
import pygame as pg 
import pygame.locals
from threading import Thread
from djitellopy import Tello
from tello_drone import Drone
from typing import Any, List, Dict


CONTROL_UPDATE_RATE = 120 # Hz

S = 60

class Game:
    def __init__(self, width : int = 1280, height : int = 720):



        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.wz = 0
        self.speed = 15

        self.send_rc_control = False
        self.in_air = False

        self.drone = Drone()
        self.frame = self.drone.image
        self.previous_image = None
        self.drone.set_speed(self.speed)
        # self.drone.set_video_resolution(Tello.RESOLUTION_480P)
        #  self.drone.set_video_bitrate(Tello.BITRATE_1MBPS)

        print(self.drone.get_battery())

        self.running : bool = True
        self.flag : bool = True
        self.fps : float = 240
        self.width : int = width
        self.height : int =  height

        self.last_time : float = time.perf_counter()

        pg.init()
        pg.font.init()
        self.font = pg.font.SysFont(None, 10)
        self.clock = pg.time.Clock()
        self.display = pg.display
        self.screen = self.display.set_mode((self.width, self.height),pg.NOFRAME)
        self.foreground = pygame.transform.scale(pg.image.load('cb_3.png').convert_alpha(),(self.width, self.height))
        self.cursor = pygame.transform.scale(pg.image.load('cc.png').convert_alpha(),(self.width , self.height))
        # self.foreground = pg.image.load('cb_3.png').convert_alpha()
        # self.cursor = pg.image.load('cc.png').convert_alpha()
        self.circle_radius = 180

        self.display.set_caption('_')
        self.dict_keys : List  = list(pg.locals.__dict__.keys())
        self.dict_values : List = list(pg.locals.__dict__.values())



        self.tick = pygame.event.Event(pygame.USEREVENT + 1, {'name' : 'ControlUpdate', 'frequency' : CONTROL_UPDATE_RATE})
        pg.time.set_timer(self.tick,  1000 // CONTROL_UPDATE_RATE)
        # pg.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
        self.mouse_pos = None




    def handle_events(self):
        events = pg.event.get()
        for event in events:
            event_name = pg.event.event_name(event.type)
            # print(f"{event_name} : {event.__dict__} | {event.type}")

            if event.type == pg.QUIT:
                self.quit()
                break
            elif 'UserEvent' in event_name:
                self.send_control()
            elif 'Key' in event_name:
                # print(f"{event_name} : {event.__dict__} | {event.type}")

                key_pr = self.dict_keys[self. dict_values.index(event.key)]
                if event_name == 'KeyDown':
                    if key_pr == 'K_ESCAPE':
                        self.quit()
                        break
                    self.handle_key_press(key_pr)
                    
                elif event_name == 'KeyUp':
                    self.handle_key_release(key_pr)
                    
                
            elif event_name == 'TextInput':
                #print(f"{event.text} Key Pressed")
                pass

            elif 'Mouse' in event_name:
                self.handle_mouse_motion(event, event_name)
                pass

            elif 'Window' in event_name:
                pass

            else:
                # print(f"Event Handler Not Implement : {event_name} : {event._dict_}")
                pass

    def update_fps(self):
        fps_text = f"{self.clock.get_fps():.2f}"
        # self.screen.blit(self.font.render(fps_text, True, pg.Color("cyan")), (self.width - self.font.size(fps_text)[0], 1))
        battery_percentage = self.drone.get_battery()
        #self.display.set_caption(f'FPS : {fps_text}')
        # battery_percentage = 89
        self.display.set_caption(f'Battery : {battery_percentage} %')
        # print(f"FPS : fps_text", end='\r')

    def update(self, dt):
        self.update_fps()
        self.screen.fill([0, 0, 0])

        if not self.frame.stopped:
            frame = self.frame.frame
            f = cv2.normalize(cv2.resize(self.frame.frame, (self.width, self.height)), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            surf = pg.image.frombuffer(f.tobytes(), (self.width, self.height), "RGB")
            self.screen.blit(surf, (0, 0))
        self.screen.blit(self.foreground, (0,0))

        if self.mouse_pos is not None:
            # print(self.mouse_pos)
            # rect = pg.draw.circle(self.screen, (255, 255, 255), self.mouse_pos, 2, width=0)
            # rect = pg.draw.circle(self.screen, (255, 255, 255), self.mouse_pos, 10, width=1)

            # Circular region parameters
            circle_center = (self.width // 2, self.height // 2)
            x, y = self.mouse_pos[0], self.mouse_pos[1]
            # Calculate the distance between the current position and the circle's center
            distance = math.hypot(x - circle_center[0], y - circle_center[1])

            # If the distance is greater than the circle's radius, constrain the position to the circle
            if distance > self.circle_radius:
                angle = math.atan2(y - circle_center[1], x - circle_center[0])
                x = circle_center[0] + self.circle_radius * math.cos(angle)
                y = circle_center[1] + self.circle_radius * math.sin(angle)

            self.screen.blit(self.cursor, (int(x) - self.width//2, int(y) - self.height//2 ))
            #self.screen.blit(self.cursor, (self.width//2, self.height//2 ))

        self.display.update()

    def run(self):
        while self.running:
                    dt = self.clock.tick(self.fps)  # seconds
                    self.update(dt)
                    self.handle_events()


    def quit(self):
        self.running = False
        self.display.quit()
        pg.quit()
        
        self.drone.end()

    def send_control(self):
        if self.in_air:
            print(f"Control : {self.vy, self.vx,self.vz, self.wz}")
            
            self.drone.send_rc_control(self.vy, self.vx,self.vz, self.wz)
            pass
    def handle_mouse_motion(self, event ,event_name):
        if 'MouseMotion' in event_name:
            self.mouse_pos = event.pos
            if self.mouse_pos:
                self.wz = self.mouse_pos[0] * S / self.width - S / 2 
                self.wz = int(self.wz) * 5
                # print(self.wz)


    def handle_key_press(self, key):
        # print(f"{key} Pressed")
        if key == 'K_w':
            self.vx = S
        elif key == 'K_s':
            self.vx = -S
        elif key == 'K_a':
            self.vy = -S
        elif key == 'K_d':
            self.vy = S   
        elif key == 'NOFRAME':
            self.vz = S
        elif key == 'K_LCTRL':
            self.vz = -S



    def handle_key_release(self, key):
        # print(f"{key} Relased")
        if key == 'K_w':
            self.vx = 0
        elif key == 'K_s':
            self.vx = 0
        elif key == 'K_a':
            self.vy = 0
        elif key == 'K_d':
            self.vy = 0   
        elif key == 'NOFRAME':
            self.vz = 0
        elif key == 'K_LCTRL':
            self.vz = 0
        elif key == 'K_c':
            if self.in_air:
                Thread(target=self.drone.land())
                self.in_air = not self.in_air
                print("Landing")
            else:
                Thread(target=self.drone.takeoff())
                self.in_air = not self.in_air
                print("Taking Off")
if __name__ == "__main__":
    game = Game()
    game.run()