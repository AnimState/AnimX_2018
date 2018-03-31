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
This script will allow you to switch the space in which an object 
moves from the current frame onward. 

Select the object you want to drive, then select the object which
represents the new onward space. The script will ensure the objects
global transform is retained during the switch.

By Mike Malinowski
www.twisted.space
"""
import pymel.core as pm

driven = pm.selected()[0]
driver = pm.selected()[1]

# -- Get the node above the control, which we can constrain
zero_node = driven.getParent()

# -- Store the worldspace transform of the driven
ws_mat4 = driven.getMatrix(worldSpace=True)

# -- Key the object on the previous frame
pm.setKeyframe(
    driven,
    time=pm.currentTime() - 1
)

# -- Look for a constraint, if we have one we need to key
# -- its current state
cns = zero_node.getChildren(type='parentConstraint')

if cns:
    pm.setKeyframe(
        cns[0].getWeightAliasList(),
        time=pm.currentTime() -1,
    )

# -- Now constrain to the new driver
cns = pm.parentConstraint(
    driver,
    zero_node,
    maintainOffset=False,
)

# -- Update the constraint so it is only looking at our
# -- new driver
for idx in range(len(cns.getWeightAliasList())):
    attr = cns.getWeightAliasList()[idx]
    target = cns.getTargetList()[idx]
    
    if target == driver:
        pm.setKeyframe(
            attr,
            time=pm.currentTime() -1,
            value=0,
        )
    attr.set(int(target == driver))
    pm.setKeyframe(attr)

# -- Finally, we restore the worldspace transform of the driven
# -- obect and key it
driven.setMatrix(ws_mat4, worldSpace=True)
pm.setKeyframe(driven)

driven.setMatrix(ws_mat4, worldSpace=True)