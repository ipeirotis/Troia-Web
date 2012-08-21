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
    
Deployment
----------

It is convinient to add your ssh public key to authorized_keys on the destination host.

There is a fabric script that does all deployment for you. Just run the following:

    fab deploy -H host -u username
    
For an update the Python's virtual environment use ``update_environment=True`` option:

    fab deploy:update_environment=True -H host -u username

If the server configuration has been changed, one can reload it with ``update_server`` command:

    fab update_server -H host -u username
    
The following command compiles and exposes the ``GetAnotherLabel.war`` file on the website. 

    fab update_war -H host -u username
    
Both ``update_server`` and ``update_war`` commands can be ran after the successful deployment using respectively
``update_server=True`` and ``update_war=True`` options:

    fab deploy:update_war=True -H host -u username
    fab deploy:update_server=True -H host -u username
    fab deploy:update_war=True,update_server=True -H host -u username
        
All options for ``deploy`` command are set to ``False`` as default.