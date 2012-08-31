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
APIDOC_ROOT = "{}/apidoc".format(PROJECT_ROOT)
TROIA_WEB_SOURCE_ROOT = "{}/Troia-Web".format(SOURCE_ROOT)
TROIA_SERVER_SOURCE_ROOT = "{}/Troia-Server".format(SOURCE_ROOT)
TROIA_CLIENT_SOURCE_ROOT = "{}/Troia-Java-Client".format(SOURCE_ROOT)
ENVIRONMENT_ROOT = "{}/virtualenv".format(PROJECT_ROOT)
ENVIRONMENT_SOURCE = "source {}/bin/activate".format(ENVIRONMENT_ROOT)

TROIA_WEB_REPOSITORY = "git://github.com/10clouds/Troia-Web.git"
TROIA_SERVER_REPOSITORY = "git://github.com/ipeirotis/Troia-Server.git"
TROIA_CLIENT_REPOSITORY = "git://github.com/10clouds/Troia-Java-Client.git"

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


def build_and_copy(source_root, source, destination, repository, cp_prefix="cp",
                   mvn_command="{} package -Dmaven.test.skip=true".format(MVN)):
    """ Builds maven project and copies results to the specified place. """
    clone_or_update(source_root, repository)
    with cd(source_root):
        run(mvn_command)
    run("{} {} {}".format(cp_prefix, source, destination))



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


def generate(source_root=TROIA_WEB_SOURCE_ROOT, static_root=STATIC_ROOT,
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
def update_troia_server():
    """ Builds the Troia-Server war file and exposes it on the website.
    """
    build_and_copy(
        source_root=TROIA_SERVER_SOURCE_ROOT, 
        source="{}/target/GetAnotherLabel.war".format(TROIA_SERVER_SOURCE_ROOT),
        destination="{}/media/downloads".format(STATIC_ROOT),
        repository=TROIA_SERVER_REPOSITORY)


@task
def update_troia_client():
    build_and_copy(
        source_root=TROIA_CLIENT_SOURCE_ROOT,
        source="{}/target/site/apidocs".format(TROIA_CLIENT_SOURCE_ROOT),
        destination=PROJECT_ROOT,
        repository=TROIA_CLIENT_REPOSITORY,
        mvn_command="{} javadoc:javadoc".format(MVN),
        cp_prefix="cp -rf ")


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
    clone_or_update(TROIA_WEB_SOURCE_ROOT, TROIA_WEB_REPOSITORY)
    ensure(update=update_environment, path=ENVIRONMENT_ROOT,
           requirements_path="{}/requirements.txt"
                             .format(TROIA_WEB_SOURCE_ROOT))
    media_root = "{}/media".format(TROIA_WEB_SOURCE_ROOT)
    css_path = "{}/css".format(media_root)
    less_path = "{}/less".format(media_root)
    run("mkdir -p {}".format(css_path))
    compile(less_path, css_path, ("troia.less", "bootstrap.less"))
    generate(source_root=TROIA_WEB_SOURCE_ROOT, static_root=STATIC_ROOT,
             environment_source=ENVIRONMENT_SOURCE)
    # Ensure downloads directory exists.
    run("mkdir -p {}/media/downloads".format(STATIC_ROOT))
    # Update server configuration.
    if update_server:
        execute(update_server)
    if update_war:
        execute(update_war)
