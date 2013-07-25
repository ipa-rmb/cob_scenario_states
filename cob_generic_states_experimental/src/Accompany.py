#!/usr/bin/python
###
#Robot moves to position in room, rotates around the Z-axis and looks for people.
#It stops, when a specific person is found.
#
#Script needs in case of application in simulation:
#  - roscore
#  - kinect driver
#  - cob_people_detection
#  - cob_bringup_sim
#  - cob_navigation_global/2dnav_ros_dwa
#Set name to look for in SetName and Position in SetNavigationGoal.


import roslib
roslib.load_manifest('cob_generic_states_experimental')
import rospy
import math
import smach
import smach_ros
import random
from cob_people_detection_msgs.msg import *
from ApproachPose import *
import sys
from tf import TransformListener
from tf.transformations import euler_from_quaternion
import time



# predefined goals:
# list of goals that are predefined in the map
# current goal:
# coordinates of goal, that is currently being navigated to

class SetStartGoalName(smach.State):
  def __init__(self):
    smach.State.__init__(self,
      outcomes=['set','failed'],
      input_keys=['predefined_goals','current_goal','script_time'],
      output_keys=['predefined_goals','current_goal','script_time'])

  def execute(self, userdata):
      userdata.predefined_goals={
          "couch":  {"name":"couch","x":3,"y":-3,"theta":0.0},
        "kitchen": {"name":"kitchen","x":1,"y":-0.1,"theta":0.0},
        "middle":  {"name":"middle","x":1.5,"y":-1.5,"theta":0.0}
        }
      userdata.current_goal=userdata.predefined_goals["couch"]
      userdata.script_time=1
      return 'set'

class SetName(smach.State):
  def __init__(self):
    smach.State.__init__(self,
      outcomes=['set','failed'],
      input_keys=['id'],
      output_keys=['id'])

  def execute(self, userdata):
    userdata.id=str(PERSON)
    #userdata.id='Richard'
    sss.say(["I am looking for %s!"%str(userdata.id)])
    return 'set'



class SelectNavigationGoal(smach.State):
  def __init__(self):
    smach.State.__init__(self,
      outcomes=['selected','not_selected','failed'],
      input_keys=['current_goal'],
      output_keys=['base_pose'])

  def execute(self, userdata):
    if len(userdata.current_goal) >0:
      print "NAVIGATING TO %s."%userdata.current_goal["name"]
      pose = []
      pose.append(float(userdata.current_goal["x"])) # x
      pose.append(float(userdata.current_goal["y"])) # y
      pose.append(float(userdata.current_goal["theta"])) # theta
      userdata.base_pose=pose
      return 'selected'
    else:
      return 'failed'

class FakeState(smach.State):
  def __init__(self):
    smach.State.__init__(self,
        outcomes=['set','failed'],
        input_keys=['current_goal','position_last_seen','person_name'],
        output_keys=['current_goal','person_name','position_last_seen'])

  def execute(self,userdata):
    pos={"name":"fake","x":1.5,"y":-1.5,"theta":0.0}
    userdata.position_last_seen=pos
    userdata.person_name="Caro"
    userdata.current_goal=pos
    return 'set'

class Search(smach.State):
  def __init__(self):
    smach.State.__init__(self,
        outcomes=['found','not_found','new_search_goal','failed'],
        input_keys=['current_goal','position_last_seen','person_name'],
        output_keys=['current_goal','position_last_seen'])
    rospy.Subscriber("/cob_people_detection/detection_tracker/face_position_array",DetectionArray, self.callback)
    self.detections=list()

  def callback(self,msg):
    # go through list of detections and append them to detection list
    if len(msg.detections) >0:
      #clear detection list
      #del self.detections[:]
      for i in xrange( len(msg.detections)):
        self.detections.append(msg.detections[i])
        print "appending %s."%msg.detections[i].label
    return

  def check_detections(self,detections,name):

    if len(detections)==0:
      return False
    for det in detections:
      print "CHECKING DETECTIONS for %s"%name
      if name == det.label:
        print det.label
        print "NAME FOUND"
        return det
      else:
        print "NAME NOT FOUND"
        return False

  def update_goal(sel,old_pos,new_pos):
    threshold= 0.1  #[m]
    dist=math.sqrt((old_pos["x"]-new_pos["x"])*(old_pos["x"]-new_pos["x"])+(old_pos["y"]-new_pos["y"])*(old_pos["y"]-new_pos["y"]))

    if dist> threshold:
      return True
    else:
      return False

  def execute(self,userdata):
    print "TRYING TO REACH LAST SEEN POSITION"
		# try reaching pose
    del self.detections[:]
    pose=list()
    pose.append(float(userdata.current_goal["x"]))
    pose.append(float(userdata.current_goal["y"]))
    pose.append(float(userdata.current_goal["theta"]))
    handle_base = sss.move("base", pose,blocking=False)

  ## init variables
  #stopping_time = 0.0
  #announce_time = 0.0
  #freq = 2.0 # Hz
  #yellow = False


    # check for goal status
    target_person_detected=False
    while not rospy.is_shutdown() and target_person_detected==False :
      print "looping.."
      time.sleep(1)
      detection=self.check_detections(self.detections,userdata.person_name)
      if detection is not False:

        msg_pos=detection.pose.pose.position
        det_pos={"name":"det","x":msg_pos.x,"y":msg_pos.y,"theta":0.0}
        if self.update_goal(userdata.current_goal,det_pos):
          print "updating goual"
          userdata.current_goal=det_pos
          userdata.position_last_seen=det_pos
          target_person_detected=True

    print "stop base"
    sss.stop("base")
    # TODO
    #  check whether robot is already close enough
    #  need tf for that?
    if True:
      sss.say("There you are %s. I am coming for you"%userdata.person_name)
      return 'new_search_goal'

      # TODO
      # check for coordinate systems
      # use detection label as found label
      # replace last seen position when it differs from old one
      # replace current goal when not within radius
      # return 'new_search_goal'
    return 'failed'

  #	# finished with succeeded
  #	if (handle_base.get_state() == 3):
  #		sss.set_light('green')
  #		return 'reached'
  #	# finished with aborted
  #	elif (handle_base.get_state() == 4):
  #		sss.set_light('green')
  #		sss.stop("base")
  #		return 'not_reached'
  #	# finished with preempted or canceled
  #	elif (handle_base.get_state() == 2) or (handle_base.get_state() == 8):
  #		sss.set_light('green')
  #		sss.stop("base")
  #		return 'not_reached'
  #	# return with error
  #	elif (handle_base.get_error_code() > 0):
  #		print "error_code = " + str(handle_base.get_error_code())
  #		sss.set_light('red')
  #		return 'failed'

  #	# check if the base is moving
  #	loop_rate = rospy.Rate(freq) # hz
  #	if not self.is_moving: # robot stands still			
  #		# increase timers
  #		stopping_time += 1.0/freq
  #		announce_time += 1.0/freq

  #		# abort after timeout is reached
  #		if stopping_time >= self.timeout:
  #			sss.set_light('green')
  #			sss.stop("base")
  #			return 'not_reached'
  #		
  #		# announce warning after every 10 sec
  #		if announce_time >= 10.0:
  #			sss.say([self.warnings[random.randint(0,len(self.warnings)-1)]],False)
  #			announce_time = 0.0

  #		# set light to "thinking" after not moving for 2 sec
  #		if round(stopping_time) >= 2.0:
  #			sss.set_light("blue")
  #			yellow = False
  #	else:
  #		# robot is moving
  #		if not yellow:
  #			sss.set_light("yellow")
  #			yellow = True
    
    # sleep
    #loop_rate.sleep()






class Observe(smach.State):
  def __init__(self):
    smach.State.__init__(self,
      outcomes=['detected','not_yet_detected','search_now','failed'],
      input_keys=['predefined_goals','current_goal','position_last_seen','script_time'],
      output_keys=['person_name','predefined_goals','current_goal','position_last_seen','script_time'])
    rospy.Subscriber("/cob_people_detection/detection_tracker/face_position_array",DetectionArray, self.callback)
    self.detections=      list()
    self.false_detections=list()
    self.rep_ctr=0

  def callback(self,msg):
    # go through list of detections and append them to detection list
    if len(msg.detections) >0:
      #clear detection list
      del self.detections[:]
      for i in xrange( len(msg.detections)):
        self.detections.append(msg.detections[i].label)
    return

  def execute(self, userdata):
    if userdata.script_time==1:
      print self.rep_ctr
      # give person time to order and observe in the meantime
      time.sleep(5)

      # pick detection label which is majority in list
      #TODO pick first is temporary hack

      if len(self.detections)==0:
        # increment repetition counter
        self.rep_ctr+=1
        if self.rep_ctr>2:
          self.rep_ctr=0
          #TODO
          userdata.position_last_seen=userdata.predefined_goals["couch"]
          userdata.current_goal=userdata.predefined_goals["kitchen"]
          userdata.script_time+=1
          return 'detected'
          return 'failed'
        else:
          return 'not_yet_detected'
      else:
        userdata.person_name=self.detections[0]
        userdata.position_last_seen=userdata.predefined_goals["couch"]
        userdata.current_goal=userdata.predefined_goals["kitchen"]
        sss.say(['Thank you for your order, %s.'%str(self.detections[0])])
        userdata.script_time+=1
        return 'detected'
    elif userdata.script_time==2:
      userdata.script_time+=1
      time.sleep(5)
      userdata.current_goal=userdata.position_last_seen
      return 'search_now'


class MoveBaseTemp(smach.State):
    def __init__(self):
      smach.State.__init__(self,
        input_keys=['current_goal'],
        outcomes=['reached','failed'])

    def execute(self,userdata):
      target_pose=list()
      if userdata.current_goal['name'] is "kitchen":
        target_pose.append(0.1)
        target_pose.append(0)
        target_pose.append(0)
      elif userdata.current_goal['name'] is "couch":
        target_pose.append(-0.1)
        target_pose.append(0)
        target_pose.append(0)
      else:
        target_pose.append(-0.1)
        target_pose.append(-0.1)
        target_pose.append(0)


      for step in xrange(2):
        handle_base = sss.move_base_rel("base", target_pose)
      return 'reached'



class Rotate(smach.State):
  #class handles the rotation until program is stopped
  def __init__(self):
    self.tf = TransformListener()
    smach.State.__init__(self,
      outcomes=['finished','failed'],
      input_keys=['base_pose','stop_rotating','person_id'],
      output_keys=['detected'])
    rospy.Subscriber("/cob_people_detection/detection_tracker/face_position_array",DetectionArray, self.callback)
    self.stop_rotating=False
    self.detections=      list()
    self.false_detections=list()

  def callback(self,msg):
    # go through list of detections and append them to detection list
    if len(msg.detections) >0:
      #clear detection list
      del self.detections[:]
      for i in xrange( len(msg.detections)):
        self.detections.append(msg.detections[i].label)
    return

  def execute(self, userdata):
    print "ACCOMPANY-> ROTATE"
    sss.say(["I am going to take a look around now."])

    # get position from tf
    if self.tf.frameExists("/base_link") and self.tf.frameExists("/map"):
        t = self.tf.getLatestCommonTime("/base_link", "/map")
        position, quaternion = self.tf.lookupTransform("/base_link", "/map", t)
  # calculate angles from quaternion
	[r,p,y]=euler_from_quaternion(quaternion)
	#print r
	#print p
	#print y
  #print position
    else:
        print "No transform available"
        return "failed"

    time.sleep(1)
    self.stop_rotating=False
    # create relative pose - x,y,theta
    curr_pose=list()
    curr_pose.append(0)
    curr_pose.append(0)
    curr_pose.append(0.1)

    while not rospy.is_shutdown() and self.stop_rotating==False and curr_pose[2]< 3.14:
      handle_base = sss.move_base_rel("base", curr_pose)

      #check in detection and react appropriately
      for det in self.detections:
        # right person is detected
        if det == userdata.id:
          self.stop_rotating=True
          sss.say(['I have found you, %s! Nice to see you.'%str(det)])
        elif det in self.false_detections:
        # false person is detected
          print "Already in false detections"
       #  person detected is unknown - only react the first time
        elif det == "Unknown":
          print "Unknown face detected"
          sss.say(['Hi! Nice to meet you, but I am still searching for %s.'%str(userdata.id)])
          self.false_detections.append("Unknown")
      # wrong face is detected the first time
        else:
          self.false_detections.append(det)
          print "known - wrong face detected"
          sss.say(['Hello %s! Have you seen %s.'%(str(det),str(userdata.id))])
      #clear detection list, so it is not checked twice
      del self.detections[:]
      time.sleep(2)

    print "-->stop rotating"
    return 'finished'

class Talk(smach.State):
  def __init__(self):
    smach.State.__init__(self,
      outcomes=['found','not_found','failed'],
      input_keys=['id','detected']
      )

    self.phrases=[
        "I am looking for ",
        "Hello, nice to meet you! I don't know you yet!",
        ", nice to see you again",
        "No,you are not "
        ]

  def execute(self, userdata):
    name= str(userdata.id)
    print "wanted: %s"%name
    print "found:  %s"% userdata.detected
    if userdata.id != userdata.detected:
      #speech=self.phrases[3]+name+" !"
      sss.say(['No, I am sorry, but you are not %s.'%str(name)])
      return 'not_found'
    else:
      sss.say(['I have found you, %s! Nice to see you.'%str(name)])
      time.sleep(2)
      return 'found'

class Seek(smach.StateMachine):
    def __init__(self):
        smach.StateMachine.__init__(self,
                outcomes=['finished','failed'])
        with self:
  #          smach.StateMachine.add('SETNAME',SetName(),
  #                                 transitions={'set':'SETSTARTGOALNAME',
  #                                              'failed':'failed'})
            smach.StateMachine.add('FAKE_STATE',FakeState(),
                                   transitions={'set':'SEARCH',
                                                'failed':'failed'})
            smach.StateMachine.add('SETSTARTGOALNAME',SetStartGoalName(),
                                   transitions={'set':'SELECT_GOAL',
                                                'failed':'failed'})
            smach.StateMachine.add('SELECT_GOAL',SelectNavigationGoal(),
                                   transitions={'selected':'MOVE_BASE_TEMP',
                                                'not_selected':'failed',
                                                'failed':'failed'})
            smach.StateMachine.add('MOVE_BASE_TEMP',MoveBaseTemp(),
                                   transitions={'reached':'OBSERVE',
                                                'failed':'failed'})
            smach.StateMachine.add('MOVE_BASE',ApproachPose(),
                                   transitions={'reached':'OBSERVE',
                                                'not_reached':'failed',
                                                'failed':'failed'})
            smach.StateMachine.add('OBSERVE',Observe(),
                                   transitions={'failed':'failed',
                                     'not_yet_detected':'OBSERVE',
                                                'detected':'SELECT_GOAL',
                                                'search_now':'SEARCH'})

            smach.StateMachine.add('SEARCH',Search(),
                                   transitions={'found':'finished',
                                                'new_search_goal':'SEARCH',
                                                'not_found':'finished',
                                                'failed':'finished'})
            smach.StateMachine.add('ROTATE',Rotate(),
                                   transitions={'finished':'finished',
                                                'failed':'failed'})
            smach.StateMachine.add('TALK',Talk(),
                                   transitions={'found':'finished',
                                                #'not_found':'failed',
                                                'not_found':'ROTATE',
                                                'failed':'failed'})




            #smach.StateMachine.add('DETECT',DetectObjectsFrontside(['milk','pringles'],mode="one"),
            #                       transitions={'detected':'ANNOUNCE',
            #                                    'not_detected':'ANNOUNCE',
            #                                    'failed':'failed'})

            #smach.StateMachine.add('ANNOUNCE',AnnounceFoundObjects(),
            #                       transitions={'announced':'SELECT_GOAL',
            #                                    'not_announced':'SELECT_GOAL',
            #                                    'failed':'failed'})


















class SM(smach.StateMachine):
    def __init__(self):
        smach.StateMachine.__init__(self,outcomes=['ended'])
        with self:
            smach.StateMachine.add('STATE',Seek(),
                transitions={'finished':'ended',
                      'failed':'ended'})

if __name__=='__main__':
  #global PERSON
  #PERSON=sys.argv[1]
  rospy.init_node('SEEK')
  sm = SM()
  sis = smach_ros.IntrospectionServer('SM', sm, 'SM')
  sis.start()
  outcome = sm.execute()
  rospy.spin()
  sis.stop()
