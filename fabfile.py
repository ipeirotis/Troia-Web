import os

from fabric import colors
from fabric.api import cd, env, prefix, run, sudo, task
from fabric.tasks import execute
from fabric.contrib.files import exists, upload_template


PROJECT_NAME = "troia-staging"
PROJECTS_ROOT = "/data/projects"
PROJECT_ROOT = "{}/{}".format(PROJECTS_ROOT, PROJECT_NAME)
STATIC_ROOT = "{}/static".format(PROJECT_ROOT)
SOURCE_ROOT = "{}/source".format(PROJECT_ROOT)
WEB_SOURCE_ROOT = "{}/Troia-Web".format(SOURCE_ROOT)
WAR_SOURCE_ROOT = "{}/Troia-Server".format(SOURCE_ROOT)
ENVIRONMENT_ROOT = "{}/virtualenv".format(PROJECT_ROOT)
ENVIRONMENT_SOURCE = "source {}/bin/activate".format(ENVIRONMENT_ROOT)

WEB_REPOSITORY = "git://github.com/10clouds/Troia-Web.git"
WAR_REPOSITORY = "git://github.com/ipeirotis/Troia-Server.git"

LESSC = "lessc"
USER = "{0}:{0}".format(env.user)

# Desired Python interpretter.
INTERPRETTER = "/usr/bin/python2.7"
# Path to your maven binaries.
MVN = "/opt/maven/bin/mvn"
SERVICE_PREFIX = "service "
# SERVICE_PREFIX = "/etc/rc.d/"  # In case of FreeBSD init convention.


def message(msg, *args):
    print colors.cyan("==>", bold=True), msg.format(*args)


def setmode(path, recursive=False, perms=None, owner=None):
    recursive = "--recursive" if recursive else ""
    if perms:
        sudo("chmod {} {} {}".format(recursive, perms, path))
    if owner:
        sudo("chown {} {} {}".format(recursive, owner, path))


def clone_or_update(path, repo):
    """ Updates a local repository or clones it. """
    run("""
        if cd {path} && git status; then
            echo "Local repository exists. Updating"
            git stash;
            git pull --rebase;
            git diff;
        elif cd {path}; then
            echo "Local repository exists but it is not a git repository".
            exit 255;
        else
            git clone {repo} {path};
        fi""".format(path=path, repo=repo))


def ensure(path, update=False, requirements_path=None,
           interpretter=INTERPRETTER):
    """ Ensures environment already exists (creates if missing). """
    splitted = path.rsplit("/", 1)
    if len(splitted) == 2:
        root = splitted[0]
        name = splitted[1]
    else:
        raise Exception("Invalid path for virtual environment {}".format(path))
    run("""
        if cd {path}/bin && source activate; then
            echo "Virtual environment exists";
        elif cd {path}; then
            echo "Virtual environment already exist but can not be activated";
            exit 255
        else
            echo "Virtual environment does not exist. Creating the new one";
            cd {root} && virtualenv --python={interpretter} \
                                    --no-site-packages {name};
            source {path}/bin/activate && pip install -r {requirements_path};
        fi
        """.format(path=path, name=name, root=root, interpretter=interpretter,
                   requirements_path=requirements_path))
    if update:
        run("""
            source {path}/bin/activate && pip install -r {requirements_path}
            """.format(path=path, requirements_path=requirements_path))


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


def generate(source_root=WEB_SOURCE_ROOT, static_root=STATIC_ROOT,
             environment_source=ENVIRONMENT_SOURCE):
    message(colors.blue("Generating static content"))
    # Ensure the static subdirectory exists.
    run("mkdir -p {}".format(static_root))
    print environment_source
    with prefix(environment_source):
        run("hyde -g -s \"{}\" -d \"{}\"".format(source_root, static_root))
    # Prepares some directories structure for nginx.
    message(colors.blue("Preparing directories structure"))
    with cd(static_root):
        run("mkdir -p logs/nginx/")
        run("mkdir -p services/nginx/")


@task
def update_server():
    """ Updates server configuration. """
    server_root = "/etc/nginx"
    local_root = os.path.dirname(os.path.abspath(__name__))
    local_path = os.path.join(local_root, "conf", "nginx", "sites-available",
                              "troia")
    available_path = "{}/sites-available/troia".format(server_root)
    enabled_path = "{}/sites-enabled/troia".format(server_root)
    context = {"project_root": PROJECT_ROOT, "project_name": PROJECT_NAME}
    upload_template(local_path, available_path, use_sudo=True, context=context)
    sudo("ln -fs {} {}".format(available_path, enabled_path))
    setmode(available_path, owner=USER)
    setmode(enabled_path, owner=USER)
    sudo("{}nginx reload".format(SERVICE_PREFIX))


@task
def update_war():
    """ Builds a war file and exposes it on the website. """
    clone_or_update(WAR_SOURCE_ROOT, WAR_REPOSITORY)
    source = "{}/target/GetAnotherLabel.war".format(WAR_SOURCE_ROOT)
    media = "{}/media".format(STATIC_ROOT)
    destination = "{}/downloads/".format(media)
    with cd(WAR_SOURCE_ROOT):
        run("{} package -Dmaven.test.skip=true".format(MVN))
    run("cp {} {}".format(source, destination))


@task
def deploy(update_environment=False, update_war=False,
           update_server=False):
    """ Synchronizes the website content with the repository. """
    if not exists(PROJECT_ROOT):
        message(colors.yellow("Initializing project structure"))
        sudo("mkdir -p {}".format(SOURCE_ROOT))
        setmode(PROJECT_ROOT, recursive=True, owner=USER)

    # Project root alredy exists. Current remote user is assummed to be an
    # onwer of the directory.
    clone_or_update(WEB_SOURCE_ROOT, WEB_REPOSITORY)
    ensure(update=update_environment, path=ENVIRONMENT_ROOT,
           requirements_path="{}/requirements.txt".format(WEB_SOURCE_ROOT))
    media_root = "{}/media".format(WEB_SOURCE_ROOT)
    css_path = "{}/css".format(media_root)
    less_path = "{}/less".format(media_root)
    run("mkdir -p {}".format(css_path))
    compile(less_path, css_path, ("troia.less", "bootstrap.less"))
    generate(source_root=WEB_SOURCE_ROOT, static_root=STATIC_ROOT,
             environment_source=ENVIRONMENT_SOURCE)
    # Ensure downloads directory exists.
    run("mkdir -p {}/media/downloads".format(STATIC_ROOT))
    # Update server configuration.
    if update_server:
        execute(update_server)
    if update_war:
        execute(update_war)
