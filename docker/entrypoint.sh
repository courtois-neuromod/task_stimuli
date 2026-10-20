#!/bin/bash
. /src/.venv/bin/activate

if [ $(id -u) -eq 0 ];
    USERNAME=user
    HOST_UID=${HOST_UID:?set HOST_UID}
    HOST_UID=${HOST_GID:?set HOST_GID}

    useradd -u "${HOST_UID}" -o -m "${USERNAME}"
    groupmod -g "${HOST_GID}" "${USERNAME}"
fi

source /src/.venv/bin/activate
cd /src/task_stimuli/

if [ $(id -u) -eq 0 ];
    gosu $USERNAME $@
else
    $@
fi
#gosu $USERNAME /usr/bin/python3 /src/task_stimuli/main.py $@
