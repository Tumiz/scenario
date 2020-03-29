from scenario import *
import time
scenario=Scenario()
s=Cube("s")
s.pose.position=Vector3(0,1,1)
s.color=Color(b=1)
s.angular_velocity=Vector3(x=0.1)
scenario.add(s)
s1=Sphere("s1")
s1.pose.position=Vector3(1,1,1)
s1.color=Color(r=1)
s1.radius=0.5
s1.velocity=Vector3(0.1,0.1)
scenario.add(s1)
while scenario.t<10:
    scenario.step(0.1)
    time.sleep(0.1)
    scenario.render()