"""
Copyright (c) 2018 Lee Dunham

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
This allows you to setup and bake automated follow-through behaviour 
on selected transform objects in a Maya scene.
Tested on Maya 2016 SP6.

The script provides 2 separate functions:

    setup_follow_through()
        Setup follow through (jiggle planes) to each selected transform object.
        Jiggle deformers are returned to allow users to animate the deformer attributes
        before baking.
        
    bake_follow_through()
        Bake and clean follow through (jiggle planes) on selected transform objects.

Note:
    This particular script has a current limitation with animation layers. The constraint
    and baking would need to be piped into the appropriate animLayer.


Lee Dunham
ldunham.blogspot.co.uk
"""
import pymel.core as pm


# -- Jiggle deformer default attributes for
# -- convenience (could replace with json...)
JIGGLE_DEFAULTS = {
    'jiggleWeight': 0.8,
    'damping': 0,
    'stiffness': 0.1,
    'forceOnTangent': 0.5,
    'forceAlongNormal': 0.5,
}


def setup_follow_through():
    """
    Setup follow through (jiggle planes) to each selected transform object.
    Jiggle deformers are returned to allow users to animate the deformer attributes
    before baking.
    
    :return: List of jiggle deformers.
    :rtype: list(pm.PyNode)
    """
    # -- Grab the selected transforms
    node_list = pm.selected(type='transform')
    
    # -- Validate node list
    if not node_list:
        pm.warning(
            'Select at least 1 transform object!'
        )
        return None

    # -- Grab the current start and end frames
    start_frame = pm.playbackOptions(q=True, min=True)
    end_frame = pm.playbackOptions(q=True, max=True)

    # -- Iterable variables for later
    to_delete = []
    plane_trans_list = []
    
    # -- For each node
    for node in node_list:
        
        # -- Create a 10x10 poly plane
        plane_trans = pm.polyPlane(
            w=10,
            h=10,
            sx=1,
            sy=1,
        )[0]
        plane_trans_list.append(plane_trans)
        
        # -- Constrain the plane to the give node (delete later)
        to_delete.append(
            pm.parentConstraint(node, plane_trans, mo=False)
        )

    # -- Bake all planes in one go (translate and rotate).
    # -- This is to sever any dependency on the selected transforms, and
    # -- removing any potential cyclic issues.
    pm.bakeResults(
        plane_trans_list,
        time=[
            start_frame,
            end_frame,
        ],
        at=['t', 'r'],
        sm=True,
    )
    
    # -- Delete plane constraints
    pm.delete(to_delete)

    # -- List of jiggle deformers to select & return
    jiggle_list = []
    
    # -- Go to the first frame
    pm.currentTime(start_frame)
    
    # -- Setup and connect each node to plane
    for node, plane_trans in zip(node_list,
                                 plane_trans_list):
        
        # -- Create a jiggle deformer on the plane
        pm.select(plane_trans)
        pm.mel.CreateJiggleDeformer()
        
        # -- Get the plane's shape
        plane_shape = plane_trans.getShape()
        
        # -- Get the Jiggle deformer
        jiggle_deformer = plane_shape.inputs(type='jiggle')[0]
        jiggle_list.append(jiggle_deformer)
        
        # -- Set the default jiggle settings
        for attr, value in JIGGLE_DEFAULTS.iteritems():
            jiggle_deformer.attr(attr).set(value)
        
        # -- Create and setup a follicle on the plane's shape
        follicle = pm.createNode('follicle')

        # -- Get the follicle's transform node (parent)
        follicle_trans = follicle.getParent()
        
        plane_shape.outMesh.connect(follicle.inputMesh)
        plane_shape.worldMatrix[0].connect(follicle.inputWorldMatrix)
        follicle.outRotate.connect(follicle_trans.rotate)
        follicle.outTranslate.connect(follicle_trans.translate)

        # -- Position the follicle in the center of the plane
        follicle.parameterU.set(0.5)
        follicle.parameterV.set(0.5)

        # -- Lock the follicle_trans translate and rotate attributes
        follicle_trans.translate.lock()
        follicle_trans.rotate.lock()
        
        # -- Constrain the original node to the follicle_trans
        constraint = pm.parentConstraint(follicle_trans, node, mo=True)
        
        # -- Connect the plane_trans to a custom attribute
        # -- on the constraint for retrieval (when baking).
        # -- Add it to the constraint as we clean it up
        # -- anyway (no need to dirty the rig).
        constraint.addAttr('ld_jiggle_node', at='message')
        plane_trans.message.connect(constraint.ld_jiggle_node)
        
    # -- Delete animation on the nodes (constrained
    # -- by the planes by now anyway)
    pm.cutKey(node_list, at=['t', 'r'], cl=True)
    
    # -- Select the node list (allows the bake process to run
    # -- immediately after).
    # -- Would recommend selecting the jiggle_list to allow users
    # -- to animate the jiggle deformer instead.
    pm.select(node_list)
    
    return jiggle_list


def bake_follow_through():
    """
    Bake and clean follow through (jiggle planes) on selected transform objects.
    
    :return: None
    """
    # -- Find all selected transforms that have a jiggle setup
    node_list = [
        node
        for node in pm.selected(type='transform')
        if any(pc.hasAttr('ld_jiggle_node')
               for pc in node.getChildren(type='parentConstraint'))
    ]
    
    # -- Validate node list
    if not node_list:
        pm.warning(
            'Select at least 1 jiggled object!'
        )
        return None
    
    plane_trans_list = []
    to_delete = set()
    
    # -- Find connected parent constraints (already validated)
    for node in node_list:
        constraint = [
            pc
            for pc in node.getChildren(type='parentConstraint')
            if pc.hasAttr('ld_jiggle_node')
        ][0]

        # -- Retrieve the plane (transform) from the constraint
        plane_trans = constraint.ld_jiggle_node.get()
        plane_trans_list.append(plane_trans)

        # -- We'll want to delete this during cleanup
        to_delete.add(plane_trans)

        # -- Grab the plane's follicle
        to_delete.update(
            plane_trans.getShape().outputs(type='follicle')
        )
    
    # -- Geo cache the planes to avoid jitter.
    # -- Enable if you get jitter issues - possibly caused
    # -- by V2.0 / playback speed etc.
    # -- As this creates a geometry cache file using current settings, users
    # -- may be prompt to replace existing cache (recommended action).
    # -- HINT: This can be avoided if you investigate the pm.mel.geometryCache() call.
    pm.select(plane_trans_list)
    pm.mel.geometryCache()

    # -- Grab the current start and end frames
    start_frame = pm.playbackOptions(q=True, min=True)
    end_frame = pm.playbackOptions(q=True, max=True)
    
    # -- Bake all transforms
    pm.bakeResults(
        node_list,
        time=[
            start_frame,
            end_frame,
        ],
        at=['t', 'r'],
        sm=True,
    )
    
    # -- Delete setup
    pm.delete(to_delete)

    # -- Select the nodes (it's polite to leave as you entered).
    pm.select(node_list)


if __name__ == '__main__':
    # -- Setup the follow through (allows you to animate the jiggle_weight)
    setup_follow_through()

    # -- Bake and cleanup follow through
    bake_follow_through()
