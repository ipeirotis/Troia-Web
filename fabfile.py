import os

from fabric import colors
from fabric.api import cd, env, prefix, run, sudo, task


PROJECT_NAME = "troia-web"
PROJECTS_ROOT = "/data/projects"
PROJECT_ROOT = "{}/{}".format(PROJECTS_ROOT, PROJECT_NAME)
STATIC_ROOT = "{}/static".format(PROJECT_ROOT)
SOURCE_ROOT = "{}/source".format(PROJECT_ROOT)
ENVIRONMENT_NAME = "virtualenv"
SOURCE = "source {}".format(
        os.path.join(PROJECT_ROOT, ENVIRONMENT_NAME, "bin", "activate"))
REPOSITORY = "git://github.com/10clouds/Troia-Web.git"
LESSC = "lessc"

USER = "{0}:{0}".format(env.user)


def message(msg, *args):
    print colors.cyan("==>", bold=True), msg.format(*args)


def setmode(path, recursive=False, perms=None, owner=None):
    recursive = "--recursive" if recursive else ""
    if perms:
        sudo("chmod {} {} {}".format(recursive, perms, path))
    if owner:
        sudo("chown {} {} {}".format(recursive, owner, path))


def update():
    message(colors.blue("Updating repository"))
    with cd(SOURCE_ROOT):
        run("git stash")
        run("git pull --rebase")
        run("git diff")


def create_env():
    message(colors.blue("Creating virtual environment"))
    with cd(PROJECT_ROOT):
        sudo("virtualenv --python=\"/usr/bin/python2.7\" --no-site-packages "
             "{}".format(ENVIRONMENT_NAME))
        setmode("{}/{}".format(PROJECT_ROOT, ENVIRONMENT_NAME),
                recursive=True, owner=USER)


def update_env():
    message(colors.blue("Installing requirements"))
    with cd(SOURCE_ROOT):
        with prefix(SOURCE):
            run('pip install -r requirements.txt')


def compile(input_dir, output_dir, files):
    """ Compiles less and moves resultant css to another directory for
        further processing using hyde. """
    message(colors.blue("Compiling less from {} to {}".format(input_dir,
                        output_dir)))
    message(colors.blue("Files to compile: {}".format(", ".join(files))))
    with cd(input_dir):
        for file_name in files:
            name, ext = file_name.rsplit(".", 1)
            result_name = "{}.css".format(name)
            run("{} {} > {}".format(LESSC, file_name,
                                    os.path.join(output_dir, result_name)))


def generate():
    message(colors.blue("Generating static content"))
    # Ensure static subdirectory exists.
    sudo("mkdir -p {}".format(STATIC_ROOT))
    setmode(STATIC_ROOT, recursive=True, owner=USER)
    with prefix(SOURCE):
        run("hyde -g -s \"{}\" -d \"{}\"".format(SOURCE_ROOT, STATIC_ROOT))
    # Prepares directories structure for nginx.
    message(colors.blue("Preparing directories structure"))
    with cd(STATIC_ROOT):
        run("mkdir -p logs/nginx/")
        run("mkdir -p services/nginx/")


@task
def initialize():
    message(colors.yellow("Initializing project structure"))
    sudo("mkdir -p {}".format(SOURCE_ROOT))
    setmode(SOURCE_ROOT, recursive=True, owner=USER)
    run("git clone {} {}".format(REPOSITORY, SOURCE_ROOT))
    create_env()
    update_env()


@task
def deploy(update_environment=False, update_nginx=False):
    update()
    if update_environment:
        update_env()
    media_root = "{}/media".format(SOURCE_ROOT)
    css_path = "{}/css".format(media_root)
    less_path = "{}/less".format(media_root)
    run("mkdir -p {}".format(css_path))
    compile(less_path, css_path, ("troia.less", "bootstrap.less"))
    generate()
    # Make sure that all directories are created.
    run("mkdir -p {}".format(os.path.join(media_root, "downloads")))
    # Update nginx configuration.
    if update_nginx:
        ngnx_path = "/etc/nginx"
        available_path = "{}/sites-available/troia".format(ngnx_path)
        enabled_path = "{}/sites-enabled/troia".format(ngnx_path)
        conf_path = "{}/conf/nginx/sites-available/troia".format(SOURCE_ROOT)
        sudo("cp {} {}".format(conf_path, available_path))
        sudo("ln -fs {} {}".format(available_path, enabled_path))
        setmode(available_path, owner=USER)
        setmode(enabled_path, owner=USER)
        sudo("service nginx reload")
