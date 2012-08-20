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

For the first deployment some initialization is required. You can do this with command:

    fab initialize
    
This will create directory structure of the project. Then run command:

    fab deploy -H host -u username
    
For update the Python's virtual environment use option ``update_environment``:

    fab deploy:update_environment=True -H host -u username
    
One can also reload nginx configuration with option ``update_nginx``:

    fab deploy:update_nginx=True -H host -u username
    
Both options are turn off as default.