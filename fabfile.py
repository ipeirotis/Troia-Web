import os

from fabric import colors, api


USER_NAME = "dsas"
USER_HOME = os.path.join("/home", USER_NAME)
HOST_NAME = "178.32.233.139"
HOST_NAME = "ci.10clouds.com"
PROJECT_NAME = "dsas"
PROJECT_ROOT = os.path.join(USER_HOME, PROJECT_NAME)
ENVIRONMENT_NAME = "virtualenv"
STATIC_ROOT = os.path.join(USER_HOME, "static")
SOURCE = "source {}".format(
        os.path.join(PROJECT_ROOT, ENVIRONMENT_NAME, "bin", "activate"))
LOGIN = "{}@{}".format(USER_NAME, HOST_NAME)
REPOSITORY = "git@github.com:borysiam/DSaS"
LESSC = "lessc"

def message(msg, *args):
    print colors.cyan("==>", bold=True), msg.format(*args)

def prepare():
    message(colors.blue("Preparing directories"))
    with api.cd(STATIC_ROOT):
        api.run("mkdir -p logs/nginx/")
        api.run("mkdir -p services/nginx/")

def clone(repository):
    message(colors.yellow("Clonning repository"))
    with api.cd(USER_HOME):
        api.run("git clone {} {}".format(REPOSITORY, PROJECT_ROOT))

def update():
    message(colors.blue("Updating repository"))
    with api.cd(PROJECT_ROOT):
        api.run("git stash")
        api.run("git pull --rebase")
        api.run("git diff")

def create_env():
    message(colors.blue("Creating virtual environment"))
    with api.cd(PROJECT_ROOT):
        api.run("virtualenv --python=\"/usr/bin/python2.7\" --no-site-packages "
                "{}".format(ENVIRONMENT_NAME))

def update_env():
    message(colors.blue("Installing requirements"))
    with api.cd(PROJECT_ROOT):
        with api.prefix(SOURCE):
            api.run('pip install -r requirements.txt')

def compile(input_dir, output_dir, files):
    """ Compiles less and moves resultant css to another directory for
        further processing using hyde. """
    message(colors.blue("Compiling less from {} to {}".format(input_dir,
                        output_dir)))
    message(colors.blue("Files to compile: {}".format(", ".join(files))))
    with api.cd(input_dir):
        for file_name in files:
            name, ext = file_name.rsplit(".", 1)
            result_name = "{}.css".format(name)
            api.run("{} {} > {}".format(LESSC, file_name,
                                        os.path.join(output_dir, result_name)))

def generate():
    message(colors.blue("Generating static content"))
    with api.prefix(SOURCE):
        api.run("hyde -g -s \"{}\" -d \"{}\"".format(PROJECT_ROOT, STATIC_ROOT))
    prepare()

@api.hosts(LOGIN)
def initialize():
    clone(REPOSITORY)
    create_env()
    update_env()

@api.hosts(LOGIN)
def deploy(update_env=False):
    update()
    if update_env:
        update_env()
    media_root = os.path.join(PROJECT_NAME, "media")
    compile(os.path.join(media_root, "less"), os.path.join(media_root, "css"),
            ("bootstrap.less",))
    generate()
