from vpython import canvas, sphere, vector, cylinder, arrow, label, box
from vpython import color as color
from math import sin, cos
from glob import glob
import numpy as np
import serial
import time
import os


class MotionTrackerVisuals:
    
    # Canvases that hold the two scenes
    imu_canvas   = None
    rpy_canvas   = None

    # Collection of vpython objects
    imu = {}
    rpy_indicators = {}
    lbl_rpy_values = []
    column_centres = [
        vector(-0.30, -0.1, 0.0),
        vector(+0.00, -0.1, 0.0),
        vector(+0.30, -0.1, 0.0)
    ]
    indicator_radius = 0.1

    def __init__(self):
        # Main scene (3D pose)
        self.imu_canvas = canvas(title="IMU 3D Orientation", width=600, height=400, background=color.black)
        self.add_reference_axis()
        self.add_imu()

        # Second scene (roll, pitch, yaw)
        self.rpy_canvas  = canvas(title='Roll-Pitch-Yaw', width=600, height=400, background=color.black)
        self.label_rpy()
        self.add_rpy_indicators()
        self.add_compass()

    def add_imu(self):

        self.imu = {
            "platform": box(length=1, height=0.05, width=0.65, color=color.green),
            "line": box(length=1, height=0.08, width=0.1, color=color.white),
            "arrow": arrow(length=0.8, color=color.green, axis=vector(1, 0, 0), shaftwidth=0.06, fixedwidth=1),
            "com": sphere(pos=vector(0, 0, 0), radius=0.05, color=color.red)
        }

    def add_reference_axis(self):
        self.imu_canvas.select()

        xref = vector(+ 1, + 0, + 0)
        yref = vector(+ 0, - 1, + 0)
        zref = vector(+ 0, + 0, - 1)
        arrow_fmt = {"shaftwidth": 0.02, "fixedwidth": 1, "color": color.red}
        label_fmt = {"box": 0, "opacity": 0}

        arrow(axis=xref, **arrow_fmt)
        label(pos=xref, text="Xref", **label_fmt)
        arrow(axis=yref, **arrow_fmt)
        label(pos=yref, text="Yref", **label_fmt)
        arrow(axis=zref, **arrow_fmt)
        label(pos=zref, text="Zref", **label_fmt)

    def label_rpy(self):
        self.rpy_canvas.select()

        value_offset = vector(0.0, 0.25, 0.0)
        self.lbl_rpy_values = [label(pos=(c + value_offset), text="-", box=0, opacity=0) for c in self.column_centres]

        # Label the column headings
        heading_offset = vector(0.0, 0.30, 0.0)
        for i, lbl in enumerate(["Roll", "Pitch", "Yaw"]):
            label(pos=self.column_centres[i] + heading_offset, text=lbl, box=0, opacity=0, color=color.white)

    def add_compass(self):
        self.rpy_canvas.select()

        center = self.column_centres[2]
        
        compass_r = self.indicator_radius
        cardinal = {"box": 0, "opacity": 0, "color": color.white}
        intercardinal = {"box": 0, "height": 7, "color": color.white}

        # Cardinal directions
        label(pos=center + compass_r * vector(0, + 1, 0), text="N", **cardinal)
        label(pos=center + compass_r * vector(0, - 1, 0), text="S", **cardinal)
        label(pos=center + compass_r * vector(- 1, 0, 0), text="W", **cardinal)
        label(pos=center + compass_r * vector(+ 1, 0, 0), text="E", **cardinal)

        # Intercardinal directions
        label(pos=center + compass_r * vector(cos(1 * np.pi / 4), sin(1 * np.pi / 4), 0), text="NE", **intercardinal)
        label(pos=center + compass_r * vector(cos(3 * np.pi / 4), sin(3 * np.pi / 4), 0), text="NW", **intercardinal)
        label(pos=center + compass_r * vector(cos(5 * np.pi / 4), sin(5 * np.pi / 4), 0), text="SW", **intercardinal)
        label(pos=center + compass_r * vector(cos(7 * np.pi / 4), sin(7 * np.pi / 4), 0), text="SE", **intercardinal)

    def add_rpy_indicators(self):

        r = self.indicator_radius

        self.rpy_indicators = {
            "roll": cylinder(pos=self.column_centres[0], axis=vector(r, 0, 0), radius=0.01, color=color.red),
            "roll2": cylinder(pos=self.column_centres[0], axis=vector(- r, 0, 0), radius=0.01, color=color.red),
            "pitch": cylinder(pos=self.column_centres[1], axis=vector(r, 0, 0), radius=0.01, color=color.green),
            "pitch2": cylinder(pos=self.column_centres[1], axis=vector(- r, 0, 0), radius=0.01, color=color.green),
            "course": arrow(pos=self.column_centres[2], axis=vector(- r, 0, 0), shaftwidth=0.02, fixedwidth=1,
                            color=color.cyan)
        }

    def update_imu(self, rpy):

        axis, up = self.get_axis_up(rpy)

        ptfm = self.imu["platform"]
        arrw = self.imu["arrow"]
        line = self.imu["line"]

        ptfm.axis = axis
        ptfm.up = up
        arrw.axis = axis
        arrw.up = up
        line.axis = axis
        line.up = up

    def update_rpy_indicators(self, rpy):

        roll, pitch, yaw = rpy

        r = self.indicator_radius
        self.rpy_indicators["roll"].axis = vector(r * cos(roll), r * sin(roll), 0)
        self.rpy_indicators["roll2"].axis = vector(- r * cos(roll), - r * sin(roll), 0)
        self.rpy_indicators["pitch"].axis = vector(r * cos(pitch), r * sin(pitch), 0)
        self.rpy_indicators["pitch2"].axis = vector(- r * cos(pitch), - r * sin(pitch), 0)
        self.rpy_indicators["course"].axis = vector(r * sin(yaw), r * cos(yaw), 0)

        for i, val in enumerate(rpy):
            self.lbl_rpy_values[i].text = "{:.4e}".format(val)

    @staticmethod
    def get_axis_up(rpy):

        roll, pitch, yaw = rpy

        axis = vector(cos(pitch) * cos(yaw),
                      - cos(pitch) * sin(yaw),
                      sin(pitch))
        up = vector(sin(roll) * sin(yaw) + cos(roll) * sin(pitch) * cos(yaw),
                    sin(roll) * cos(yaw) - cos(roll) * sin(pitch) * sin(yaw),
                    - cos(roll) * cos(pitch))

        return axis, up

    def update(self, rpy):
        self.update_imu(rpy)
        self.update_rpy_indicators(rpy)


class MotionTracker:

    filename    = None
    serial      = None
    port        = None
    rpy         = [0.0, 0.0, 0.0]
    visuals     = None

    def __init__(self, port, baudrate=115_200, timeout=1.0):

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.visuals = MotionTrackerVisuals()

    @classmethod
    def from_file(cls, filename, baudrate=None, timeout=0.1):
        cls.filename = os.path.abspath(filename)
        return cls(None, baudrate=baudrate, timeout=timeout)

    def process_line(self, line):
        if line != "\n":
            try:
                self.rpy = [np.radians(float(x)) for x in line.split(",")]
            except ValueError:
                print(f"Invalid line: {line}")

            self.visuals.update(self.rpy)
        time.sleep(self.timeout)

    def run(self):
        if self.port is None:
            with open(self.filename, 'r') as f:
                for line in f:
                    self.process_line(line)
        else:
            with serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout) as ser:
                line = ser.readline()
                self.process_line(line)


def main():
    files = [file for file in sorted(glob("./data/Serial*.txt"))]

    # Run the motion tracker on an old run
    mt = MotionTracker.from_file(files[0])
    mt.run()


if __name__ == "__main__":
    main()
