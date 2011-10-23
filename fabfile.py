from fabric.api import local, run

def prepare_deploy():
    #local("./manage.py test characters")
    local("git stash")

def post_deploy():
    local("git stash pop")


def restart_app():
    run('./uwsgi.sh restart')

def deploy_helper(deploy_dirs, scp_port, scp_server, dest_dir):
    prepare_deploy()
    for deploy_dir in deploy_dirs:
        local("scp -rp -P {} {dd}/* {}:{dest_dir}/{dd}".format(scp_port, scp_server, dd=deploy_dir, dest_dir=dest_dir))

    restart_app()
    post_deploy()

def deploy(scp_port, scp_server, dest_dir):
    deploy_dirs = [
        'apps',
        'fixtures',
        'templates',
        'tests'
    ]
    deploy_helper(deploy_dirs, scp_port, scp_server, dest_dir)

def deploy_apps(scp_port, scp_server, dest_dir):
    deploy_dirs = [
        'apps',
    ]
    deploy_helper(deploy_dirs, scp_port, scp_server, dest_dir)

def deploy_templates(scp_port, scp_server, dest_dir):
    deploy_dirs = [
        'templates',
    ]
    deploy_helper(deploy_dirs, scp_port, scp_server, dest_dir)

#TODO: Needs to copy correctly to the location
def deploy_media(scp_port, scp_server, dest_dir):
    deploy_dirs = [
        'site_media/static',
        'media',
    ]
    for deploy_dir in deploy_dirs:
        local("scp -rp -P {} {dd}/* {}:{dest_dir}/{dd}".format(scp_port, scp_server, dd=deploy_dir, dest_dir=dest_dir))
