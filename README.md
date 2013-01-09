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

It is convinient to add your ssh public key to ``authorized_keys`` on the
destination host.

You also have to prepare a configuration json based on the ``defaults.json``.
    
The fabric script does all deployment work for you. It performs several
different tasks.

# Initialize project

For the first time you have to initialize project structure. It can be done by running the following:

    fab initialize_project:confpath=path/to/conf.json -H host -u username

# Deployment of the Troia web site

Just run the following:

    fab deploy_troia_web:confpath=path/to/conf.json -H host -u username

# Deployment of the Troia-Server

One can deploy Troia-Server .war file in the tomcat servlet container using the
following command:

    fab deploy_troia_server:confpath=path/to/conf.json -H host -u username

# Reloading the Troia-Server configuration

If the Troia-Server configuration has been changed, one can reload it with
the following command:

    fab update_troia_server:confpath=path/to/conf.json -H host -u username

# Reloading the web server configuration

The Nginx configuration can be updated with:

    fab update_nginx:confpath=path/to/conf.json -H host -u username
