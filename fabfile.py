from fabric.api import local, run

def prepare_deploy():
    #local("./manage.py test characters")
    local("git stash")

def post_deploy():
    local("git stash pop")

def deploy(scp_port, scp_server, dest_dir):
    prepare_deploy()
    deploy_dirs = [
        'apps',
        'fixtures',
        'templates',
        'tests'
    ]
    for deploy_dir in deploy_dirs:
        local("scp -rp -P {} {dd}/* {}:{dest_dir}/{dd}".format(scp_port, scp_server, dd=deploy_dir, dest_dir=dest_dir))

    run('./uwsgi.sh restart')
    post_deploy()

def deploy_media(scp_port, scp_server):
    deploy_dirs = [
        'site_media/static',
        'media',
    ]
    for deploy_dir in deploy_dirs:
        local("scp -rp -P {} {dd}/* {}:~/env/testit/{dd}".format(scp_port, scp_server, dd=deploy_dir))
