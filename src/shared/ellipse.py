"""Creates an Ellipse from two given radius
as a special case of a :class:`~psychopy.visual.Polygon`
"""

from __future__ import absolute_import, print_function

import psychopy  # so we can get the __path__

from psychopy.visual.polygon import Polygon
from psychopy.tools.attributetools import attributeSetter, setAttribute

import numpy


class Ellipse(Polygon):
    """Creates a Circle with a given radius as a special case of a
    :class:`~psychopy.visual.ShapeStim`
    (New in version 1.72.00)
    """

    def __init__(self, win, radius=0.5, radius2=0.5, edges=32, **kwargs):
        """
        Circle accepts all input parameters that
        `~psychopy.visual.ShapeStim` accept,
        except for vertices and closeShape.
        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove("self")
        # kwargs isn't a parameter, but a list of params
        self._initParams.remove("kwargs")
        self._initParams.extend(kwargs)

        # initialise parent class
        kwargs["edges"] = edges
        kwargs["radius"] = radius
        self.__dict__["radius2"] = numpy.asarray(radius2)
        super(Ellipse, self).__init__(win, **kwargs)

    @attributeSetter
    def radius2(self, radius2):
        """float, int, tuple, list or 2x1 array
        Radius of the Polygon (distance from the center to the corners).
        May be a -2tuple or list to stretch the polygon asymmetrically.
        :ref:`Operations <attrib-operations>` supported.
        Usually there's a setAttribute(value, log=False) method for each
        attribute. Use this if you want to disable logging.
        """
        self.__dict__["radius2"] = numpy.array(radius2)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def _calcVertices(self):
        d = numpy.pi * 2 / self.edges
        self.vertices = numpy.asarray(
            [
                numpy.asarray(
                    (numpy.sin(e * d) * self.radius, numpy.cos(e * d) * self.radius2)
                )
                for e in range(int(round(self.edges)))
            ]
        )
