"""
Copyright (c) 2018 Mike Malinowski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
This is a simple re-pivoting tool which allows you to select an
object you want to animate, and an object you want to animate it
from.

It will map all the motion of the object onto the new pivot object
and allow you to manipulate the object from that pivot. You can then
keep running this to change the pivot as and hwen you need.

By Mike Malinowski
www.twisted.space
"""
import pymel.core as pm

# -- Assume a selection order. The first object is the object
# -- we want to drive, the second object is the object we want
# -- to use as a new pivot point
driven = pm.selected()[0]
driver = pm.selected()[1]

# -- We need to map the motion of the soon-to-be driven
# -- object onto our driver
cns = pm.parentConstraint(
    driven,
    driver,
    maintainOffset=True,
)
pm.bakeResults(
    driver,
    time=[
        pm.playbackOptions(q=True, min=True),
        pm.playbackOptions(q=True, max=True),
    ],
    simulation=True,
)

# -- Now remove the constraint, and ensure there are no
# -- constraints on the soon-to-be driven object
pm.delete(cns)

constraints = list()
for child in driven.getChildren():
    if isinstance(child, pm.nt.Constraint):
        constraints.append(child)

pm.delete(constraints)

# -- Now we can constrain the driven to our new driver and
# -- we should get the same result, but we can manipulate
# -- it from our new space
pm.parentConstraint(
    driver,
    driven,
    maintainOffset=True,
)
