# PythonOCC version of Quaoar's Workshop [Lesson 15: Export OpenCascade assemblies to STEP](https://www.youtube.com/watch?v=dq2-evewPeA&list=PL_WFkJrQIY2iVVchOPhl77xl432jeNYfQ&index=7)

* This video is one in a series of [Open Cascade Lessons](https://www.youtube.com/playlist?list=PL_WFkJrQIY2iVVchOPhl77xl432jeNYfQ)

* Here is the DFBrowse view of the document produced in this Lesson

![DRAW DFBrowse view of doc](imgs/chassis_doc_top.png)
![DRAW DFBrowse view of doc](imgs/chassis_doc_bot.png)

* Two files are saved:
    * `doc.xml` containing the composed document
    * `chassis.stp` containing the result of conversion of the document to step format

* Both files can be opened in CAD Assistant.

* Notice that the composed document shows the top assembly with the highest value of tag (label entry value = `0:1:1:4`

![doc opened in cad assistant](imgs/doc-cad-assist.png)

* Whereas the step file has the top assembly with the label entry value = `0:1:1:1`

![stp opened in cad assistant](imgs/step-cad-assist.png)

* Apparently, this was needed in order to maintain compliance with the step format requirements.

* Further exploration has shown that using `shape_tool.UpdateAssemblies()` doesn't have any effect on this.

* So far, the only way I have discovered that will cause these label entry values to get reordered is by saving in step format.

* If the step file is then reloaded, the label entry values in the document will be reordered with the root level assembly having the lowest label entry values.

