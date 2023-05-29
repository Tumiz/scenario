# Copyright (c) Tumiz.
# Distributed under the terms of the GPL-3.0 License.
from __future__ import annotations
import numpy
from IPython.display import display, HTML
from typing import Dict
import pathlib
import uuid
import json
import struct

pi = numpy.arccos(-1)
__module__ = __import__(__name__)


def sign(v):
    return numpy.sign(v, where=v != 0, out=numpy.ones_like(v))


class View:
    __preload__ = HTML(filename=pathlib.Path(__file__).parent/"viewer.html")
    display(__preload__)
    __template__ = """
<div id=PY#D_ID>
</div>
<script>
	new Viewer("PY#D_ID", PY#D_ARGS)
</script>
    """

    def __init__(self) -> None:
        self.cache: Dict[float, list] = {}
        self.min = []
        self.max = []

    def __render_args__(self, t, **args):
        t = round(t, 3)
        if t in self.cache:
            self.cache[t].append(args)
        else:
            self.cache[t] = [args]
        return self

    def _repr_html_(self):
        html = self.__template__.replace("PY#D_ID", str(uuid.uuid1())).replace(
            "PY#D_ARGS", json.dumps(self.__dict__))
        self.cache.clear()
        self.max = []
        self.min = []
        return html

    def save(self, name):
        open(name, "w").write(self.__preload__.data + self._repr_html_())

    def render(self, obj: Point, t=0):
        if self.max == []:
            self.max = obj.xyz.flatten().max().tolist()
            self.min = obj.xyz.flatten().min().tolist()
        else:
            self.max = numpy.max(
                [self.max, obj.xyz.flatten().max()], axis=0).tolist()
            self.min = numpy.min(
                [self.min, obj.xyz.flatten().min()], axis=0).tolist()
        return self.__render_args__(t=t, mode=obj.TYPE, vertex=obj.xyz.ravel(
        ).tolist(), color=obj.color.ravel().tolist())

    def label(self, text: str, position: list = [0, 0, 0], color="grey", t=0):
        return self.__render_args__(t=t, mode="TEXT", text=text,
                                    vertex=position, color=color)


default_view = View()


def render(*objs, t=0):
    for obj in objs:
        default_view.render(obj, t)
    return default_view


def label(text, position: list = [0, 0, 0], color="grey", t=0):
    return default_view.label(text, position, color, t)


def show():
    return default_view


def read_pcd(path):
    f = open(path, "rb")
    data_type = ""
    ret = []
    tp_map = {
        (1, "I"): "b",
        (1, "U"): "B",
        (2, "I"): "h",
        (2, "U"): "H",
        (4, "I"): "i",
        (4, "U"): "I",
        (4, "F"): "f",
        (8, "I"): "q",
        (8, "U"): "Q",
        (8, "F"): "d"
    }
    while True:
        if "binary" not in data_type:
            r = str(f.readline(), encoding="utf-8")[:-1]
            if not r:
                break
            elif r.startswith("FIELDS"):
                cols = r.replace("FIELDS ", "").split(" ")
            elif r.startswith("SIZE"):
                size = [int(s) for s in r.replace("SIZE ", "").split(" ")]
            elif r.startswith("TYPE"):
                tp = r.replace("TYPE ", "").split(" ")
            elif r.startswith("POINTS"):
                count = int(r.replace("POINTS ", ""))
            elif r.startswith("DATA"):
                data_type = r.replace("DATA ", "")
            elif data_type == "ascii":
                ret.append([float(s) for s in r.split(" ")])
        elif "compressed" in data_type:
            break
        else:
            if count > 0:
                count -= 1
            else:
                break
            tmp = []
            for s, t in zip(size, tp):
                bt = f.read(s)
                d, = struct.unpack(tp_map[(s, t)], bt)
                tmp.append(d)
            ret.append(tmp)
    ret = Vector(ret)
    for i, c in enumerate(cols):
        setattr(ret, c, ret[:, i])
    return ret


class Data(numpy.ndarray):
    BASE_SHAPE = ()

    def __new__(cls, data: list | numpy.ndarray = [], n=()):
        return numpy.tile(data, n + (1,)).view(cls)

    def __imatmul__(self, value) -> Data:
        return self @ value

    def tile(self, *n):
        return numpy.tile(self, n + self.ndim * (1,))

    def flatten(self):
        return self.reshape(-1, *self.BASE_SHAPE)

    @property
    def n(self):
        base_dims = len(self.BASE_SHAPE)
        if base_dims:
            return self.shape[:-base_dims]
        else:
            return self.shape

    @classmethod
    def Rand(cls, *n) -> Data:
        n += cls.BASE_SHAPE
        return numpy.random.rand(*n).view(cls)

    @classmethod
    def load_csv(cls, path):
        return numpy.loadtxt(path, delimiter=',').view(cls)

    def save_csv(self, path):
        numpy.savetxt(path, self, delimiter=',')


class Vector(Data):
    # Base class of Vector2, Vector3, Vector4
    def __new__(cls, data: list | numpy.ndarray = [], n=()):
        return super().__new__(cls, data, n)

    @property
    def x(self):
        return self[..., 0].view(numpy.ndarray)

    @x.setter
    def x(self, v):
        self[..., 0] = v

    @property
    def y(self):
        return self[..., 1].view(numpy.ndarray)

    @y.setter
    def y(self, v):
        self[..., 1] = v

    @property
    def z(self):
        return self[..., 2].view(numpy.ndarray)

    @z.setter
    def z(self, v):
        self[..., 2] = v

    @property
    def xy(self) -> Vector2:
        return self[..., 0:2].view(Vector2)

    @xy.setter
    def xy(self, v):
        self[..., 0:2] = v

    @property
    def xyz(self) -> Vector3:
        return self[..., 0:3].view(Vector3)

    @xyz.setter
    def xyz(self, v):
        self[..., 0:3] = v

    @property
    def U(self) -> Vector:
        '''
        unit vector, direction vector
        '''
        n = self.L
        return numpy.divide(self, n, where=n != 0)

    @property
    def H(self) -> Vector:
        '''
        Homogeneous vector
        '''
        ret = numpy.insert(self, self.shape[-1], 1, axis=self.ndim-1)
        w = ret.shape[-1]
        if w in [2, 3, 4]:
            return ret.view(getattr(__module__, f"Vector{w}"))
        else:
            return ret.view(Vector)

    @property
    def M(self) -> Vector:
        # mean vector
        return super().mean(axis=self.ndim-2)

    @property
    def L(self) -> Vector:
        # length
        return numpy.linalg.norm(self, axis=self.ndim - 1, keepdims=True)

    def min(self) -> Vector:
        return super().min(axis=self.ndim-2)

    def max(self) -> Vector:
        return super().max(axis=self.ndim-2)

    def diff(self, n=1) -> Vector:
        return numpy.diff(self, n, axis=self.ndim-2)

    def to_pcd(self, path, fields=""):
        w = self.shape[-1]
        pcd = self.reshape(-1, w)
        width = len(pcd)
        size = " ".join(["4"] * w)
        tp = " ".join(["F"] * w)
        count = " ".join(["1"] * w)
        if not fields:
            fields = " ".join([str(i) for i in range(w)])
        f = open(path, "w")
        f.write('''# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS {}
SIZE {}
TYPE {}
COUNT {}
WIDTH {}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {}
DATA ascii
'''.format(fields, size, tp, count, width, width))
        for p in pcd:
            f.write(" ".join([str(a) for a in p]) + "\n")
        f.close()


class Vector2(Vector):
    BASE_SHAPE = 2,

    def __new__(cls, data: list | numpy.ndarray = [], n=()):
        return super().__new__(cls, data, n)


class Vector3(Vector):
    BASE_SHAPE = 3,

    def __new__(cls, data: list | numpy.ndarray = [], x=0, y=0, z=0, n=()):
        '''
            Represent points, positions and translations
        '''
        if numpy.any(data):
            return super().__new__(cls, data, n)
        else:
            n += max(numpy.shape(x), numpy.shape(y), numpy.shape(z))
            ret = super().__new__(cls, [0., 0., 0.], n)
            ret.x = x
            ret.y = y
            ret.z = z
            return ret

    @classmethod
    def grid(cls, x=0, y=0, z=0) -> Vector3:
        n = numpy.shape(x) + numpy.shape(y) + numpy.shape(z)
        ret = super().__new__(cls, [0., 0., 0.], n)
        i = numpy.arange(len(n))
        ret.x = numpy.expand_dims(x, axis=i[i != 0].tolist())
        ret.y = numpy.expand_dims(y, axis=i[i != 1].tolist())
        ret.z = numpy.expand_dims(z, axis=i[i != 2].tolist())
        return ret

    @classmethod
    def circle(cls, radius=1, segments=20) -> Vector3:
        a = numpy.linspace(0, 2*numpy.pi, segments, False)
        return cls(x=radius * numpy.sin(a), y=radius * numpy.cos(a))

    def __matmul__(self, value: Transform) -> Vector3:
        if type(value) is Transform:
            return numpy.matmul(self.H, value)[..., 0:3].view(Vector3)
        else:
            return self.__matmul__(value)

    def dot(self, v) -> Vector3:
        if type(v) is Vector3:
            product = self * v
            return product.sum(axis=product.ndim - 1, keepdims=True).view(numpy.ndarray)
        else:
            return numpy.dot(self, v)

    def cross(self, v: numpy.ndarray) -> Vector3:
        return numpy.cross(self, v).view(self.__class__)

    def angle_to_vector(self, to: numpy.ndarray) -> Vector3:
        cos = self.dot(to) / self.L / Vector3(to).L
        return numpy.arccos(cos)

    def angle_to_plane(self, normal: numpy.ndarray) -> float:
        return numpy.pi / 2 - self.angle_to_vector(normal)

    def is_parallel_to_vector(self, v: numpy.ndarray) -> bool:
        return self.U == v.U

    def is_parallel_to_plane(self, normal: numpy.ndarray) -> bool:
        return self.is_perpendicular_to_vector(normal)

    def is_perpendicular_to_vector(self, v: numpy.ndarray) -> bool:
        return self.dot(v) == 0

    def is_perpendicular_to_plane(self, normal: numpy.ndarray) -> bool:
        return self.is_parallel_to_vector(normal)

    def scalar_projection(self, v: numpy.ndarray) -> float:
        return self.dot(v) / v.L

    def vector_projection(self, v: numpy.ndarray) -> Vector3:
        return self.scalar_projection(v) * v / v.L

    def distance_to_line(self, p0: numpy.ndarray, p1: numpy.ndarray) -> float:
        v0 = p1 - p0
        v1 = self - p0
        return v0.cross(v1).L / v0.L

    def distance_to_plane(self, n: numpy.ndarray, p: numpy.ndarray) -> float:
        # n: normal vector of the plane
        # p: a point on the plane
        v = self - p
        return v.scalar_projection(n)

    def projection_on_line(
        self, p0: numpy.ndarray, p1: numpy.ndarray
    ) -> numpy.ndarray:
        return p0 + (self - p0).vector_projection(p1 - p0)

    def projection_on_plane(self, plane) -> numpy.ndarray:
        return self + (plane.position[:, numpy.newaxis] - self).vector_projection(
            plane.normal[:, numpy.newaxis]
        )

    def interpolate(self, x, xp) -> Vector3:
        '''
        linear interpolation
        x: 1-D array, the data to be interpolated.
        xp: 1-D array, the data to interpolate into. For example, time series.
        '''
        x = numpy.array(x)
        xp = numpy.array(xp)
        assert x.ndim <= xp.ndim == 1
        i = numpy.searchsorted(xp, x).clip(1, len(xp)-1)
        x0 = xp[i-1]
        x1 = xp[i]
        d = ((x-x0)/(x1-x0)).reshape(-1, 1)
        f0 = self[i-1]
        f1 = self[i]
        return (1-d)*f0+d*f1

    def as_scaling(self) -> Transform:
        ret = Transform(n=self.n)
        ret[..., 0, 0] = self[..., 0]
        ret[..., 1, 1] = self[..., 1]
        ret[..., 2, 2] = self[..., 2]
        return ret

    def as_translation(self) -> Transform:
        ret = Transform(n=self.n)
        ret[..., 3, 0] = self[..., 0]
        ret[..., 3, 1] = self[..., 1]
        ret[..., 3, 2] = self[..., 2]
        return ret

    def as_point(self) -> Point:
        entity = Point(*self.n)
        entity.xyz = self
        return entity

    def as_line(self) -> LineSegment:
        n = list(self.n)
        n[-1] = (n[-1] - 1) * 2
        entity = LineSegment(*n)
        entity.start.xyz = self[..., :-1, :]
        entity.end.xyz = self[..., 1:, :]
        return entity

    def as_lineloop(self) -> LineSegment:
        n = list(self.n)
        n[-1] = n[-1] * 2
        entity = LineSegment(*n)
        entity.start.xyz = self
        entity.end.xyz = numpy.roll(self, -1, axis=self.ndim - 2)
        return entity

    def as_linesegment(self) -> LineSegment:
        entity = LineSegment(*self.n)
        entity.xyz = self
        return entity

    def as_shape(self) -> Triangle:
        v = numpy.repeat(self, 3, axis=self.ndim-2)
        v = numpy.roll(v, 1, axis=v.ndim-2)
        c = self.M[..., numpy.newaxis, :]
        v[..., 1::3, :] = c
        return v.view(Vector3).as_triangle()

    def as_triangle(self) -> Triangle:
        entity = Triangle(*self.n)
        entity.xyz = self
        return entity

    def as_vector(self) -> LineSegment:
        entity = LineSegment(*self.n, 2)
        entity.start.xyz = 0
        entity.end.xyz = numpy.expand_dims(self, axis=self.ndim - 1)
        return entity


class Vector4(Vector):
    BASE_SHAPE = 4,

    def __new__(cls, xyzw_list: list | numpy.ndarray = [], x=0, y=0, z=0, w=1, n=()):
        if numpy.any(xyzw_list):
            return super().__new__(cls, xyzw_list, n)
        else:
            n += max(numpy.shape(x), numpy.shape(y),
                     numpy.shape(z), numpy.shape(w))
            ret = super().__new__(cls, [0., 0., 0., 1.], n)
            ret.x = x
            ret.y = y
            ret.z = z
            ret.w = w
            return ret

    @property
    def w(self):
        return self[..., 3].view(numpy.ndarray)

    @w.setter
    def w(self, v):
        self[..., 3] = v

    @property
    def wxyz(self) -> Vector:
        ret = Vector([0., 0., 0., 0.], n=self.n)
        ret[..., 0] = self.w
        ret[..., 1:4] = self.xyz
        return ret

    def from_axis_angle_to_quaternion(self) -> Vector4:
        q = Vector4(n=self.n)
        q.xyz = numpy.sin(self.w / 2)[..., numpy.newaxis] * self.xyz.U
        q.w = numpy.cos(self.w / 2)
        return q

    def from_quaternion_to_axis_angle(self) -> Vector4:
        q = Vector4(n=self.n)
        q.w = numpy.arccos(self.w) * 2
        sin_ha = numpy.sin(q.w / 2)[..., numpy.newaxis]
        q.xyz = numpy.divide(self.xyz, sin_ha,
                             where=sin_ha != 0)
        return q


class Transform(Data):
    BASE_SHAPE = 4, 4

    def __new__(cls, data: list | numpy.ndarray = numpy.eye(4), n=()):
        return super().__new__(cls, data, n + (1,))

    @classmethod
    def from_translation(cls, xyz_list: list | numpy.ndarray = [], x=0, y=0, z=0, n=()) -> Transform:
        '''
        translation matrix
        '''
        return Vector3(xyz_list, x, y, z, n).as_translation()

    @classmethod
    def from_scaling(cls, xyz_list: list | numpy.ndarray = [], x=1, y=1, z=1, n=()) -> Transform:
        '''
        scaling matrix
        '''
        return Vector3(xyz_list, x, y, z, n).as_scaling()

    @classmethod
    def Rx(cls, a, n=()) -> Transform:
        a = numpy.array(a)
        ret = numpy.full(n + a.shape + (4, 4), numpy.eye(4))
        cos = numpy.cos(a)
        sin = numpy.sin(a)
        ret[..., 1, 1] = cos
        ret[..., 1, 2] = sin
        ret[..., 2, 1] = -sin
        ret[..., 2, 2] = cos
        return ret.view(cls)

    def rx(self, a, n=()) -> Transform:
        return self @ self.Rx(a, n)

    @classmethod
    def Ry(cls, a, n=()) -> Transform:
        a = numpy.array(a)
        ret = numpy.full(n + a.shape + (4, 4), numpy.eye(4))
        cos = numpy.cos(a)
        sin = numpy.sin(a)
        ret[..., 0, 0] = cos
        ret[..., 0, 2] = -sin
        ret[..., 2, 0] = sin
        ret[..., 2, 2] = cos
        return ret.view(cls)

    def ry(self, a, n=()) -> Transform:
        return self @ self.Ry(a, n)

    @classmethod
    def Rz(cls, a, n=()) -> Transform:
        a = numpy.array(a)
        ret = numpy.full(n + a.shape + (4, 4), numpy.eye(4))
        cos = numpy.cos(a)
        sin = numpy.sin(a)
        ret[..., 0, 0] = cos
        ret[..., 0, 1] = sin
        ret[..., 1, 0] = -sin
        ret[..., 1, 1] = cos
        return ret.view(cls)

    def rz(self, a, n=()) -> Transform:
        return self @ self.Rz(a, n)

    @classmethod
    def from_axis_angle(cls, xyz_angle_list: list | Vector4 = [], axis=[0, 0, 1], angle=0, n=()) -> Transform:
        axis = Vector3(axis)
        q = Vector4(xyz_angle_list, axis.x, axis.y, axis.z,
                    angle, n).from_axis_angle_to_quaternion()
        return cls.from_quaternion(q)

    def as_axis_angle(self):
        return self.as_quaternion().from_quaternion_to_axis_angle()

    @classmethod
    def from_rotation_vector(cls, xyz_list: list | Vector3 = [], x=0, y=0, z=0, n=()) -> Transform:
        rv = Vector3(xyz_list, x, y, z, n)
        axis_angle_list = Vector4(n=rv.n)
        axis_angle_list.w = rv.L
        axis_angle_list.xyz = rv.U
        return cls.from_axis_angle(axis_angle_list)

    def as_rotation_vector(self):
        q = self.as_axis_angle()
        return q.xyz.U * q.w

    @classmethod
    def from_two_vectors(cls, a: list | Vector3, b: list | Vector3) -> Transform:
        a = Vector3(a)
        b = Vector3(b)
        q = Vector4(n=max(a.n, b.n))
        q.w = a.angle_to_vector(b).squeeze()
        q.xyz = a.cross(b)
        return cls.from_axis_angle(q)

    @classmethod
    def from_quaternion(cls, xyzw_list: list | numpy.ndarray) -> Transform:
        q = Vector4(xyzw_list)
        ret = cls(n=q.shape[:-1])
        ret[..., 0, 0] = 1 - 2 * q.y ** 2 - 2 * q.z ** 2
        ret[..., 0, 1] = 2 * q.w * q.z + 2 * q.x * q.y
        ret[..., 0, 2] = -2 * q.w * q.y + 2 * q.x * q.z
        ret[..., 1, 0] = -2 * q.w * q.z + 2 * q.x * q.y
        ret[..., 1, 1] = 1 - 2 * q.x ** 2 - 2 * q.z ** 2
        ret[..., 1, 2] = 2 * q.w * q.x + 2 * q.y * q.z
        ret[..., 2, 0] = 2 * q.w * q.y + 2 * q.x * q.z
        ret[..., 2, 1] = -2 * q.w * q.x + 2 * q.y * q.z
        ret[..., 2, 2] = 1 - 2 * q.x ** 2 - 2 * q.y ** 2
        return ret

    def as_quaternion(self) -> Vector4:
        q = Vector4(n=self.n)
        q.w = numpy.sqrt(1+self[..., 0, 0]+self[..., 1, 1] + self[..., 2, 2])/2
        m0 = self[q.w == 0]
        m1, w1 = self[q.w != 0], q.w[q.w != 0]
        q.x[q.w != 0] = numpy.divide(m1[..., 1, 2]-m1[..., 2, 1], 4*w1)
        q.y[q.w != 0] = numpy.divide(m1[..., 2, 0]-m1[..., 0, 2], 4*w1)
        q.z[q.w != 0] = numpy.divide(m1[..., 0, 1]-m1[..., 1, 0], 4*w1)
        q.x[q.w == 0] = sign(m0[..., 1, 2]-m0[..., 2, 1]) * numpy.sqrt(
            1+m0[..., 0, 0]-m0[..., 1, 1] - m0[..., 2, 2])/2
        q.y[q.w == 0] = sign(m0[..., 2, 0]-m0[..., 0, 2]) * numpy.sqrt(
            1-m0[..., 0, 0]+m0[..., 1, 1] - m0[..., 2, 2])/2
        q.z[q.w == 0] = sign(m0[..., 0, 1]-m0[..., 1, 0]) * numpy.sqrt(
            1-m0[..., 0, 0]-m0[..., 1, 1] + m0[..., 2, 2])/2
        return q

    @classmethod
    def from_euler(cls, sequence: str, angles_list: list | numpy.ndarray) -> Transform:
        lo = sequence.lower()
        v = numpy.array(angles_list)
        m = {a: getattr(cls, "R" + a.lower()) for a in 'xyz'}
        if sequence.islower():
            return m[lo[0]](v[..., 0]) @ m[lo[1]](v[..., 1]) @ m[lo[2]](v[..., 2])
        else:
            return m[lo[2]](v[..., 2]) @ m[lo[1]](v[..., 1]) @ m[lo[0]](v[..., 0])

    def as_euler(self, sequence: str):
        extrinsic = sequence.islower()
        lo = sequence.lower()
        ret = Vector3(n=self.n)
        i = [0, 1, 2] if extrinsic else [2, 1, 0]
        m = [0 if o == 'x' else 1 if o == 'y' else 2 for o in lo]
        if not extrinsic:
            m.reverse()

        def f(x, y): return -1 if x-y == 2 or x - y == -1 else 1
        a = [f(m[1], m[0]), f(m[2], m[0]), f(m[2], m[1])]
        if a.count(-1) > 1:
            b = [-1, 1, 1, -1, 1]
        else:
            b = [1, a[0], a[1], 1, a[2]]

        ret[..., i[0]] = numpy.arctan2(
            b[0]*self[..., m[1], m[2]], b[1]*self[..., 3-m[0]-m[1], m[2]])
        ret[..., i[1]] = getattr(numpy, 'arccos' if m[0] == m[2] else 'arcsin')(
            b[2]*self[..., m[0], m[2]])
        ret[..., i[2]] = numpy.arctan2(
            b[3]*self[..., m[0], m[1]], b[4]*self[..., m[0], 3-m[1]-m[2]])
        return ret

    @classmethod
    def from_rpy(cls, angles_list: list | numpy.ndarray) -> Transform:
        return cls.from_euler('XYZ', angles_list)

    def as_rpy(self):
        return self.as_euler('XYZ')

    @property
    def translation_vector(self) -> Vector3:
        return self[..., 3, 0:3].view(Vector3)

    @translation_vector.setter
    def translation_vector(self, v: Vector3):
        self[..., 3, 0:3] = v

    @property
    def scaling_vector(self) -> Vector3:
        return numpy.linalg.norm(self[..., 0:3, 0:3], axis=self.ndim-1).view(Vector3)

    @scaling_vector.setter
    def scaling_vector(self, v: Vector3):
        self[:] = v.as_scaling() @ self.scaling.I @ self

    @property
    def translation(self) -> Transform:
        ret = Transform(*self.n)
        ret[..., 3, 0:3] = self.translation_vector
        return ret

    @translation.setter
    def translation(self, v: numpy.ndarray):
        self[..., 3, :3] = v[..., 3, :3]

    @property
    def scaling(self) -> Transform:
        ret = Transform(*self.n)
        ret[..., range(3), range(3)] = self.scaling_vector
        return ret

    @scaling.setter
    def scaling(self, v: numpy.ndarray):
        self[:] = v @ self.scaling.I @ self

    @property
    def rotation(self) -> Transform:
        return self.scaling.I @ self @ self.translation.I

    @rotation.setter
    def rotation(self, v):
        self[:] = self.scaling @ v @ self.translation

    @property
    def I(self) -> Transform:
        return numpy.linalg.inv(self)

    @classmethod
    def from_perspective(cls, fovy, aspect, near, far) -> Transform:
        f = 1 / numpy.tan(fovy/2)
        range_inv = 1.0 / (near - far)
        return numpy.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (near + far) * range_inv, 1],
            [0, 0, -2 * near * far * range_inv, 0]
        ])

    @classmethod
    def from_orthographic(cls, l, r, t, b, n, f):
        pass

    def interpolate(self, x, xp) -> Transform:
        '''
        Linear interpolation
        x: 1-D array, the data to be interpolated.
        xp: 1-D array, the data to interpolate into. For example, time series.
        Only translation, rotation and scaling can be interpolated
        '''
        xp = numpy.array(xp)
        x = numpy.array(x)
        i = numpy.searchsorted(xp, x).clip(1, len(xp)-1)
        x0 = xp[i-1]
        x1 = xp[i]
        d: numpy.ndarray = (x-x0)/(x1-x0)
        r0: Transform = self.rotation[i-1]
        r1: Transform = self.rotation[i]
        t0: Vector3 = self.translation_vector[i-1]
        t1: Vector3 = self.translation_vector[i]
        s0: Vector3 = self.scaling_vector[i-1]
        s1: Vector3 = self.scaling_vector[i]
        angle, axis = (r0.I@r1).as_angle_axis()
        rotation = Transform.from_angle_axis(d*angle, axis)
        translation = (d[..., numpy.newaxis] * (t1 - t0)).as_translation()
        scaling = (d[..., numpy.newaxis] * s1 / s0).as_scaling()
        return self[i-1]@scaling@rotation@translation


class Color(Vector):
    BASE_SHAPE = 4,

    def __new__(cls, data: numpy.ndarray | list = [], r=0, g=0, b=0, a=1, n=()):
        if numpy.any(data):
            return super().__new__(cls, data, n)
        else:
            n += max(numpy.shape(r), numpy.shape(g),
                     numpy.shape(b), numpy.shape(a))
            ret = super().__new__(cls, [0., 0., 0., 1.], n)
            ret[..., 0] = r
            ret[..., 1] = g
            ret[..., 2] = b
            ret[..., 3] = a
        return ret

    @classmethod
    def map(cls, value, start, end):
        center = (start + end)/2
        width = (end - start)/2
        r = numpy.maximum(value - center, 0)/width
        g = 1-numpy.abs(value - center)/width
        b = numpy.maximum(center - value, 0)/width
        return cls(r=r, g=g, b=b)

    @classmethod
    def standard(cls, *n):
        size = numpy.prod(n)
        c = int(numpy.power(size, 1/3)) + 1
        s = numpy.linspace(.3, 1, c)
        rgb = Vector3.grid(x=s, y=s, z=s).flatten()[:size]
        return cls(rgb.H).reshape(n + (4,))

    @property
    def r(self):
        return self[..., 0].view(numpy.ndarray)

    @r.setter
    def r(self, v):
        self[..., 0] = v

    @property
    def g(self):
        return self[..., 1].view(numpy.ndarray)

    @g.setter
    def g(self, v):
        self[..., 1] = v

    @property
    def b(self):
        return self[..., 2].view(numpy.ndarray)

    @b.setter
    def b(self, v):
        self[..., 2] = v

    @property
    def a(self):
        return self[..., 3].view(numpy.ndarray)

    @a.setter
    def a(self, v):
        self[..., 3] = v

    @property
    def rgb(self):
        return self[..., :-1].view(Vector3)


class Point(Vector):
    BASE_SHAPE = 7,
    TYPE = "POINTS"

    def __new__(cls, *n):
        ret = numpy.empty(n + cls.BASE_SHAPE).view(cls)
        ret.color = Color.standard(*(n[:-1] + (1,)))
        ret.color.a = 1
        return ret

    @property
    def color(self) -> Color:
        return self[..., 3:7].view(Color)

    @color.setter
    def color(self, v):
        self[..., 3:7] = v

    def paint(self, color):
        self.color = color
        return self

    def __add__(self, v: Point) -> Point:
        assert self.TYPE == v.TYPE, "Different TYPE"
        return numpy.concatenate((self, v), axis=0).view(self.__class__)

    def __matmul__(self, transform: Transform) -> Point:
        vertex = self.xyz @ transform
        ret = self.__class__(*vertex.n)
        ret.xyz = vertex
        return ret

    def _repr_html_(self):
        return render(self)._repr_html_()


class Triangle(Point):
    TYPE = "TRIANGLES"

    def __new__(cls, *n):
        ret = super().__new__(cls, *n)
        return ret


class LineSegment(Point):
    TYPE = "LINES"

    def __new__(cls, *n):
        ret = super().__new__(cls, *n)
        return ret

    @property
    def start(self):
        return self[..., ::2, :].view(Point)

    @property
    def end(self):
        return self[..., 1::2, :].view(Point)


class Camera:
    def __init__(self, *n):
        self.transform = Transform(*n)
        self.projection = Transform(*n)

    def set_perspective(self, fov, aspect, near, far):
        self.projection = Transform.from_perspective(fov, aspect, near, far)

    @property
    def matrix(self):
        return self.transform.I @ self.projection


def cube(size_x=1, size_y=1, size_z=1) -> LineSegment:
    k = Vector3.grid([-.5, .5], [-.5, .5], [-.5, .5]).flatten() * \
        (size_x, size_y, size_z)
    k: Vector3 = k[[0, 1, 2, 3, 4, 5, 6, 7, 0, 2,
                   2, 6, 6, 4, 4, 0, 1, 3, 3, 7, 7, 5, 5, 1], :]
    return k.as_linesegment()


def car(wheelbase=3, wheel_radius=0.3, track_width=1.6, height=1.5, front_overhang=1, rear_overhang=1) -> LineSegment:
    size_x = wheelbase+front_overhang+rear_overhang
    size_y = track_width
    size_z = height-wheel_radius
    body = cube(size_x, size_y, size_z).xyz
    body @= Transform.from_translation(x=size_x /
                                       2-rear_overhang, z=size_z/2+wheel_radius)
    wheel = Vector3.circle(wheel_radius).as_lineloop().xyz
    wheel @= Transform.from_rpy([pi/2, 0, 0]) @ Vector3.grid(x=[wheelbase, 0], y=[-size_y/2, size_y/2], z=wheel_radius
                                                             ).as_translation()
    return numpy.vstack((body.flatten(), wheel.flatten())).view(Vector3).as_linesegment()


def axis(size=5) -> LineSegment:
    a = Vector3([[size, 0, 0], [0, size, 0], [0, 0, size]]).as_vector()
    a[0].color = Color(r=1)
    a[1].color = Color(g=1)
    a[2].color = Color(b=1)
    return a
