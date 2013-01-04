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
# SERVICE_PREFIX = '/etc/rc.d/'  # In case of BSD init convention.

conf = env


def message(msg, *args, **kwargs):
    print colors.cyan('==>', bold=True), msg.format(*args)


def readconf(cpath):
    with open(DEFAULT_PATH, 'r') as cfile:
        conf = json.load(cfile)
    if cpath is not None:
        with open(cpath, 'r') as cfile:
            conf.update(json.load(cfile))
    # For shorter notation.
    cset = conf.setdefault
    # Set some aux values.
    cset('project_root', '{projects_root}/{project_name}'.format(**conf))
    cset('source_root', '{project_root}/source'.format(**conf))
    cset('static_root', '{project_root}/static'.format(**conf))
    cset('services_root', '{project_root}/services'.format(**conf))
    cset('scripts_root', '{project_root}/scripts'.format(**conf))
    cset('sql_root', '{project_root}/sql'.format(**conf))
    cset('virtualenv_root', '{project_root}/virtualenv'.format(**conf))
    # Sources roots.
    cset('troia_web_root', '{source_root}/Troia-Web'.format(**conf))
    cset('troia_server_root', '{source_root}/Troia-Server'.format(**conf))
    cset('troia_java_client_root', '{source_root}/Troia-Java-Client'.format(**conf))
    # Static roots.
    cset('apidocs_root', '{static_root}/apidocs'.format(**conf))
    cset('downloads_root', '{static_root}/downloads'.format(**conf))
    cset('hyde_root', '{static_root}/hyde'.format(**conf))
    # Services roots.
    cset('tomcat_root', '{services_root}/tomcat'.format(**conf))
    cset('maven_root', '{services_root}/maven'.format(**conf))
    cset('use_sudo', False)
    env.update(conf)
    return env


def cp(src, dst, recursive=False):
    func = sudo if conf.use_sudo else run
    func('cp {} {} {}'.format('-r' if recursive else '', src.format(**conf),
        dst.format(**conf)))


def mv(src, dst):
    func = sudo if conf.use_sudo else run
    func('mv {} {}'.format(src.format(**conf), dst.format(**conf)))


def rm(path, recursive=False, force=False):
    func = sudo if conf['use_sudo'] else run
    func('rm {} {} {}'.format('-r' if recursive else '', '-f' if force else '',
        path.format(**conf)))


def mkdir(path, parent=True):
    func = sudo if conf['use_sudo'] else run
    func('mkdir {} {}'.format('-p' if parent else '', path.format(**conf)))


def chmod(path, mod, recursive=False):
    func = sudo if conf['use_sudo'] else run
    func('chmod {} {} {}'.format('-R' if recursive else '', mod,
        path.format(**conf)))


def chown(path, own, recursive=False):
    func = sudo if conf['use_sudo'] else run
    func('chown {} {} {}'.format('-R' if recursive else '', own,
        path.format(**conf)))


def lessc(less, css):
    run('{lessc} {} > {}'.format(less.format(**conf), css.format(**conf),
        **conf))


def lessc_wrapper(name):
    lessc('{troia_web_root}/content/media/less/{}.less'.format(name, **conf),
        '{hyde_root}/media/css/{}.css'.format(name, **conf))


def clone_or_update(path, repo, branch="master", commit=None):
    '''Updates a local repository or clones it.'''
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


def make_project_tree():
    with settings(use_sudo=True):
        mkdir('{project_root}')
        chown('{project_root}', '{0}:{0}'.format(conf.user, **conf))
    mkdir('{project_root}/logs/nginx')
    mkdir('{project_root}/logs/tomcat')
    mkdir('{source_root}')
    mkdir('{hyde_root}')
    mkdir('{downloads_root}')
    mkdir('{apidocs_root}')


def make_hyde_tree():
    mkdir('{hyde_root}')
    mkdir('{hyde_root}/media/css')
    mkdir('{hyde_root}/media/downloads')
    mkdir('{hyde_root}/media/img')
    mkdir('{hyde_root}/media/js')
    mkdir('{hyde_root}/media/less')
    mkdir('{hyde_root}/media/txt')


def install_services(force_update=False):
    '''Installs services.'''
    message('Installing services')
    # Remove whole subdirectory.
    if force_update:
        rm('{services_root}', recursive=True, force=True)
    # Check if services exist.
    elif (exists('{services_root}/tomcat/bin/catalina.sh'.format(**conf)) and
            exists('{services_root}/maven/bin/mvn'.format(**conf))):
        message('Services already installed. Skipping')
        return
    # Create services root directory if does not exist.
    mkdir('{services_root}')
    with cd('/tmp'):
        if not exists("/tmp/tomcat.tgz"):
            message('Downloading apache tomcat')
            run('wget {tomcat_url} -O tomcat.tgz'.format(**conf))
        message('Installing apache tomcat')
        run('tar xzf tomcat.tgz')
        rm('{services_root}/tomcat', recursive=True, force=True)
        mv('apache-tomcat-*', '{services_root}/tomcat')
        if not exists("/tmp/maven.tgz"):
            message('Downloading apache maven')
            run('wget {maven_url} -O maven.tgz'.format(**conf))
        message('Installing apache maven')
        run('tar xzf maven.tgz')
        rm('{services_root}/maven', recursive=True, force=True)
        run('rm -rf maven/')
        mv('apache-maven-*', '{services_root}/maven')
    # Upload configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'tomcat', 'server.xml'),
        '{services_root}/tomcat/conf'.format(**conf),
        context=conf)


def install_requirements(force_update=False):
    '''Makes virtual environment and installs requirements.'''
    message('Installing Python\'s virtual environtment')
    if force_update:
        rm('{virtualenv_root}', recursive=True, force=True)
    activate_path = '{virtualenv_root}/bin/activate'.format(**conf)
    activate_cmd = 'source {}'.format(activate_path)
    install_cmd = None
    valid = True
    with settings(warn_only=True):
        if not exists(activate_path):
            valid = False
    if not valid:
        message('Virtual environment does not exist or it is broken. '
            'Reinstalling')
        return
        rm('{virtualenv_root}', recursive=True, force=True)
        run('virtualenv --python={python} --no-site-packages '
            '{virtualenv_root}'.format(**conf))
        with prefix(activate_cmd):
            run('pip install -r {troia_web_root}/requirements.txt'
                .format(**conf))
    message('Virtual environment exists. Trying to activate')
    run(activate_cmd)


def manage_srv(srv, cmd):
    sudo("{}{} {}".format(SERVICE_PREFIX, srv, cmd))


@task
def update_nginx_config(confpath=None):
    """Updates nginx configuration and restarts the server."""
    readconf(confpath)
    name = '{project_name}'.format(**conf)
    available_path = '/etc/nginx/sites-available/{}'.format(name)
    enabled_path = '/etc/nginx/sites-enabled/{}'.format(name)
    upload_template(
        os.path.join(CONF_ROOT, 'nginx', 'sites-available', name),
        '/etc/nginx/sites-available/{}'.format(name),
        use_sudo=True,
        context=conf)
    sudo('ln -fs {} {}'.format(available_path, enabled_path))
    with settings(use_sudo=True):
        chown(available_path, '{0}:{0}'.format(env.user))
        chown(enabled_path, '{0}:{0}'.format(env.user))
    make_project_tree()
    manage_service('nginx', 'reload')


@task
def start_troia_server(confpath=None):
    """Starts the troia server (tomcat)."""
    conf = readconf(confpath)
    run('CATALINA_PID={tomcat_root}/temp/catalina.pid '
        '{tomcat_root}/bin/catalina.sh start'.format(**conf), pty=False)


@task
def stop_troia_server(confpath=None, force=False):
    """Stops the troia server (tomcat)."""
    conf = readconf(confpath).copy()
    conf['force'] = force
    with settings(warn_only=True):
        cmd = ('CATALINA_PID={tomcat_root}/temp/catalina.pid '
                '{tomcat_root}/bin/catalina.sh stop {force}'.format(**conf))
        run(cmd, pty=False)


@task
def restart_troia_server(confpath=None):
    """Stops and starts the troia server (tomcat)."""
    execute(stop_troia_server, confpath=confpath)
    execute(start_troia_server, confpath=confpath)


@task
def deploy_troia_server_download(confpath=None):
    readconf(confpath)
    # Ensure project structure.
    make_project_tree()
    # Ensure all services are properly installed.
    install_services()
    source_root = '{source_root}/Troia-Server'.format(**conf)
    clone_or_update(source_root, conf['troia_server_repo'],
        branch=conf['troia_server_repo_branch'])
    # Build Troia-Server.war file.
    with cd(source_root):
        run('{maven_root}/bin/mvn package -Dmaven.test.skip=true'.format(**conf))
    cp('{troia_server_root}/target/{troia_server_war_name}.war',
        '{hyde_root}/media/downloads/{final_name}.war')


@task
def deploy_troia_server(confpath=None):
    """Performs the Troia-Server deployment to the tomcat."""
    readconf(confpath)
    # Ensure project structure.
    make_project_tree()
    # Ensure all services are properly installed.
    install_services()
    source_root = '{source_root}/Troia-Server'.format(**conf)
    clone_or_update(source_root, conf['troia_server_repo'],
        branch=conf['troia_server_repo_branch'])
    # Replace the properties with custom file.
    upload_template(
        os.path.join(CONF_ROOT, 'troia-server', 'dawidskene.properties'),
        '{troia_server_root}/troia-server/src/main/resources/'
        'dawidskene.properties'.format(**conf),
        context=conf)
    # Build Troia-Server.war file.
    with cd(source_root):
        run('{maven_root}/bin/mvn package -Dmaven.test.skip=true'.format(**conf))
    # Deploy Troia-Server to the tomcat.
    execute(stop_troia_server, confpath=confpath)
    # Clean and copy .war file to the tomcat webapps directory.
    rm('{tomcat_root}/webapps/{troia_server_final_name}*', recursive=True,
        force=True)
    cp('{troia_server_root}/target/{troia_server_war_name}.war',
        '{tomcat_root}/webapps/{final_name}.war')
    execute(start_troia_server, confpath=confpath)


@task
def update_troia_server(confpath=None):
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
def generate_apidocs(confpath=None):
    readconf(confpath)
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
def deploy_troia_web(confpath=None):
    '''Synchronizes the website content with the repository.'''
    readconf(confpath)
    # Ensure project has valid directory structure.
    make_project_tree()
    # Clear the hyde directory.
    rm('{hyde_root}', recursive=True, force=True)
    # Ensure hyde directory structure.
    make_hyde_tree()
    source_root = '{source_root}/Troia-Web'.format(**conf)
    clone_or_update(source_root, conf['troia_web_repo'],
        branch=conf['troia_web_repo_branch'])
    message('Compiling less')
    lessc_wrapper('bootstrap')
    lessc_wrapper('responsive')
    lessc_wrapper('troia')
    # Ensure python virtual environment is properly configured.
    install_requirements(force_update=False)
    with prefix('source {virtualenv_root}/bin/activate'.format(**conf)):
        message('Generating static content')
        run('hyde -s \'{0}\' gen -d \'{1}\' -c \'{0}/production.yaml\''
            .format(conf.troia_web_root, conf.hyde_root))
    cp('{static_root}/downloads', '{hyde_root}/media/', recursive=True)
