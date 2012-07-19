from fabric import colors, api


USER_NAME = "dsas"
USER_HOME = "/home/{}/".format(USER_NAME)
HOST_NAME = "178.32.233.139"
HOST_NAME = "ci.10clouds.com"
PROJECT_NAME = "dsas"
PROJECT_ROOT = "/{}/{}/".format(USER_HOME, PROJECT_NAME)
STATIC_ROOT = "/{}/static/".format(USER_HOME)
SOURCE = "/{}/bin/activate".format(PROJECT_ROOT)
LOGIN = "{}@{}".format(USER_NAME, HOST_NAME)
REPOSITORY = "git@github.com:borysiam/DSaS"

def message(msg, *args):
    print colors.cyan("==>", bold=True), msg.format(*args)

def clone(repository):
    message(colors.yellow("Clonning repository"))
    with api.cd(USER_HOME):
        api.run("git clone {} {}".format(REPOSITORY, PROJECT_ROOT))

def update():
    message(colors.blue("Updating {} repository"))
    with api.cd(PROJECT_ROOT):
        api.run("git stash")
        api.run("git pull --rebase")
        api.run("git diff")

def create_env():
    message(colors.blue("Creating virtual environment"))
    with api.cd(PROJECT_ROOT):
        api.run("virtualenv --python=\"/usr/bin/python2.7\" --no-site-packages "
                "virtualenv")

def update_env():
    message(colors.blue("Installing requirements"))
    with api.cd(PROJECT_ROOT):
        api.run('pip install -r requirements.txt')

def generate():
    message(colors.blue("Generating static content"))
    with api.prefix(SOURCE):
        api.run("hyde -g -s \"{}\" -d \"{}\"".format(PROJECT_ROOT, STATIC_ROOT))

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
    generate()
