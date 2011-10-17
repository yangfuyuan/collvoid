#!/usr/bin/env python
import roslib; roslib.load_manifest('collvoid_controller')
import rospy
import commands
import string
try:
    import wx
except ImportError:
    raise ImportError,"The wxPython module is required to run this program"

from std_msgs.msg import String
from geometry_msgs.msg import PoseWithCovarianceStamped,PoseStamped
from std_srvs.srv import Empty
from collvoid_local_planner.srv import StateSrv
from collvoid_local_planner.msg import PositionShare

import tf

#import numpy as np

class controller(wx.Frame):
    #numRobots = 12
    #listDone = []

    def __init__(self,parent,id,title):
        wx.Frame.__init__(self,parent,id,title)
        self.parent = parent
        self.initialize()
        
    def initialize(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)


        self.subCommands = rospy.Subscriber("/commandsRobot", String, self.cbCommands)
#        self.subGoal = rospy.Subscriber("/goal",PoseStamped,self.cbGoal)
        self.subCommonPositions = rospy.Subscriber("/commonPositions", PositionShare, self.cbCommonPositions)
        self.pub = rospy.Publisher('/commandsRobot', String)
        self.numRobots = rospy.get_param("/numRobots",12)
        self.robotList = []
        self.robotList.append("all")

        self.reset_srv = rospy.ServiceProxy('/stageros/reset', Empty)

#        for i in range(self.numRobots):
 #           self.robotList.append("/robot_{0}".format(i))


        static_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Controls"), wx.HORIZONTAL)
        sizer.Add(static_sizer, 0)
         
        start = wx.Button(self,-1,label="Start!")
        static_sizer.Add(start, 0)
        self.Bind(wx.EVT_BUTTON, self.start, start)
        
        stop = wx.Button(self,-1,label="Stop!")
        static_sizer.Add(stop, 0)
        self.Bind(wx.EVT_BUTTON, self.stop, stop)

        reset = wx.Button(self,-1,label="Reset!")
        static_sizer.Add(reset, 0)
        self.Bind(wx.EVT_BUTTON, self.reset, reset)


        grid_sizer = wx.GridBagSizer()
        static_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "New Goals"), wx.HORIZONTAL)
        static_sizer.Add(grid_sizer, 0)
        sizer.Add(static_sizer, 0)
 
        self.choiceBox = wx.Choice(self,-1,choices=self.robotList)

        grid_sizer.Add(self.choiceBox,(0,0),(1,2),wx.EXPAND)
        self.SetPosition(wx.Point(200,200))
        self.SetSize(wx.Size(600,200))
        
 #       self.goalX = wx.TextCtrl(self,-1,value=u"0.0")
 #       self.goalY = wx.TextCtrl(self,-1,value=u"0.0")
 #       self.goalAng = wx.TextCtrl(self,-1,value=u"0.0")
        
  #      grid_sizer.Add(self.goalX,(2,1))
  #      grid_sizer.Add(self.goalY,(3,1))
  #      grid_sizer.Add(self.goalAng,(4,1))
      
        setWPon = wx.Button(self,-1,label="WP Planner On")
        grid_sizer.Add(setWPon, (4,0))
        self.Bind(wx.EVT_BUTTON, self.setWPon, setWPon)

        setWPoff = wx.Button(self,-1,label="WP Planner Off")
        grid_sizer.Add(setWPoff, (4,1))
        self.Bind(wx.EVT_BUTTON, self.setWPoff, setWPoff)

        setNewGoal = wx.Button(self,-1,label="Send Next Goal")
        grid_sizer.Add(setNewGoal, (5,0))
        self.Bind(wx.EVT_BUTTON, self.setNewGoal, setNewGoal)
        
        setCircleOn = wx.Button(self,-1,label="Circle On")
        grid_sizer.Add(setCircleOn, (6,0))
        self.Bind(wx.EVT_BUTTON, self.setCircleOn, setCircleOn)

        setCircleOff = wx.Button(self,-1,label="Circle Off")
        grid_sizer.Add(setCircleOff, (6,1))
        self.Bind(wx.EVT_BUTTON, self.setCircleOff, setCircleOff)



#        self.initGuessPubs = []
#        self.state_srv = []
#        for i in range(self.numRobots):
#            publisher = rospy.Publisher("{0}/initialpose".format(robotList[i]),PoseWithCovarianceStamped)
 #           self.initGuessPubs.append(publisher)
 #           self.state_srv.append(rospy.ServiceProxy("{0}/state".format(self.robotList[i]),StateSrv))
        
  #      self.labelX = wx.StaticText(self,-1,label=u'X = ')
        #self.label.SetBackgroundColour(wx.BLUE)
  #      self.labelX.SetForegroundColour(wx.BLACK)
  #      grid_sizer.Add( self.labelX, (2,0) )

        
  #      self.labelY = wx.StaticText(self,-1,label=u'Y = ')
        #self.label.SetBackgroundColour(wx.BLUE)
   #     self.labelY.SetForegroundColour(wx.BLACK)
    #    grid_sizer.Add( self.labelY, (3,0) )
        
   #     self.labelAng = wx.StaticText(self,-1,label=u'Ang in Radian = ')
        #self.label.SetBackgroundColour(wx.BLUE)
   #     self.labelAng.SetForegroundColour(wx.BLACK)
  #      grid_sizer.Add( self.labelAng, (4,0) )

        grid_sizer.AddGrowableCol(0)
        self.SetSizer(sizer)
        self.listDone = []
        #self.SetSizeHints(-1,self.GetSize().y,-1,self.GetSize().y )
        #self.entry.SetFocus()
        #self.entry.SetSelection(-1,-1)
        self.Layout()
        self.Fit()
        self.Show(True)

    def setWPon(self,event):
        str = "%s WP On"%self.choiceBox.GetStringSelection()
        self.pub.publish(String(str))

    def setWPoff(self,event):
        str = "%s WP Off"%self.choiceBox.GetStringSelection()
        self.pub.publish(String(str))
        
               
    def sendInitGuess(self,event):
        num = self.choiceBox.GetSelection()
        msg = PoseWithCovarianceStamped()
        msg.pose.pose.position.x = float(self.goalX.GetValue())
        msg.pose.pose.position.y = float(self.goalY.GetValue())
        yaw = float(self.goalAng.GetValue())
        q = tf.transformations.quaternion_from_euler(0,0, yaw, axes='sxyz')
        msg.pose.pose.orientation.x = q[0];
        msg.pose.pose.orientation.y = q[1];
        msg.pose.pose.orientation.z = q[2];
        msg.pose.pose.orientation.w = q[3];
        self.initGuessPubs[num].publish(msg)

    def cbCommonPositions(self,msg):
        if self.robotList.count(msg.id) == 0:
            rospy.loginfo("robot added")
            self.robotList.append(msg.id)
            self.choiceBox.Append(msg.id)


    def setCircleOn(self,event):
        string = "%s Circle On"%self.choiceBox.GetStringSelection()
        self.pub.publish(String(string))
    
    def setCircleOff(self,event):
        string = "%s Circle Off"%self.choiceBox.GetStringSelection()
        self.pub.publish(String(string))


    def setNewGoal(self,event):
        #rospy.set_param("{0}/goal".format(self.choiceBox.GetStringSelection()),{"x": float(self.goalX.GetValue()),'y':float(self.goalY.GetValue()), "ang":float(self.goalAng.GetValue())})
        str = "%s New Goal"%self.choiceBox.GetStringSelection()
        self.pub.publish(String(str))

    def cbGoal(self,msg):
        self.goalX.SetValue(str(msg.pose.position.x))
        self.goalY.SetValue(str(msg.pose.position.y))
        q = []
        q.append(msg.pose.orientation.x)
        q.append(msg.pose.orientation.y)
        q.append(msg.pose.orientation.z)
        q.append(msg.pose.orientation.w)
        
        self.goalAng.SetValue(str(tf.transformations.euler_from_quaternion(q)[2]))

    def cbCommands(self,msg):
        #rospy.logerr(msg.data)
        if (msg.data != "Start" and msg.data != "Restart"):
            self.listDone.append(msg.data)
            #rospy.loginfo(rospy.get_name()+"vI heard %s",msg.data)
    
    def isDone(self):
    #counter = 0
    #for (name,done) in listDone:
    #    if (done == False):
    #        return False
    #    else:
    #       counter++
    #rospy.logerr("I heard %d robots of %d robots",len(listDone),numRobots)
        if (len(self.listDone) >= self.numRobots): 
            return True
        return False 

    def stop(self,event):
        str = "%s Stop"%self.choiceBox.GetStringSelection()
 #       for service in self.state_srv:
  #          service(False)
       
        self.pub.publish(String(str))

    def start(self,event):
        str = "%s Start"%self.choiceBox.GetStringSelection()
#        for service in self.state_srv:
 #           service(True)
        self.pub.publish(String(str))

    def reset(self,event):
        self.pub.publish("all Stop")
        rospy.sleep(0.2)
        self.pub.publish("all Restart")
        #rospy.sleep(0.2)
        self.reset_srv()
            
    
if __name__ == '__main__':
    #x = np.arange(0, 5, 0.1);
   # y = np.sin(x)
    #plt.plot(x, y)
    #plt.show()
    rospy.init_node('controller')
    app = wx.App()
    frame = controller(None,-1,'Controller')

    app.MainLoop()
