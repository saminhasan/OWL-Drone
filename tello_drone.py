from djitellopy import Tello

class Drone(Tello):
    def __init__(self):
        super().__init__()
        self.run()

    def run(self):
        # return super().get_battery()
        #print(self.get_battery())
        super().connect()
        #super().set_video_bitrate(Tello.BITRATE_1MBPS)
        super().streamoff()
        super().streamon()
        self.image = self.get_frame_read()

if __name__ == "__main__":
    d = Drone()
    print(d.get_battery())
    d.end()