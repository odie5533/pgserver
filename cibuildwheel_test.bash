#! /bin/bash
PROJECT=$1

echo "Running on OSTYPE=$OSTYPE with UID=$UID"

# Ensure a writable runtime dir for interprocess lock & unix sockets on CI
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp}
if [ ! -w "$XDG_RUNTIME_DIR" ]; then
  echo "XDG_RUNTIME_DIR ($XDG_RUNTIME_DIR) not writable; using /tmp"
  export XDG_RUNTIME_DIR=/tmp
fi

case "$OSTYPE" in
    # linux *)
    #     echo "Tests disabled on the manylinux docker container for now"
    #     ;;
    *)
        pytest -s -v --log-cli-level=INFO $PROJECT/tests
        ;;
esac
