===========
Troia Basics
===========

What is Troia
------------
Troia acronym stands for "Dawid Skene as Service" and this is exactly what it is.
To be more precise it's web service that provides labeling based on algorithm first
described by Dawid and Skene hence it's name.

Why use it
----------
Troia provides high quality labeling service in environment with noisy 
labels. This means that unlike naive approaches it does not assume that
all workers are equal. That is very important if you are getting workers
from services like MTurk as there is now way to assure their level of quality.
This algorithm makes incompetent or malicious workers less of a problem then 
they where before. Another interesting feature is misclassification cost
that allows you to to assign higher cost to some mistakes then to others,
to read more about this read latter part of this tutorial dedicated to 
this topic.

Terminology
-----------

 - Object : object to with category will be assigned
 - Category : Predefined unique category that can be assigned to object
 - Worker : person that assigns category to object
 - Label : triplet that contains object name, category assign to it and name of worker that made this assignment
 - Gold label : object with correct category assigned, can be used to test workers
 - Misclassification cost : cost of incorrect class assignment  
 - Request : set of objects, classes, labels, workers and gold labels
 - Troia data model : same as request


Basic usage
-----------
For most simple use of Troia service you have to create a request with unique ID and then
populate this request with objects and categories. For best quality of results
you also should add some gold labels if possible. After that you can use some other service (like MTurk)
to create labels and then add those labels to request. With all this data in request you can call 
execution of Dawid-Skene algorithm that will traverse data few times analyzing workers reliability
and assigning classes to object. Finally you can request result either as pairs of object-class or
as a class probability maps for each object. 


Misclassification cost
----------------------
In previous example we assumed that misclassification cost is same for each class, this means
that value of those costs will be 0 for correct classification and 1 for wrong. While this
simple approach is very often correct one and there is no reason to complicate model, sometimes
is crucial to have different costs for different classification errors. To compare two examples :
if classification aim is to separate black chairs from blue ones there is not much diffrence between
errors. If we put black chair among blue ones consequences will be same as if we would put blue one among
black ones. However if classification aim is to determine if mushroom is poisonous or not situation is
radically different. Classifying non-poisonous one as poisonous will only mean that we picked up one mushroom less
than we could but classifying poisonous as harmless will result in our death. For classifications like that 
Troia provides misclassification cost maps in with you can set different values of costs.
For mushroom example it would look like that 

 - poisonous->poisonous = 0
 - harmless->harmless = 0
 - poisonous->harmless = 1
 - harmless->poisonous = 5

Thanks to that algorithm will assign harmless label to object only if there is strong bias towards that.

How to actually use Troia
------------------------
For tutorial on how to implement Troia in your project you should 
read tutorial for either Java or Python client or, if you don't want
to use neither of those languages, on raw access to Troia.
If you want to set up your own Troia server you should read DSaS installation tutorial.  
