#!/bin/sh

set -x
ACTION=$1
PROJECT=$2
shift

function start_oc() {
    # First of all, we start the cluster
    oc cluster up

    # Create user and a project for him
    oc login -u ocuser
    oc new-project $PROJECT

    # We switch to "system" user and then  we can create the k8 resources.
    # This is only necessary for the Persistent Storage
    oc login -u system:admin

    # Create service account and allow to run processes as root (required for init)
    oc create serviceaccount useroot
    oc adm policy add-scc-to-user anyuid -z useroot

    # Create a temporary copy of the macrocontainer. This assumes default leapp installation
    sudo rm -rf /tmp/macrocontainer
    sudo cp /var/lib/leapp/macrocontainers/container_centos6-app-vm /tmp/macrocontainer -av

    # Change SELinux security context
    sudo chcon -R -t svirt_sandbox_file_t -l s0 /tmp/macrocontainer

    # Create everything from template files
    oc create -f hostPath/
    #oc create -f nfs/
}

function stop_oc() {
    # Swithc to "system" user so we get permissions to delete storage
	oc login -u system:admin

    # Delete everything from $PROJECT and shut the cluster down
	oc delete all -l app=$PROJECT
    oc create -f hostPath/
	oc cluster down
}

function main() {
    case $ACTION in
        start)
            start_oc
            ;;
        stop)
            stop_oc
            ;;
        *)
            echo "Not a valid action"
            ;;
    esac
}

main
