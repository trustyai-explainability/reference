import subprocess
import sys
import time
import re


def get_projects():
    # get all projects
    cmd = r"oc get projects -o name"
    projects = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = projects.stdout.decode("utf-8")
    return [project.split("/")[-1] for project in stdout.strip().split("\n")]


def filter_projects(projects):
    # filter out projects whose disconnection breaks the openshift console
    filter_keywords = ["auth", "console", "openshift-ingress"]
    to_filter = [project for project in projects if any(filter_keyword in project for filter_keyword in filter_keywords)]
    print("The following namespaces will not be changed:", to_filter)
    return [project for project in projects if project not in to_filter]


def get_longest_name(projects):
    return max([len(project) for project in projects])


def connect_or_disconnect(disconnect):
    projects_to_modify = filter_projects(get_projects()) if disconnect else get_projects()

    connected, disconnected = check_connectivity()

    if disconnect:
        # skip projects that are already disconnected
        projects_to_modify = [p for p in projects_to_modify if p not in disconnected]
    else:
        # skip projects that are already connected
        projects_to_modify = [p for p in projects_to_modify if p not in connected]

    if (len(projects_to_modify) == 0):
        print("All possible projects already", "disconnected." if disconnect else "connected.")
        return

    longest_project_name = get_longest_name(projects_to_modify)
    num_projects = len(projects_to_modify)
    fmt_string = "\r{{:>{}}}/{{:<{}}}: {{}} namespace {{:<{}}}".format(len(str(num_projects)), len(str(num_projects)), longest_project_name+1)

    # === apply/delete the disconnect NetworkPolicy ================================================
    for project_idx, project in enumerate(projects_to_modify):
        verb = "Disconnecting" if disconnect else "Connecting"
        print(fmt_string.format(project_idx, num_projects, verb, project), end="")

        if disconnect:
            cmd = "oc apply -f disconnect.yaml -n {}".format(project)
            subprocess.run(cmd.split())
        else:
            cmd = "oc delete -f disconnect.yaml -n {}  --ignore-not-found".format(project)
            subprocess.run(cmd.split())


def check_connectivity(verbose=False):
    all_namespaces = get_projects()
    cmd = "oc get networkpolicies --all-namespaces"
    projects = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = projects.stdout.decode("utf-8").strip().split("\n")
    lines = [re.split(" +",line) for line in lines]

    namespaces = {n:False for n in all_namespaces}
    for line in lines[1:]:
        namespace, policy_name, _, _ = line
        if policy_name == "disconnect":
            namespaces[namespace] = True

    connected = []
    disconnected = []

    for ns, is_disconnected in namespaces.items():
        if is_disconnected:
            disconnected.append(ns)
        else:
            connected.append(ns)

    if verbose:
        header = "="*(get_longest_name(all_namespaces)//2 + 1)
        print("{} Connected Namespaces {}".format(header, header))
        for namespace in connected:
            print(namespace)

        print("\n{} Disconnected Namespaces {}".format(header, header))
        for namespace in disconnected:
            print(namespace)

    return connected, disconnected



if __name__ == '__main__':
    # parse args

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = None

    # === get the projects to disconnect/connect ===================================================
    if command == "disconnect" or command == "connect":
        connect_or_disconnect(command == "disconnect")
    elif command == "check":
        check_connectivity(verbose=True)
    else:
        print()
        print("No command provided. Usage: python3 cluster_connector.py $COMMAND")
        print("Available commands are [connect, disconnect, check]")