# Lesson15_under_top

## Third in a series of OpenCascade C++ examples

* This example loads a step file `as1-oc-214.stp` as a component of a top level `root` assembly.

* It was first written in Python.
* It produces 2 files:
    * `under-top.xml` which contains the document resulting from loading the file under a root level assembly
    * `under-top.stp` which is a result of transferring the document to the step writer then writing the step file.

* Below are the results of loading each of those file in CAD ASSistant.

![doc file in CAD Assistant](imgs/doc-under-top-ca.png)
![stp file in CAD Assistant](imgs/stp-under-top-ca.png)

* Clearly, the document isn't right. It's not complete and it's not enough for CAD Assistant to render it.
* However, Open Cascade is able to generate what seems to be a correct STEP file.
* One way to repair the document would be to go through a save/load cycle:
    * Save the doc to a temporary step file
    * Reload the step file and replace the defective document with the newly generated one.
* My suspicion is that there is an error in the way my code works.
* I believe the OpenCascade C++ communitiy is larger and more active than the PyOCC community, so I may be more likely to discover the problem if I post the question to a C++ forum.
* The equivalent C++ code, included here for reference, produces pretty much the same results.

## Resolved problem causing name errors in saved step file

* I discovered how to avoid the name errors in the step file
    * See file `load_step_under_top_fixed.py`
    * Note 2 name errors (2nd and 4th lines) that don't occur and thus don't need to be fixed.
* However, there is no improvement in the .xml file...

![step file in CAD Assistant](imgs/stp-under-top-fixed-ca.png)
![doc file in CAD Assistant](imgs/doc-under-top-fixed-ca.png)

