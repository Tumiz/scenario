from scenario import Vector3

a=Vector3([1,2,3,4,5,6])
print(a)
l=a.norm()
print("l",l)
a.normalize()
print("after normalizing",a)
print("------------------")
b=Vector3()
print(b)
b.normalize()
print(b)
print("----------------1d vector-------------")
c1=Vector3(2,3,4)
print("c1 normalized",c1.normalized())
print("c1",c1)
c2=Vector3.Rand(1)
print("c2",c2)
print(c1.dot(c2))
print(c1.cross(c2))
print("----------nd vector--------")
print("Vector:")
r=Vector3.Rand(3)
print(r)
print("Length:")
print(r.norm())
print("Normalized:")
print(r.normalized())
print("------------------")
a=Vector3.Rand(4)
b=Vector3.Rand(4)
c=2*a
print("Length")
print(a.norm())
print("Cross:")
print(a.cross(b))
print("Dot")
print(a.dot(b))
print("-----------angle------------")
print("angle to vectors:")
print(a.angle_to_vector(b))
print("angle to planes:")
print(a.angle_to_plane(b))
print("rotation to")
print(a.rotation_to(b))
print("------------parallel---------")
print(a.is_parallel_to_vector(b))
print(a.is_parallel_to_vector(c))
print(a.is_perpendicular_to_vector(b))
print(a)
print(a[0].norm())
a[0].normalize()
print(a[0].norm())
print(a[0].cross(Vector3.Rand(1)))
print(b.dot(a[0]))
print("-------------------------")
a=Vector3(1,0,0.7)
b=Vector3(1.0,0.,0.7)
c=Vector3(1.1,0,0.7)
print(a==b,b==c,a!=c)