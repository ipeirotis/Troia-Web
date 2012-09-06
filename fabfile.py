import os
import json

from fabric import colors
from fabric.api import cd, env, execute, prefix, put, run, sudo, task
from fabric.contrib.files import exists, upload_template


THIS_ROOT = os.path.dirname(os.path.abspath(__name__))
CONF_ROOT = os.path.join(THIS_ROOT, "conf")
DEFAULT_PATH = os.path.join(THIS_ROOT, 'default.json')

LESSC = 'lessc'
USER = '{0}:{0}'.format(env.user)

SERVICE_PREFIX = 'service '
SERVICE_PREFIX = '/etc/rc.d/'  # In case of BSD init convention.


def message(msg, *args, **kwargs):
    print colors.cyan('==>', bold=True), msg.format(*args)


def readconf(cpath):
    with open(cpath, 'r') as cfile:
        conf = json.load(cfile)
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
        cset('tomcat_root','{services_root}/tomcat'.format(**conf))
        cset('maven_root','{services_root}/maven'.format(**conf))
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


def maven_build(path, repo, cmd, mvn="mvn"):
    ''' Updates a local repository and builds the maven project. '''
    clone_or_update(path, repo)
    with cd(path):
        run('{} {}'.format(mvn, cmd))


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
    # Ensure the static subdirectory exists.
    run('mkdir -p {}'.format(dst))
    run('hyde -g -s \'{}\' -d \'{}\''.format(src, dst))


@task
def update_server(confpath=DEFAULT_PATH):
    ''' Updates server configuration. '''
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
def start_troia_server(confpath=DEFAULT_PATH):
    conf = readconf(confpath)
    #with prefix("JDK_HOME={jdk_root}".format(**conf)):
    run('{tomcat_root}/bin/catalina.sh start'.format(**conf))


@task
def stop_troia_server(confpath=DEFAULT_PATH):
    conf = readconf(confpath)
    #with prefix("JDK_HOME={jdk_root}".format(**conf)):
    run('{tomcat_root}/bin/catalina.sh stop'.format(**conf))


@task
def restart_troia_server(confpath=DEFAULT_PATH):
    execute(stop_troia_server, confpath=confpath)
    execute(start_troia_server, confpath=confpath)


@task
def deploy_troia_server(confpath=DEFAULT_PATH):
    conf = readconf(confpath)
    # Ensure all services are already installed.
    ensure_srv(conf)
    src = '{source_root}/Troia-Server'.format(**conf)
    #clone_or_update(src, conf['troia_server_repo'])
    target = '{}/target/GetAnotherLabel.war'.format(src)
    #maven_build(src, target, cmd='package -Dmaven.test.skip=true',
    #            mvn='{maven_root}/bin/mvn'.format(**conf))
    upload_template(
        os.path.join(CONF_ROOT, 'troia-server', 'dawidskene.properties'),
        '{tomcat_root}/webapps/GetAnotherLabel/WEB-INF/classes/dawidskene.properties'.format(**conf),
        context=conf)
    media_root = '{hyde_root}/media'.format(**conf)
    ensure_tree(media_root, ('downloads'))
    ensure_tree('{project_root}'.format(**conf), ('scripts', 'sql'))
    upload_template(
        os.path.join(CONF_ROOT, 'db_clear.sh'),
        '{project_root}/scripts'.format(**conf),
        context=conf)
    put(os.path.join(CONF_ROOT, 'db_clear.sql'),
        '{sql_root}'.format(**conf))
    run('cp {} {}/downloads'.format(target, media_root))
    run('cp {} {tomcat_root}/webapps'.format(target, **conf))
    execute(restart_troia_server, confpath=confpath)


@task
def generate_apidocs(confpath=DEFAULT_PATH):
    conf = readconf(confpath)
    src = '{source_root}/Troia-Java-Client'.format(**conf)
    clone_or_update(src, conf['troia_client_repo'])
    target = '{}/target/site/apidocs'.format(src)
    maven_build(src, target, cmd='javadoc:javadoc',
                mvn='{maven_root}/bin/mvn'.format(**conf))
    run('cp -rf {} {static_root}'.format(target, **conf))


@task
def deploy_web(update_env=False, confpath='default.json'):
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
    clone_or_update(src_root, conf['troia_web_repo'], 'mb_troia_server')
    ensure_env(update=update_env, path=conf['virtualenv_root'],
               reqpath='{}/requirements.txt'.format(src_root))
    media_root = '{}/media'.format(src_root)
    css_root = '{}/css'.format(media_root)
    less_root = '{}/less'.format(media_root)
    ensure_tree(media_root, 'css')
    compile(less_root, css_root, ('troia.less', 'bootstrap.less'))
    with prefix('source {virtualenv_root}/bin/activate'.format(**conf)):
        generate(src_root, conf['hyde_root'])
