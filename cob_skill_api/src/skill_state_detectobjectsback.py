#!/usr/bin/env python

#################################################################
##\file
#
# \note
# Copyright (c) 2012 \n
# Fraunhofer Institute for Manufacturing Engineering
# and Automation (IPA) \n\n
#
#################################################################
#
# \note
# Project name: Care-O-bot Research
# \note
# ROS package name: cob_skill_api
#
# \author
# Author: Thiago de Freitas Oliveira Araujo, 
# email:thiago.de.freitas.oliveira.araujo@ipa.fhg.de
# \author
# Supervised by: Florian Weisshardt, email:florian.weisshardt@ipa.fhg.de
#
# \date Date of creation: September 2012
#
# \brief
# Skill state detect objects re-implementation using the skills API
# Detect Objects at the Back Side of the Robot
#
#################################################################
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer. \n
# - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution. \n
# - Neither the name of the Fraunhofer Institute for Manufacturing
# Engineering and Automation (IPA) nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission. \n
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License LGPL as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License LGPL for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License LGPL along with this program.
# If not, see < http://www.gnu.org/licenses/>.
#
#################################################################

import roslib
roslib.load_manifest("cob_skill_api")

import rospy
import smach
import smach_ros

from math import *
import copy

from simple_script_server import *
sss = simple_script_server()

from cob_object_detection_msgs.msg import *
from cob_object_detection_msgs.srv import *

from abc_state_skill import SkillsState

class skill_state_detectobjectsback(SkillsState):

    def __init__(self, object_names = [], namespace="", detector_srv = "/object_detection/detect_object", mode = "all"):
        smach.State.__init__(
                self,
                outcomes = ["detected", "not_detected", "failed"],
                input_keys=["object_names"],
                output_keys=["objects"])

        if mode not in ["all", "one"]:
            rospy.logwarn("Invalid mode: must be 'all', or 'one', selecting the default value = 'all'")
            self.mode = "all"
        else:
            self.mode = mode

        self.object_detector = ObjectDetector(object_names, namespace, detector_srv, self.mode)

    def execute(self, userdata):

        rospy.loginfo("Started Executing the Detect Objects State")
        sss.set_light("blue")

        handle_torso = sss.move("torso", "shake", False)
        sss.set_light("yellow")
        handle_arm = sss.move("arm", "folded-to-look_at_table", False)
        handle_head = sss.move("head", "back", False)
        handle_arm.wait()
        handle_torso.wait()
        handle_head.wait()

        sss.set_light("blue")

        result, userdata.objects = self.object_detector.execute(userdata)

        #cleanup robot components
        if result != "detected":
            sss.set_light("yellow")
            sss.move("torso", "front")
            handle_arm = sss.move("arm", "look_at_table-to-folded")

        sss.move("torso", "home")

        if result == "failed":
            sss.set_light("red")
        else:
            sss.set_light("green")

        return result
