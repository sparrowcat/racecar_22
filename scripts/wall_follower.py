#!/usr/bin/env python

import rospy
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped
from std_msgs.msg import Bool
import time, collections


class pid_controller():
    def __init__(self):
        self.driving = AckermannDriveStamped()
        self.driving.header.stamp = rospy.Time.now()
        self.driving.drive.speed = 3
        self.ddes = 1 #1.0 #1.55
        self.prev_times = collections.deque([time.clock() for _ in range(10)])
        self.prev_errors = collections.deque([0 for _ in range(4)])
        self.kp = .6 #.75--right  #.5--OG
        self.ki = 0 #.1--right   # .05--OG
        self.kd = .02 #.05  # .025--right   #.1--OG
        self.mult =  1  # right
        self.start_ind = 80  # right
        self.end_ind = 280#500  # right
        #self.side_sub = rospy.Subscriber("/racecar/JoyLRSelec", Bool, self.side_callback)
        self.pid_pub = rospy.Publisher("vesc/ackermann_cmd_mux/input/navigation", AckermannDriveStamped, queue_size=1)
        self.scan_sub = rospy.Subscriber("scan", LaserScan, self.pid_callback)
	#rospy.Subscriber("blob_color", String, self.color_callback)
	rospy.Subscriber("/wall", Bool, self.side_callback) 

    def pid_callback(self, msg):
        side = msg.ranges[self.start_ind:self.end_ind]
        dist = sum(side) / len(side)
        error = self.ddes - dist
        if abs(error) < .03:
            self.driving.drive.steering_angle = 0
        else:
            self.driving.drive.steering_angle = self.mult * self.pid(self.kp, self.kd, self.ki, error)
        self.pid_pub.publish(self.driving)

    """def color_callback(self, msg):
	if msg.data == "g": #left wall
	    self.mult = -1
	    self.start_ind = 800#580
	    self.end_ind = 1000
	else: # right wall
	    self.mult = 1
	    self.start_ind = 80
	    self.end_ind = 280#500"""	

    def side_callback(self, msg):
        if msg.data:  # left wall
            self.mult = -1
            self.start_ind = 800#580
            self.end_ind = 1000
        else:  # right wall
            self.mult = 1
            self.start_ind = 80
            self.end_ind = 280#500

    def pid(self, kp, kd, ki, error):
        prev_error = self.prev_errors.popleft()
        prev_time = self.prev_times.popleft()
        e_deriv = (error - prev_error) / (time.clock() - prev_time)
        e_int = (error + prev_error) / 2 * (time.clock() - prev_time)
        self.prev_times.append(time.clock())
        self.prev_errors.append(error)
        return kp * error + kd * e_deriv + ki * e_int


rospy.init_node("pid")
controller = pid_controller()

rospy.spin()
