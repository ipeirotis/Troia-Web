import os
import json

from fabric import colors
from fabric.api import cd, env, execute, prefix, run, settings, sudo, task
from fabric.contrib.files import exists, upload_template


THIS_ROOT = os.path.dirname(os.path.abspath(__name__))
CONF_ROOT = os.path.join(THIS_ROOT, "conf")
DEFAULT_PATH = os.path.join(THIS_ROOT, 'default.json')

LESSC = 'lessc'
USER = '{0}:{0}'.format(env.user)

SERVICE_PREFIX = 'service '
#SERVICE_PREFIX = '/etc/rc.d/'  # In case of BSD init convention.


def message(msg, *args, **kwargs):
    print colors.cyan('==>', bold=True), msg.format(*args)


def readconf(cpath):
    with open(DEFAULT_PATH, 'r') as cfile:
        conf = json.load(cfile)
    with open(cpath, 'r') as cfile:
        conf.update(json.load(cfile))
        # For shorter notation.
        cset = conf.setdefault
        # Set some aux values.
        cset('project_root', '{projects_root}/{project_name}'.format(**conf))
        cset('source_root', '{project_root}/source'.format(**conf))
        cset('static_root', '{project_root}/static'.format(**conf))
        cset('services_root', '{project_root}/services'.format(**conf))
        cset('virtualenv_root', '{project_root}/virtualenv'.format(**conf))
        cset('scripts_root', '{project_root}/scripts'.format(**conf))
        cset('sql_root', '{project_root}/sql'.format(**conf))
        cset('tomcat_root', '{services_root}/tomcat'.format(**conf))
        cset('maven_root', '{services_root}/maven'.format(**conf))
        cset('hyde_root', '{static_root}/hyde'.format(**conf))
        return conf
    raise Exception('Could not read the configuration file')


def setmode(path, recursive=False, perms=None, owner=None):
    recursive = '--recursive' if recursive else ''
    if perms:
        sudo('chmod {} {} {}'.format(recursive, perms, path))
    if owner:
        sudo('chown {} {} {}'.format(recursive, owner, path))


def ensure_srv(conf):
    ''' Ensures services (maven, tomcat) are installed correctly.
        It takes care only about services that are under ``services``
        directory. '''
    if exists('{services_root}/tomcat/bin/catalina.sh'.format(**conf)) and \
            exists('{services_root}/maven/bin/mvn'.format(**conf)):
        message('Services already installed. Skipping')
        return
    with cd('/tmp'):
        ensure_tree('{project_root}'.format(**conf), 'services')
        if not exists("/tmp/tomcat.tgz"):
            message('Downloading apache tomcat')
            run('wget {tomcat_url} -O tomcat.tgz'.format(**conf))
        message('Installing apache tomcat')
        run('tar xzf tomcat.tgz')
        run('rm -rf tomcat/')
        run('mv apache-tomcat-* tomcat')
        run('cp -rf tomcat {services_root}'.format(**conf))
        if not exists("/tmp/maven.tgz"):
            message('Downloading apache maven')
            run('wget {maven_url} -O maven.tgz'.format(**conf))
        message('Installing apache maven')
        run('tar xzf maven.tgz')
        run('rm -rf maven/')
        run('mv apache-maven-* maven')
        run('cp -rf maven {services_root}'.format(**conf))
    # Upload configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'tomcat', 'server.xml'),
        '{services_root}/tomcat/conf'.format(**conf),
        context=conf)


def manage_srv(srv, cmd):
    sudo("{}{} {}".format(SERVICE_PREFIX, srv, cmd))


def pip_install(envpath, reqpath):
    with prefix('source {}'.format(envpath)):
        run('pip install -r {}'.format(reqpath))


def clone_or_update(path, repo, branch="master"):
    ''' Updates a local repository or clones it. '''
    message('Synchronizing with remote repository')
    refspec = 'origin/{}'.format(branch)
    if exists(path):
        with cd(path):
            run("git fetch origin")
            run("git clean -f")
            run("git reset --hard {}".format(refspec))
    else:
        run('git clone {} {}'.format(repo, path))
        with cd(path):
            run("git reset --hard {}".format(refspec))


def ensure_env(path, update=False, reqpath=None, py='/usr/bin/python2.7'):
    ''' Ensures environment already exists (creates if missing). '''
    message('Checking Python\'s virtual environment')
    splitted = path.rsplit('/', 1)
    if len(splitted) == 2:
        root = splitted[0]
        name = splitted[1]
    else:
        raise Exception('Invalid path for virtual environment {}'.format(path))
    source_path = '{}/bin/activate'.format(path)
    source_cmd = 'source {}'.format(source_path)
    if exists(path):
        message('Virtual environment exists. Trying to activate')
        run(source_cmd)
        if update:
            pip_install(source_path, reqpath)
    else:
        message('Virtual environment does not exist. Creating a new one')
        with cd(root):
            run('virtualenv --python={} --no-site-packages {}'
                .format(py, name))
            pip_install(source_path, reqpath)


def ensure_tree(root, subdirs, use_sudo=False):
    func = sudo if use_sudo else run
    if not isinstance(subdirs, (list, tuple)):
        subdirs = [subdirs]
    message(colors.blue('Preparing directories structure'))
    with cd(root):
        for subdir in subdirs:
            message('Making {}/{}'.format(root, subdir))
            func('mkdir -p {}'.format(subdir))


def compile(input_dir, output_dir, files=[]):
    ''' Compiles less and moves resultant css to another directory for
        further processing using hyde. '''
    message(colors.blue('Compiling less from {} to {}'.format(input_dir,
                        output_dir)))
    message(colors.blue('Files to compile: {}'.format(', '.join(files))))
    with cd(input_dir):
        for file_name in files:
            name, ext = file_name.rsplit('.', 1)
            result_name = '{}.css'.format(name)
            run('{} {} > {}'.format(LESSC, file_name,
                                    os.path.join(output_dir, result_name)))


def generate(src, dst):
    message(colors.blue('Generating static content'))
    # Clear the static subdirectory.
    run('rm -rf {}'.format(dst))
    run('mkdir -p {}'.format(dst))
    # Generate the static content.
    run('hyde -s \'{0}\' gen -d \'{1}\' -c \'{0}/production.yaml\''.format(src, dst))
    media_root = '{}/media'.format(dst)
    less_root = '{}/less'.format(media_root)
    css_root = '{}/css'.format(media_root)
    message(colors.blue('Compiling less files'))
    # Compile less files.
    run('mkdir -p {}'.format(css_root))
    run('{} {}/bootstrap.less > {}/bootstrap.css'.format(LESSC, less_root,
        css_root))
    run('{} {}/responsive.less > {}/responsive.css'.format(LESSC, less_root,
        css_root))
    run('{} {}/troia.less > {}/troia.css'.format(LESSC, less_root, css_root))


@task
def update_server(confpath=None):
    """Reloads web server configuration and restart the server."""
    conf = readconf(confpath)
    apath = '/etc/nginx/sites-available/troia'
    epath = '/etc/nginx/sites-enabled/troia'
    upload_template(
        os.path.join(CONF_ROOT, 'nginx', 'sites-available', 'troia'),
        '/etc/nginx/sites-available/troia',
        use_sudo=True,
        context=conf)
    sudo('ln -fs {} {}'.format(apath, epath))
    setmode(apath, owner=USER)
    setmode(epath, owner=USER)
    ensure_tree(conf['project_root'], ('logs', 'logs/nginx'))
    manage_srv('nginx', 'reload')


@task
def start_troia_server(confpath=None):
    """Starts the troia server (tomcat)."""
    conf = readconf(confpath)
    run('CATALINA_PID={tomcat_root}/temp/catalina.pid '
        '{tomcat_root}/bin/catalina.sh start'.format(**conf), pty=False)


@task
def stop_troia_server(confpath=None):
    """Stops the troia server (tomcat)."""
    conf = readconf(confpath)
    with settings(warn_only=True):
        run('CATALINA_PID={tomcat_root}/temp/catalina.pid '
            '{tomcat_root}/bin/catalina.sh stop -force'.format(**conf),
            pty=False)


@task
def restart_troia_server(confpath=None):
    """Stops and starts the troia server (tomcat)."""
    execute(stop_troia_server, confpath=confpath)
    execute(start_troia_server, confpath=confpath)


@task
def deploy_troia_server(confpath=None):
    """Performs the Troia-Server deployment in the tomcat servlet
    container."""
    conf = readconf(confpath)
    # Ensure all services are already installed.
    ensure_srv(conf)
    src_root = '{source_root}/Troia-Server'.format(**conf)
    # Update Troia-Server repo.
    clone_or_update(src_root, conf['troia_server_repo'],
                    conf['troia_server_branch'])
    maven_cmd = '{maven_root}/bin/mvn package -Dmaven.test.skip=true' \
                .format(**conf)

    def maven_build():
        '''Builds the Troia-Server's .war file.'''
        with cd(src_root):
            run(maven_cmd)

    # Build the .war file.
    maven_build()
    media_root = '{hyde_root}/media'.format(**conf)
    ensure_tree(media_root, ('downloads'))
    target_path = '{}/target/GetAnotherLabel.war'.format(src_root)
    # Copy this file to the downloads directory.
    run('cp {} {}/downloads'.format(target_path, media_root))
    # Replace the properties with custom file.
    upload_template(
        os.path.join(CONF_ROOT, 'troia-server', 'dawidskene.properties'),
        '{}/src/main/resources/dawidskene.properties'.format(src_root),
        context=conf)
    # Again build .war file with custom properties.
    maven_build()
    execute(stop_troia_server, confpath=confpath)
    # Clean and copy .war file to the tomcat's webapps directory.
    run('rm -rf {tomcat_root}/webapps/GetAnotherLabel*'.format(**conf))
    run('cp {} {tomcat_root}/webapps'.format(target_path, **conf))
    execute(start_troia_server, confpath=confpath)


@task
def update_troia_server(confpath=DEFAULT_PATH):
    conf = readconf(confpath)
    # Upload tomcat configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'tomcat', 'server.xml'),
        '{services_root}/tomcat/conf'.format(**conf),
        context=conf)
    # Upload mysql configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'mysql', 'my.cnf'),
        '/etc/mysql',
        use_sudo=True,
        context=conf)
    ensure_tree('{project_root}'.format(**conf), ('scripts', 'sql'))
    # Upload scripts for cleaning database.
    upload_template(
        os.path.join(CONF_ROOT, 'db_clear.sh'),
        '{project_root}/scripts'.format(**conf),
        context=conf)
    upload_template(
        os.path.join(CONF_ROOT, 'db_clear.sql'),
        '{sql_root}'.format(**conf),
        context=conf)
    # Restart mysql server.
    sudo('service mysql restart')
    # Restart troia server.
    execute(restart_troia_server, confpath=confpath)


@task
def generate_apidocs(confpath=DEFAULT_PATH):
    conf = readconf(confpath)
    src_root = '{source_root}/Troia-Java-Client'.format(**conf)
    clone_or_update(src_root, conf['troia_client_repo'],
                    conf['troia_client_branch'])
    target_path = '{}/target/site/apidocs'.format(src_root)
    with cd(src_root):
        run('{maven_root}/bin/mvn javadoc:javadoc'
            .format(**conf))
    run('rm -rf {static_root}/apidocs'.format(**conf))
    run('cp -rf {} {static_root}'.format(target_path, **conf))


@task
def deploy_web(update_env=False, confpath=DEFAULT_PATH):
    ''' Synchronizes the website content with the repository.
        Optionally udates Python's virtual environment. '''
    conf = readconf(confpath)
    root = conf['project_root']
    if not exists(root):
        message(colors.yellow('Initializing project structure'))
        ensure_tree(conf['projects_root'], root, use_sudo=True)
        ensure_tree(root, ['source'], use_sudo=True)
        setmode(root, recursive=True, owner=USER)
    # Project root alredy exists. Current remote user is assummed to be an
    # onwer of the directory.
    src_root = '{source_root}/Troia-Web'.format(**conf)
    clone_or_update(src_root, conf['troia_web_repo'],
                    branch=conf['troia_web_repo_branch'])
    ensure_env(update=update_env, path=conf['virtualenv_root'],
               reqpath='{}/requirements.txt'.format(src_root))
    with prefix('source {virtualenv_root}/bin/activate'.format(**conf)):
        generate(src_root, conf['hyde_root'])
