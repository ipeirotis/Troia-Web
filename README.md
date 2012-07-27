Troia-Web
=========

This is the docummentation site for the Troia Project. The site is created using hyde - a Python static 
website generator.

Project set up
--------------

Get the latest version of code:

    git clone git://github.com/10clouds/Troia-Web/
    

Go to the project root directory and install required Python packages:
    
    pip install -r requirements.txt
    pip install -r requirements-devel.txt
    
Static content generation
-------------------------

The website can be generated with command:

    hyde -g -s path/to/website/source/ -d path/to/resultant/website/

Or with (for automatic changes detection):

    hyde -kg -s path/to/website/source/ -d path/to/resultant/website/
    
Running
-------

The website can be served locally (using Cherrypy webserver) with command:

    hyde -w -s path/to/website/source/ -d path/to/resultant/website
    
For the deployment on remote machine use fabric commands (``initialize`` for the first deployment and ``deploy`` for each
update of existing website):

    fab initialize
    fab deploy