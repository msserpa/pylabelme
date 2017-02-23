#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Michael Pitidis, Hussein Abdulwahid.
#
# This file is part of Labelme.
#
# Labelme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Labelme is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labelme.  If not, see <http://www.gnu.org/licenses/>.
#

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from lib import distance

# TODO:
# - [opt] Store paths instead of creating new ones at each paint.

DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)

class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    ## The following class variables influence the drawing
    ## of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    def __init__(self, label=None, line_color=None):
        self.label = label
        self.points = []
        self.fill = False
        self.selected = False

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
            }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

    def close(self):
        assert len(self.points) > 2
        self._closed = True

    # msserpa: it is the original addPoint. Now it's used to add points from a file.
    def addPointOld(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    # msserpa: this new version of addPoint wait for user draw two points:
    # a center point (points[0]) and a radius point (points[1]) which are
    # used to draw a square.
    def addPoint(self, point):
        self.points.append(point)
        if len(self.points) == 2:
            dist = distance(self.points[1] - self.points[0])

            a = QPointF(self.points[0].x() - dist, self.points[0].y() - dist)
            b = QPointF(self.points[0].x() - dist, self.points[0].y() + dist)
            c = QPointF(self.points[0].x() + dist, self.points[0].y() + dist)
            d = QPointF(self.points[0].x() + dist, self.points[0].y() - dist)

            self.popPoint()
            self.popPoint()

            self.points.append(a)
            self.points.append(b)
            self.points.append(c)
            self.points.append(d)

            self.close()            

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def paint(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)

            line_path = QPainterPath()
            vrtx_path = QPainterPath()

            line_path.moveTo(self.points[0])
            # Uncommenting the following line will draw 2 paths
            # for the 1st vertex, and make it non-filled, which
            # may be desirable.
            #self.drawVertex(vrtx_path, 0)

            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                self.drawVertex(vrtx_path, i)
            if self.isClosed():
                line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.vertex_fill_color)
            if self.fill:
                color = self.select_fill_color if self.selected else self.fill_color
                painter.fillPath(line_path, color)

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d/2, point.y() - d/2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d/2.0, d/2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        for i, p in enumerate(self.points):
            if distance(p - point) <= epsilon:
                return i
        return None

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def makePath(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    # msserpa: this new version of moveVertex is used to handle the moves and
    # keep the polygon a square.def moveVertexBy(self, i, offset):
    def moveVertexBy(self, i, offset):
        if i == 0:
            if offset.x() >= 0 or offset.y() >= 0:
                offset = QPointF(+0.5, +0.5)
            else:
                offset = QPointF(-0.5, -0.5)

            old_sup_esq = self.points[0]
            old_inf_esq = self.points[1]
            old_inf_dir = self.points[2]
            old_sup_dir = self.points[3]

            self.points[0] = self.points[0] + offset

            sup_dir_x = old_sup_dir.x() - offset.x()

            inf_esq_x = self.points[0].x()
            inf_dir_x = sup_dir_x

            inf_esq_y = old_inf_esq.y() - offset.y()
            
            sup_dir_y = self.points[0].y()
            inf_dir_y = inf_esq_y

            self.points[1] = QPointF(inf_esq_x, inf_esq_y)
            self.points[2] = QPointF(inf_dir_x, inf_dir_y)
            self.points[3] = QPointF(sup_dir_x, sup_dir_y)
        elif i == 1:
            if offset.x() >= 0 or offset.y() <= 0:
                offset = QPointF(+0.5, -0.5)
            else:
                offset = QPointF(-0.5, +0.5)

            old_sup_esq = self.points[0]
            old_inf_esq = self.points[1]
            old_inf_dir = self.points[2]
            old_sup_dir = self.points[3]

            self.points[1] = self.points[1] + offset

            sup_dir_x = old_sup_dir.x() - offset.x()

            sup_esq_x = self.points[1].x()
            inf_dir_x = sup_dir_x

            sup_esq_y = old_sup_esq.y() - offset.y()
            
            sup_dir_y = sup_esq_y
            inf_dir_y = self.points[1].y()

            self.points[0] = QPointF(sup_esq_x, sup_esq_y)
            self.points[2] = QPointF(inf_dir_x, inf_dir_y)
            self.points[3] = QPointF(sup_dir_x, sup_dir_y)
        elif i == 2:
            if offset.x() >= 0 or offset.y() >= 0:
                offset = QPointF(+0.5, +0.5)
            else:
                offset = QPointF(-0.5, -0.5)

            old_sup_esq = self.points[0]
            old_inf_esq = self.points[1]
            old_inf_dir = self.points[2]
            old_sup_dir = self.points[3]

            self.points[2] = self.points[2] + offset

            sup_esq_x = old_sup_esq.x() - offset.x()

            inf_esq_x = sup_esq_x
            sup_dir_x = self.points[2].x()

            sup_esq_y = old_sup_esq.y() - offset.y()
            
            sup_dir_y = sup_esq_y
            inf_esq_y = self.points[2].y()

            self.points[0] = QPointF(sup_esq_x, sup_esq_y)
            self.points[1] = QPointF(inf_esq_x, inf_esq_y)
            self.points[3] = QPointF(sup_dir_x, sup_dir_y)
        elif i == 3:
            if offset.x() >= 0 or offset.y() <= 0:
                offset = QPointF(+0.5, -0.5)
            else:
                offset = QPointF(-0.5, +0.5)

            old_sup_esq = self.points[0]
            old_inf_esq = self.points[1]
            old_inf_dir = self.points[2]
            old_sup_dir = self.points[3]

            self.points[3] = self.points[3] + offset

            inf_esq_x = old_inf_esq.x() - offset.x()

            sup_esq_x = inf_esq_x
            inf_dir_x = self.points[3].x()

            inf_esq_y = old_inf_esq.y() - offset.y()
            
            sup_esq_y = self.points[3].y()
            inf_dir_y = inf_esq_y

            self.points[0] = QPointF(sup_esq_x, sup_esq_y)
            self.points[1] = QPointF(inf_esq_x, inf_esq_y)
            self.points[2] = QPointF(inf_dir_x, inf_dir_y)
        
        if ((abs(distance(self.points[0] - self.points[1]) + distance(self.points[1] - self.points[2]) + distance(self.points[2] - self.points[3]) + distance(self.points[3] - self.points[0]) - 4 * distance(self.points[3] - self.points[0])) - 0.1) < 0) == False:
            print "Error: it isn't a square!", (abs(distance(self.points[0] - self.points[1]) + distance(self.points[1] - self.points[2]) + distance(self.points[2] - self.points[3]) + distance(self.points[3] - self.points[0]) - 4 * distance(self.points[3] - self.points[0])) - 0.1)

    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        shape = Shape("Copy of %s" % self.label )
        shape.points= [p for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value

