#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
source /opt/livox_ws/install/setup.bash
source /hrc_ws/install/setup.bash
exec "$@"
