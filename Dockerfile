# HRC Lab - Livox Mid-360S (ROS 2 Humble)
# Builds: Livox-SDK2 + livox_ros_driver2 (official) + hrc_livox (our launch/config package)

FROM osrf/ros:humble-desktop

# ---- Pinned versions (change here to upgrade) ----
# Livox-SDK2 commit tested on hrc631 (2026-11-20/23)
ARG LIVOX_SDK2_REF=c0796f0
# livox_ros_driver2 commit tested on hrc631 (version 1.2.8)
ARG LIVOX_DRIVER_REF=2144554

ENV DEBIAN_FRONTEND=noninteractive
# Avoid root-owned __pycache__ in the host-mounted hrc_livox folder
ENV PYTHONDONTWRITEBYTECODE=1
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
        git cmake build-essential iproute2 iputils-ping tcpdump nano \
        python3-yaml \
    && rm -rf /var/lib/apt/lists/*

# ---- 1. Livox-SDK2 ----
RUN git clone https://github.com/Livox-SDK/Livox-SDK2.git /opt/Livox-SDK2 \
    && cd /opt/Livox-SDK2 && git checkout ${LIVOX_SDK2_REF} \
    && mkdir build && cd build \
    && cmake .. && make -j"$(nproc)" && make install \
    && ldconfig

# ---- 2. livox_ros_driver2 (must be built with its own build.sh) ----
RUN mkdir -p /opt/livox_ws/src \
    && git clone https://github.com/Livox-SDK/livox_ros_driver2.git /opt/livox_ws/src/livox_ros_driver2 \
    && cd /opt/livox_ws/src/livox_ros_driver2 && git checkout ${LIVOX_DRIVER_REF} \
    && source /opt/ros/humble/setup.bash \
    && ./build.sh humble

# ---- 3. hrc_livox (this repo) ----
WORKDIR /hrc_ws
COPY hrc_livox /hrc_ws/src/hrc_livox
RUN source /opt/ros/humble/setup.bash \
    && source /opt/livox_ws/install/setup.bash \
    && colcon build --symlink-install

# ---- Environment for every shell ----
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && echo 'source /opt/ros/humble/setup.bash' >> /root/.bashrc \
    && echo 'source /opt/livox_ws/install/setup.bash' >> /root/.bashrc \
    && echo 'source /hrc_ws/install/setup.bash' >> /root/.bashrc

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
