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

    hyde gen
    
Running
-------

The website can be served locally (using bulti-in hyde webserver) with command:

    hyde serve
    
Deployment
----------

It is convinient to add your ssh public key to ``authorized_keys`` on the destination host.

There is a fabric script that does all deployment for you. Just run the following:

    fab deploy -H host -u username
    
For an update the Python's virtual environment use ``update_environment=True`` option:

    fab deploy:update_environment=True -H host -u username

If the server configuration has been changed, one can reload it with ``update_server`` command:

    fab update_server -H host -u username
    
The following command compiles and exposes the ``GetAnotherLabel.war`` file on the website:

    fab update_troia_server -H host -u username

Another command exists for generating the Troia Java Client API docs:

    fab update_troia_client -H host -u username
    
    
