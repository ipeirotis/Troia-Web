import os
import json
import requests
import time

from fabric import colors
from fabric.api import (cd, env, execute, prefix, run, settings, sudo,
                        runs_once)
from fabric.contrib.files import exists, upload_template
from fabric.tasks import WrappedCallableTask


THIS_ROOT = os.path.dirname(os.path.abspath(__name__))
CONF_ROOT = os.path.join(THIS_ROOT, "conf")
DEFAULT_PATH = os.path.join(THIS_ROOT, 'default.json')


conf = env


class Task(WrappedCallableTask):

    def run(self, *args, **kwargs):
        run('echo `date` {command} {local_user} >> '
            '~/deployment.log'.format(**conf))
        super(Task, self).run(*args, **kwargs)


def task(func):
    return Task(func)


def message(msg, *args, **kwargs):
    print colors.cyan('==>', bold=True), colors.yellow(msg.format(*args))


@runs_once
def readconf(cpath):
    """Reads configuration from given location and sets some auxiliary values.
    Moreover updates global fabric environment with read values."""
    if cpath is None:
        message('Configuration reading skipped')
        return
    message('Reading configuration file from {0}'.format(cpath))
    with open(DEFAULT_PATH, 'r') as cfile:
        conf = json.load(cfile)
    if cpath is not None:
        with open(cpath, 'r') as cfile:
            conf.update(json.load(cfile))
    # For shorter notation.
    cset = conf.setdefault
    # Set some aux values.
    cset('project_root', '{projects_root}/{project_name}'.format(**conf))
    cset('logs_root', '{project_root}/logs'.format(**conf))
    cset('source_root', '{project_root}/source'.format(**conf))
    cset('static_root', '{project_root}/static'.format(**conf))
    cset('services_root', '{project_root}/services'.format(**conf))
    cset('scripts_root', '{project_root}/scripts'.format(**conf))
    cset('sql_root', '{project_root}/sql'.format(**conf))
    cset('virtualenv_root', '{project_root}/virtualenv'.format(**conf))
    # Sources roots.
    cset('troia_web_source', '{source_root}/Troia-Web'.format(**conf))
    cset('troia_server_source', '{source_root}/Troia-Server'.format(**conf))
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


def cp(src, dst, recursive=False, force=False):
    fun = sudo if conf.use_sudo else run
    fun('cp {} {} {} {}'.format(
        '-r' if recursive else '',
        '-f' if force else '',
        src.format(**conf),
        dst.format(**conf)))


def mv(src, dst):
    fun = sudo if conf.use_sudo else run
    fun('mv {} {}'.format(src.format(**conf), dst.format(**conf)))


def rm(path, recursive=False, force=False):
    fun = sudo if conf['use_sudo'] else run
    fun('rm {} {} {}'.format('-r' if recursive else '', '-f' if force else '',
        path.format(**conf)))


def mkdir(path, parent=True):
    fun = sudo if conf['use_sudo'] else run
    fun('mkdir {} {}'.format('-p' if parent else '', path.format(**conf)))


def chmod(path, mod, recursive=False):
    fun = sudo if conf['use_sudo'] else run
    fun('chmod {} {} {}'.format('-R' if recursive else '', mod,
        path.format(**conf)))


def chown(path, own, recursive=False):
    fun = sudo if conf['use_sudo'] else run
    fun('chown {} {} {}'.format('-R' if recursive else '', own,
        path.format(**conf)))


def lessc(less, css):
    run('{lessc} {} > {}'.format(less.format(**conf), css.format(**conf),
        **conf))


def coffee(input, output):
    run("coffee --compile --output {} {}".format(output, input))


def mvn(command):
    run('{maven_root}/bin/mvn {0}'.format(command, **conf))


def clone_or_update(path, repo, branch="master", commit=None):
    """Updates a local repository or clones it."""
    message('Synchronizing with remote repository')
    # Format arguments with global configuration.
    path = path.format(**conf)
    repo = repo.format(**conf)
    branch = branch.format(**conf)
    refspec = 'origin/{0}'.format(branch)
    if exists(path):
        with cd(path):
            run('git fetch origin')
            run('git clean -f')
            run('git reset --hard {0}'.format(refspec))
    else:
        run('git clone {0} {1}'.format(repo, path))
        with cd(path):
            run('git reset --hard {0}'.format(refspec))


def manage_service(service, command):
    if conf.service == 'service':
        form = '{0} {1}'
    else:  # if SERVICE_PREFIX in ('systemctl', 'rc.d'):
        form = '{1} {0}'
        if service in ('cron', 'mysql', 'ssh'):
            service += 'd'
    sudo('{0} {1}'.format(conf.service, form.format(service, command)))


@task
def start_tomcat(confpath=None):
    """Starts the tomcat server."""
    readconf(confpath)
    run('CATALINA_PID={tomcat_root}/temp/catalina.pid '
        '{tomcat_root}/bin/catalina.sh start'.format(**conf), pty=False)


@task
def stop_tomcat(force=False, confpath=None):
    """Stops the tomcat server."""
    readconf(confpath)
    with settings(warn_only=True):
        run('CATALINA_PID={tomcat_root}/temp/catalina.pid '
            '{tomcat_root}/bin/catalina.sh stop {0}'
            .format('force' if force else '', **conf), pty=False)


@task
def restart_tomcat(force_stop=False, confpath=None):
    """Restarts the tomcat server."""
    readconf(confpath)
    execute(stop_tomcat, force=force_stop)
    execute(start_tomcat)


@task
def update_tomcat(confpath=None):
    """Updates tomcat configuration."""
    readconf(confpath)
    # Upload tomcat configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'tomcat', 'server.xml'),
        '{services_root}/tomcat/conf'.format(**conf),
        context=conf)
    execute(restart_tomcat)


@task
def start_mysql(confpath=None):
    readconf(confpath)
    manage_service("mysql", "start")


@task
def stop_mysql(confpath=None):
    readconf(confpath)
    manage_service("mysql", "stop")


@task
def restart_mysql(confpath=None):
    readconf(confpath)
    manage_service("mysql", "restart")


@task
def update_mysql(confpath=None):
    readconf(confpath)
    # Upload mysql configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'mysql', 'my.cnf'),
        '/etc/mysql',
        use_sudo=True,
        context=conf)
    execute(restart_mysql)


@task
def start_nginx(confpath=None):
    readconf(confpath)
    manage_service('nginx', 'start')


@task
def stop_nginx(confpath=None):
    readconf(confpath)
    manage_service('nginx', 'stop')


@task
def restart_nginx(confpath=None):
    readconf(confpath)
    manage_service('nginx', 'restart')


@task
def reload_nginx(confpath=None):
    readconf(confpath)
    manage_service('nginx', 'reload')


@task
def update_nginx(confpath=None):
    readconf(confpath)
    remote_path = ('/etc/nginx/sites-available/{project_domain}'
                   .format(**conf))
    upload_template(
        os.path.join(CONF_ROOT, 'nginx', 'sites-available', 'troia'),
        remote_path,
        use_sudo=True,
        context=conf)
    execute('enable_site', conf.project_domain)


@task
def enable_site(site_name, confpath=None):
    readconf(confpath)
    available_path = '/etc/nginx/sites-available/{0}'.format(site_name)
    enabled_path = '/etc/nginx/sites-enabled/{0}'.format(site_name)
    sudo('ln -fs {} {}'.format(available_path, enabled_path))
    with settings(use_sudo=True):
        chown(available_path, '{0}:{0}'.format(env.user))
        chown(enabled_path, '{0}:{0}'.format(env.user))
    execute(reload_nginx)


@task
def disable_site(site_name, confpath=None):
    readconf(confpath)
    with settings(use_sudo=True):
        rm('/etc/nginx/sites-enabled/{0}'.format(site_name), force=True)
    execute(reload_nginx)


@task
def initialize_project(reinstall_services=False, reinstall_requirements=False,
                       confpath=None):
    """Initializes the project directory structure and installs required
    services and Python packages."""
    readconf(confpath)
    with settings(use_sudo=True):
        mkdir('{project_root}')
        chown('{project_root}', '{0}:{0}'.format(conf.user))
    mkdir('{logs_root}/nginx')
    mkdir('{logs_root}/tomcat')
    mkdir('{scripts_root}')
    mkdir('{source_root}')
    mkdir('{sql_root}')
    mkdir('{static_root}')
    mkdir('{downloads_root}')
    execute('install_services', force_reinstall=reinstall_services)
    execute('install_requirements', force_reinstall=reinstall_requirements)


@task
def install_services(force_reinstall=False, confpath=None):
    """Installs services."""
    readconf(confpath)
    message('Installing services')
    # Remove whole subdirectory.
    if force_reinstall:
        rm('{services_root}', recursive=True, force=True)
    # Check if services exist.
    if not exists('{services_root}'):
        # Create services root directory if does not exist.
        mkdir('{services_root}')
    # Download and install services.
    with cd('/tmp'):
        # Tomcat 7.
        if not exists('{services_root}/tomcat/bin/catalina.sh'.format(**conf)):
            message('Installing apache tomcat')
            if not exists('/tmp/tomcat.tgz'):
                message('Downloading apache tomcat')
                run('wget {tomcat_url} -O tomcat.tgz'.format(**conf))
            run('tar xzf tomcat.tgz')
            rm('{services_root}/tomcat', recursive=True, force=True)
            mv('apache-tomcat-*', '{services_root}/tomcat')
        # Maven 3.
        if not exists('{services_root}/maven/bin/mvn'.format(**conf)):
            message('Installing apache maven')
            if not exists('/tmp/maven.tgz'):
                run('wget {maven_url} -O maven.tgz'.format(**conf))
            run('tar xzf maven.tgz')
            rm('{services_root}/maven', recursive=True, force=True)
            mv('apache-maven-*', '{services_root}/maven')
        # Java Server Faces library.
        if not exists('/tmp/javax.faces.jar'):
            message('Installing Java Server Faces library')
            if not exists('/tmp/javax.faces.jar'):
                message('Downloading Java Server Faces library')
                run('wget {faces_url} -O javax.faces.jar'.format(**conf))
            # TODO not works.
            # mv('javax.faces.jar', '{tomcat_root}/lib')
        # Raven Java.
        if not exists('{services_root}/raven-java'):
            message('Installing Raven Java Server')
            if not exists('/tmp/raven-java'):
                message('Downloading Raven Java')
                run('git clone {raven_url} raven-java'.format(**conf))
                with cd('raven-java'):
                    mvn('clean install')
            mv('raven-java', '{services_root}')
    # Update services configuration.
    execute('update_tomcat')


@task
def install_requirements(force_reinstall=False, confpath=None):
    """Creates virtual environment and installs requirements."""
    message('Installing Python\'s virtual environtment')
    if force_reinstall:
        rm('{virtualenv_root}', recursive=True, force=True)
    activate_path = '{virtualenv_root}/bin/activate'.format(**conf)
    activate_cmd = 'source {0}'.format(activate_path)
    valid = True
    with settings(warn_only=True):
        if not exists(activate_path):
            valid = False
    if not valid:
        message('Virtual environment does not exist or it is broken. '
                'Reinstalling')
        rm('{virtualenv_root}', recursive=True, force=True)
        run('virtualenv --python={python} --no-site-packages '
            '{virtualenv_root}'.format(**conf))
        with prefix(activate_cmd):
            run('pip install -r {troia_web_source}/requirements.txt'
                .format(**conf))
    message('Virtual environment exists. Trying to activate')
    run(activate_cmd)


@task
def deploy_troia_web(confpath=None):
    """Deploys the Troia-Web site (generic)."""
    readconf(confpath)
    # Clear destination directory.
    rm('{static_root}/{troia_web_name}', recursive=True, force=True)
    # Create hyde project structure.
    mkdir('{static_root}/{troia_web_name}')
    clone_or_update('{troia_web_source}', '{troia_web_repo}',
                    '{troia_web_branch}')
    message('Compiling less')
    with cd('{troia_web_source}/content/media/less'.format(**conf)):
        mkdir('../css')
        lessc('bootstrap.less', '../css/bootstrap.css')
        lessc('responsive.less', '../css/responsive.css')
        lessc('troia.less', '../css/troia.css')

    message("Compiling coffee")
    with cd('{troia_web_source}/content/media/coffee'.format(**conf)):
        coffee('.', '../js')

    message('Generating static content')
    with prefix('source {virtualenv_root}/bin/activate'.format(**conf)):
        run('hyde -s \'{troia_web_source}\' gen'
            '     -d \'{static_root}/{troia_web_name}\' '
            '     -c \'{troia_web_source}/production.yaml\''
            .format(**conf))
    cp('{downloads_root}', '{static_root}/{troia_web_name}/media/',
        recursive=True, force=True)
    run('ln -fs {example_datasets_path} {static_root}/{troia_web_name}/media/examples'.format(**conf))
    run('ln -fs {csv_path} {static_root}/{troia_web_name}/media/csv'.format(**conf))


@task
def enable_troia_web(confpath=None):
    readconf(confpath)
    enable_site(conf.project_domain)


@task
def disable_troia_web(confpath=None):
    readconf(confpath)
    disable_site(conf.project_domain)


@task
def deploy_troia_server(confpath=None, blocking=True):
    """Deploys the Troia-Server project (generic)."""
    readconf(confpath)
    clone_or_update('{troia_server_source}', '{troia_server_repo}',
                    '{troia_server_branch}')
    # Send files.
    files = (('sql', 'db_clear.sql'), ('scripts', 'db_clear.sh'))
    for file_tuple in files:
        upload_template(
            os.path.join(CONF_ROOT, *file_tuple),
            '{project_root}/{0}/{1}'.format(*file_tuple, **conf),
            context=conf)
    # Replace the properties with custom file.
    upload_template(
        os.path.join(CONF_ROOT, 'troia-server', 'troia.properties'),
        '{troia_server_source}/service/src/main/resources/troia.properties'.format(**conf),
        context=conf)
    upload_template(
        os.path.join(CONF_ROOT, 'troia-server', 'log4j.properties'),
        '{troia_server_source}/service/src/main/resources/log4j.properties'.format(**conf),
        context=conf)
    # Clean and build the .war file.
    with cd('{troia_server_source}/service'.format(**conf)):
        mvn('clean')
        mvn('package -Dmaven.test.skip=true')
    before = requests.get('http://{project_domain}/api/status'.format(**conf))
    # Deploy the .war file.
    # execute(stop_tomcat)
    rm('{tomcat_root}/webapps/{troia_server_name}.war', recursive=True, force=True)
    cp('{troia_server_source}/service/target/{troia_server_war_name}.war',
        '{tomcat_root}/webapps/{troia_server_name}.war')
    # execute(start_tomcat)
    while blocking:
        after = requests.get('http://{project_domain}/api/status'.format(**conf))
        print before.content
        print after.content
        if not before.ok and after.ok:
            break
        if (before.ok and after.ok and after.json()['status'] == "NOT_INITIALIZED"):
            break
        time.sleep(5)
    requests.post("http://{project_domain}/api/config".format(**conf), data={'IS_FREEZED': 'on'})


@task
def update_troia_server(confpath=None):
    """Updates the Troia-Server configuration (tomcat, mysql)."""
    readconf(confpath)
    execute(update_tomcat)
    execute(update_mysql)


@task
def synchronize_downloads(confpath=None):
    cp('{downloads_root}', '{static_root}/{troia_web_name}/media',
        recursive=True, force=True)


@task
def deploy_troia_server_download(confpath=None):
    readconf(confpath)
    clone_or_update('{troia_server_source}', '{troia_server_repo}',
                    '{troia_server_branch}')
    # Build the .war file.
    with cd('{troia_server_source}/troia-server'.format(**conf)):
        mvn('package -Dmaven.test.skip=true')
    cp('{troia_server_source}/troia-server/target/{troia_server_war_name}.war',
        '{downloads_root}')
    execute(synchronize_downloads)
