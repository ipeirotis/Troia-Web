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

if 'ctx' not in env:
    env['ctx'] = {}
ctx = env['ctx']


def message(msg, *args, **kwargs):
    print colors.cyan('==>', bold=True), msg.format(*args)


def readctx(ctxpath=None):
    if len(env['ctx']) > 0:
        message('Context is already loaded. Skipping')
    ctx = dfl = {}
    with open(DEFAULT_PATH, 'r') as dfile:
        # Read the default context.
        dfl = json.load(dfile)
        # For shorter notation.
        setd = dfl.setdefault
        # Set some aux default values.
        setd('project_root', '{projects_root}/{project_name}'.format(**dfl))
        setd('source_root', '{project_root}/source'.format(**dfl))
        setd('static_root', '{project_root}/static'.format(**dfl))
        setd('services_root', '{project_root}/services'.format(**dfl))
        setd('virtualenv_root', '{project_root}/virtualenv'.format(**dfl))
        setd('scripts_root', '{project_root}/scripts'.format(**dfl))
        setd('sql_root', '{project_root}/sql'.format(**dfl))
        setd('tomcat_root','{services_root}/tomcat'.format(**dfl))
        setd('maven_root','{services_root}/maven'.format(**dfl))
        setd('hyde_root', '{static_root}/hyde'.format(**dfl))
        setd('catalina', '{tomcat_root}/bin/catalina.sh'.format(**dfl))
        setd('mvn', '{maven_root}/bin/mvn'.format(**dfl))
        setd('python', '/usr/bin/python2'),
        setd('service_prefix', 'service ')
        setd('requirements_path', '{virtualenv_root}/requirements.txt'
                                  .format(**dfl))
        setd('virtualenv_source', '{virtualenv_root}/bin/activate'
                                  .format(**ctx)),
    env['ctx'].update(dfl)
    if ctxpath is not None:
        with open(ctxpath, 'r') as cfile:
            # Read an user defined context.
            ctx = json.load(cfile)
        env['ctx'].update(ctx)


def setmode(path, recursive=False, perms=None, owner=None):
    recursive = '--recursive' if recursive else ''
    if perms:
        sudo('chmod {} {} {}'.format(recursive, perms, path))
    if owner:
        sudo('chown {} {} {}'.format(recursive, owner, path))


def mkdir(path, use_sudo=False, parent=True):
    cmd = 'mkdir {} {}'.format('-p' if parent else '', path)
    (sudo if use_sudo else run)(cmd)


def manage_srv(srv, cmd):
    sudo("{service_prefix}{} {}".format(srv, cmd, **ctx))


def pip_install():
    message(colors.blue('Installing packages from {requirements_path} file'),
            **ctx)
    with prefix('source {virtualenv_source}'.format(**ctx)):
        run('pip install -r {requirements_path}'.format(**ctx))


def synchronize(path, repo, branch="master"):
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


def ensure_env(update=False):
    ''' Ensures environment already exists (creates if missing). '''
    message('Checking Python\'s virtual environment')
    if exists(ctx['virtualenv_source']):
        message('Virtual environment exists. Trying to activate')
        run('source {virtualenv_source}'.format(**ctx))
        if update:
            pip_install()
    else:
        message('Virtual environment does not exist. Creating the new one')
        run('virtualenv --python={python} {virtualenv_root}'
            .format(**ctx))
        pip_install()


def ensure_tree():
    project_root = ctx['project_root']
    if not exists(project_root):
        mkdir(project_root, use_sudo=True)
        setmode(project_root, recursive=True, owner=USER)
    paths = ['{source_root}', '{static_root}', '{services_root}',
             '{scripts_root}', '{sql_root}', '{logs_root}',
             '{virtualenv_root}', '{source_root}/Troia-Web',
             '{source_root}/Troia-Server', '{source_root}/Troia-Java-Client',
             '{logs_root}/nginx', '{services_root}/nginx',
             '{hyde_root}', '{hyde_root}/media',
             '{hyde_root}/media/downloads']
    paths = (map(lambda p: p.format(**ctx), paths))
    for path in paths:
        mkdir(path)


def ensure_srv():
    ''' Ensures services (maven, tomcat) are installed correctly.
        It takes care only about services that are under ``services``
        directory. '''
    if exists('{services_root}/tomcat/bin/catalina.sh'.format(**ctx)) and \
       exists('{services_root}/maven/bin/mvn'.format(**ctx)):
        message('Services already installed. Skipping')
        return
    with cd('/tmp'):
        ensure_tree('{project_root}'.format(**ctx), 'services')
        if not exists("/tmp/tomcat.tgz"):
            message('Downloading apache tomcat')
            run('wget {tomcat_url} -O tomcat.tgz'.format(**ctx))
        message('Installing apache tomcat')
        run('tar xzf tomcat.tgz')
        run('rm -rf tomcat/')
        run('mv apache-tomcat-* tomcat')
        run('cp -rf tomcat {services_root}'.format(**ctx))
        if not exists("/tmp/maven.tgz"):
            message('Downloading apache maven')
            run('wget {maven_url} -O maven.tgz'.format(**ctx))
        message('Installing apache maven')
        run('tar xzf maven.tgz')
        run('rm -rf maven/')
        run('mv apache-maven-* maven')
        run('cp -rf maven {services_root}'.format(**ctx))
    # Upload configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'tomcat', 'server.xml'),
        '{services_root}/tomcat/conf'.format(**ctx),
        context=ctx)


def maven_build(path, repo, cmd):
    ''' Updates the local repository and builds the maven project. '''
    synchronize(path, repo)
    with cd(path):
        run('{mvn} {}'.format(cmd, **ctx))


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


@task
def update_global(ctxpath=None):
    ''' Updates the configuration of the global (sytem) services (including
        cron and nginx). '''
    readctx(ctxpath)
    message(colors.red('Updating the nginx configuration'))
    apath = '/etc/nginx/sites-available/troia'
    epath = '/etc/nginx/sites-enabled/troia'
    # Upload the server configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'nginx', 'sites-available', 'troia'),
        '/etc/nginx/sites-available/troia',
        use_sudo=True,
        context=ctx)
    sudo('ln -fs {} {}'.format(apath, epath))
    setmode(apath, owner=USER)
    setmode(epath, owner=USER)
    manage_srv('nginx', 'reload')
    message(colors.red('Updating the cron configuration'))
    # Upload the crontab file.
    upload_template(
        os.path.join(CONF_ROOT, 'cron', 'troia'),
        '/etc/cron.d/troia',
        use_sudo=True,
        context=ctx)
    manage_srv('cron', 'reload')


@task
def start_troia_server(ctxpath=DEFAULT_PATH):
    conf = readctx(ctxpath)
    with prefix("JDK_HOME={jdk_root}".format(**conf)):
        run('{tomcat_root}/bin/catalina.sh start'.format(**conf))


@task
def stop_troia_server(ctxpath=DEFAULT_PATH):
    conf = readctx(ctxpath)
    with prefix("JDK_HOME={jdk_root}".format(**conf)):
        run('{tomcat_root}/bin/catalina.sh stop'.format(**conf))


@task
def restart_troia_server(ctxpath=DEFAULT_PATH):
    execute(stop_troia_server, ctxpath=ctxpath)
    execute(start_troia_server, ctxpath=ctxpath)


@task
def build_troia_server(ctxpath=None, upload_conf=False):
    ''' Build the Troia-Server .war file. Optionally use custom
        database properties file. This cannot be used when exposing
        the .war file on the website. '''
    readctx(ctxpath)
    ensure_tree()
    ensure_srv()
    src_root = '{source_root}/Troia-Server'.format(**ctx)
    if upload_conf:
        upload_template(
            os.path.join(CONF_ROOT, 'troia-server', 'dawidskene.properties'),
            '{}/src/main/resources/dawidskene.properties'.format(**ctx),
            context=ctx)
    maven_build(src_root, ctx['troia_server_repo'],
                'package -Dmaven.test.skip=true')


@task
def deploy_troia_server(ctxpath=None):
    message(colors.blue('Deploying the Troia-Server'))
    execute(build_troia_server, ctxpath=ctxpath, upload_conf=True)
    path = '{source_root}/Troia-Server/target/GetAnotherLabel.war' \
           .format(**ctx)
    execute(stop_troia_server, ctxpath=ctxpath)
    run('cp {} {tomcat_root}/webapps'.format(path, **ctx))
    execute(start_troia_server, ctxpath=ctxpath)
    message(colors.blue('Uploading scripts'))
    upload_template(
            os.path.join(CONF_ROOT, 'db_clear.sh'),
            ctx['scripts_root'],
            context=ctx)
    upload_template(
            os.path.join(CONF_ROOT, 'db_clear.sql'),
            ctx['sql_root'],
            context=ctx)


@task
def expose_troia_server(ctxpath=None):
    ''' Exposes the Troia-Server .war on the website. '''
    execute(build_troia_server, ctxpath=ctxpath, upload_conf=False)
    path = '{source_root}/Troia-Server/target/GetAnotherLabel.war' \
           .format(**ctx)
    run('cp {} {hyde_root}/media/downloads'.format(path, **ctx))


@task
def update_troia_server(ctxpath=None):
    ''' Updates the configuration of the Troia-Server. '''
    readctx(ctxpath)
    ensure_tree()
    ensure_srv()
    src_root = '{source_root}/Troia-Server'.format(**ctx)
    synchronize(src_root, ctx['troia_server_repo'])
    # Upload the tomcat configuration file.
    upload_template(
        os.path.join(CONF_ROOT, 'tomcat', 'server.xml'),
        '{services_root}/tomcat/conf'.format(**ctx),
        context=ctx)
    # Also the proxy server has to be updated.
    execute(update_global, ctxpath=ctxpath)
    upload_template(
        os.path.join(CONF_ROOT, 'db_clear.sh'),
        '{project_root}/scripts'.format(**ctx),
        context=ctx)
    put(os.path.join(CONF_ROOT, 'db_clear.sql'),
        '{sql_root}'.format(**ctx))
    run('cp {} {}/downloads'.format(target, media_root))
    execute(restart_troia_server, ctxpath=ctxpath)


@task
def deploy_apidocs(ctxpath=DEFAULT_PATH):
    readctx(ctxpath)
    ensure_tree()
    src_root = '{source_root}/Troia-Java-Client'.format(**ctx)
    maven_build(src_root, ctx['troia_client_repo'], cmd='javadoc:javadoc')
    run('cp -rf {}/target/apidoc {static_root}'.format(src_root, **ctx))


@task
def deploy_troia_web(update_env=False, ctxpath=None):
    ''' Synchronizes the website content with the repository.
        Optionally udates Python's virtual environment. '''
    readctx(ctxpath)
    ensure_tree()
    # Project root alredy exists. Current remote user is assummed to be an
    # onwer of the directory.
    src_root = '{source_root}/Troia-Web'.format(**ctx)
    synchronize(src_root, ctx['troia_web_repo'], branch='mb_troia_server')
    run('cp -f {} {virtualenv_root}'.format(src_root, **ctx))
    ensure_env(update_env)
    # We have to compile less files before static web content generation.
    media_root = '{}/media'.format(src_root)
    css_root = '{}/css'.format(media_root)
    less_root = '{}/less'.format(media_root)
    mkdir(css_root)
    compile(less_root, css_root, ('troia.less', 'bootstrap.less'))
    with prefix('source {virtualenv_root}/bin/activate'.format(**ctx)):
        message(colors.blue('Generating static content'))
        run('hyde -g -s \'{}\' -d \'{}\''.format(src_root, ctx['hyde_root']))

@task
def deploy(ctxpath=None):
    print ctx
