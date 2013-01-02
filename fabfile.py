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


def preformat(fmt, dct):
    return fmt.format(**dct if dct is not None else {})


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
    cset('virtualenv_root', '{project_root}/virtualenv'.format(**conf))
    cset('scripts_root', '{project_root}/scripts'.format(**conf))
    cset('sql_root', '{project_root}/sql'.format(**conf))
    cset('tomcat_root', '{services_root}/tomcat'.format(**conf))
    cset('maven_root', '{services_root}/maven'.format(**conf))
    cset('hyde_root', '{static_root}/hyde'.format(**conf))
    return conf


def setmode(path, recursive=False, perms=None, owner=None):
    recursive = '--recursive' if recursive else ''
    if perms:
        sudo('chmod {} {} {}'.format(recursive, perms, path))
    if owner:
        sudo('chown {} {} {}'.format(recursive, owner, path))


def cp(src, dst, recursive=False, conf=None):
    run('cp {} {} {}'.format('-r' if recursive else '', preformat(src, conf),
        preformat(dst, conf))


def rm(path, recursive=False, force=False, conf=None):
    run('rm {} {} {}'.format('-r' if recursive else ''. '-f' if force '',
        preformat(path, conf)))


def mv(src, dst, **conf):
    run('mv {} {}'.format(src, dst))


def mkdir(path, parent=False, conf=None):
    path = path.format(**conf)
    run('mkdir {} {}'.format('-p' if parent else '', path))


def chmod(path, mod, recursive=False, conf=None):
    run('chmod {} {} {}'.format('-R' if recursive else '', mod,
        preformat(path, conf)))


def chown(path, own, recursive=False, conf=None):
    run('chown {} {} {}'.format('-R' if recursive else '', own,
        path.format(**conf)))


def lessc(less, css, conf):
    run('{lessc} {} > {}'.format(less, css, **conf))


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


def make_project_tree(conf):
    with (sudo=True):
        mkdir('{project_root}', conf=conf)
        chown('{project_root}', USER)
    mkdir('{project_root}/logs/nginx', conf=conf)
    mkdir('{project_root}/logs/tomcat', conf=conf)
    mkdir('{source_root}', conf=conf)
    mkdir('{hyde_root}', conf=conf)
    mkdir('{downloads_root}', conf=conf)
    mkdir('{apidocs_root}', conf=conf)
    mkdir('{virtualenv_root}', conf=conf)


def make_hyde_tree(conf):
    mkdir('{hyde_root}', conf=conf)
    mkdir('{hyde_root}/media/css', conf=conf)
    mkdir('{hyde_root}/media/downloads', conf=conf)
    mkdif('{hyde_root}/media/img', conf=conf)
    mkdir('{hyde_root}/media/js', conf=conf)
    mkdir('{hyde_root}/media/less', conf=conf)
    mkdir('{hyde_root}/media/txt', conf=conf)


def install_services(conf, force_update=False):
    '''Installs services.'''
    message('Installing services')
    # Remove whole subdirectory.
    if force_update:
        rm('{services_root}', recursive=True, force=True, conf)
    # Check if services exist.
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


def install_requirements(conf, force_update=False):
    '''Makes virtual environment and installs requirements.'''
    message('Installing Python\'s virtual environtment')
    path = conf['virtualenv_root']
    splitted = path.rsplit('/', 1)
    if len(splitted) == 2:
        root = splitted[0]
        name = splitted[1]
    else:
        raise Exception('Invalid path for virtual environment {}'.format(path))
    activate_path = '{}/bin/activate'.format(path)
    activate_cmd = 'source {}'.format(activate_path)
    requirements_path = ('{source_root}/Troia-Web/requirements.txt'
        .format(**conf))
    install_cmd = None
    if exists(path):
        message('Virtual environment exists. Trying to activate')
        run(activate_cmd)
    else:
        message('Virtual environment does not exist. Creating a new one')
        with cd(root):
            run('virtualenv --python={} --no-site-packages {}'
                .format(conf['pyton'], name))
        with prefix('source {}'.format(envpath)):
            run('pip install -r {}'.format(reqpath))


def manage_srv(srv, cmd):
    sudo("{}{} {}".format(SERVICE_PREFIX, srv, cmd))


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
    message('Generating static content')
    # Clear the static subdirectory (without downloads).
    run('rm -rf {}/{{documentation,tutorials}}'.format(dst))
    run('rm -rf {}/media/{{css,img,less,js,txt}}'.format(dst))
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
    raise NotImplementedError("This command is temporary disabled.")
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
def deploy_troia_server(confpath=None):
    """Performs the Troia-Server deployment in the tomcat servlet
    container."""
    conf = readconf(confpath)
    # Ensure project structure.
    make_project_tree(conf=conf)
    # Ensure all services are already installed.
    install_services(conf=conf)
    source_root = '{source_root}/Troia-Server-{troia_server_repo_branch}'.format(**conf)
    # Update Troia-Server repo.
    clone_or_update(src_root, conf['troia_server_repo'],
                    conf['troia_server_repo_branch'])
    maven_cmd = ('{maven_root}/bin/mvn package -Dmaven.test.skip=true'
                    .format(**conf))

    def maven_build():
        '''Builds the Troia-Server's .war file.'''
        with cd(src_root):
            run(maven_cmd)

    # Build the .war file.
    maven_build()
    media_root = '{hyde_root}/media'.format(**conf)
    ensure_tree(media_root, ('downloads'))
    target_path = '{}/troia-server/target/{}.war'.format(src_root, conf['war_name'])
    # Copy this file to the downloads directory.
    cp(target_path, media_root)
    # Replace the properties with custom file.
    upload_template(
        os.path.join(CONF_ROOT, 'troia-server', 'dawidskene.properties'),
        '{}/troia-server/src/main/resources/dawidskene.properties'.format(src_root),
        context=conf)
    # Again build .war file with custom properties.
    maven_build()
    execute(stop_troia_server, confpath=confpath)
    # Clean and copy .war file to the tomcat's webapps directory.
    run('rm -rf {tomcat_root}/webapps/{final_name}*'.format(**conf))
    run('cp {} {tomcat_root}/webapps'.format(target_path, **conf))
    run('mv {tomcat_root}/webapps/{war_name}.war {tomcat_root}/webapps/{final_name}.war'.format(**conf))
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
def deploy_web(update_env=False, confpath=None):
    ''' Synchronizes the website content with the repository.
        Optionally udates Python's virtual environment. '''
    conf = readconf(confpath)
    # Ensure project directory structure.
    make_project_tree(conf)
    # Clear the hyde directory.
    rm('{hyde_root}', recursive=True, force=True, conf=conf)
    # Ensure hyde directory structure.
    make_hyde_tree(conf)
    source_root = '{source_root}/Troia-Web'.format(**conf)
    clone_or_update(source_root, conf)
    install_requirements(update=update_env, conf)
    with prefix('source {virtualenv_root}/bin/activate'.format(**conf)):
        generate(src_root, conf['hyde_root'])
