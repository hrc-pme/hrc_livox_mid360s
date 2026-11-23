# hrc_livox_mid360s

HRC 實驗室 Livox **Mid-360S** 光達的 Docker + ROS 2 Humble 環境。

- 使用官方 [Livox-SDK2](https://github.com/Livox-SDK/Livox-SDK2) 與 [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2)，在 Docker build 時自動下載並編譯。
- `hrc_livox` 是我們自己的 ROS 2 package，提供 launch 檔，以及實驗室兩台光達的 IP 設定。
- 一行指令選擇要用哪一台，不用手動改 IP、也不用重新 build。

> ⚠️ 這兩台是 **Mid-360S**（SDK 型號代碼 35），不是一般 Mid-360（型號 9）。直接用官方的 `MID360_config.json` / `rviz_MID360_launch.py` 會「找得到光達但收不到點雲」。本 repo 已經處理好，使用的是官方的 `MID360s_config.json`。

## 實驗室光達

| 編號 | 光達 IP | 測試日期 |
|---|---|---|
| 1 | `192.168.1.199` | 2026-11-20 |
| 2 | `192.168.1.119` | 2026-11-23 |

電腦端 IP 固定是 `192.168.1.5`。兩台的 IP 記錄在 `hrc_livox/config/lidars.yaml`，新增光達時加在這裡。

## 1. 硬體接線

1. 轉接線的 M12 接頭對準定位凸點插進光達，用手鎖緊螺帽。
2. RJ45 網路線**直接**接電腦的有線網卡，不經過路由器。
3. 細訊號線（PPS / GPS / IO，3.3V）用不到，線頭各自用膠帶包好。
4. 最後插 12V 電源（9–27V DC 都可以），等約 10 秒讓光達開機。

## 2. 電腦網路設定（每台電腦做一次，在主機上執行）

```bash
./scripts/setup_host_network.sh              # 先列出有線網卡名稱
./scripts/setup_host_network.sh enp5s0       # 例如網卡是 enp5s0
```

這會建立一個叫 `livox` 的 NetworkManager 連線，把該網卡固定成 `192.168.1.5`。只影響這張有線網卡，Wi-Fi 上網不受影響。要還原就執行 `sudo nmcli con delete livox`。

> 如果用第二個參數改了電腦端 IP（例如 `./scripts/setup_host_network.sh enp5s0 192.168.1.50`），`hrc_livox/config/lidars.yaml` 裡的 `host_ip` 也要改成一樣，否則收不到點雲。

確認光達有在送資料：

```bash
ping -c 4 192.168.1.199
sudo tcpdump -i enp5s0 -n -c 10     # 看到 192.168.1.1xx → 192.168.1.5.56301 就是點雲
```

## 3. Build 與啟動 Docker

第一次 build 需要下載與編譯，約 10 分鐘。

```bash
git clone git@github.com:hrc-pme/hrc_livox_mid360s.git
cd hrc_livox_mid360s
xhost +local:docker
docker compose build
docker compose up -d
docker compose exec livox bash
```

之後再使用：

```bash
xhost +local:docker
docker compose up -d
docker compose exec livox bash
```

用完關閉：`docker compose down`

**ROS_DOMAIN_ID**：容器使用 host 網路，同一個網段（例如實驗室 Wi-Fi）上其他人的 ROS 2 topic 會互相看到。預設是 `0`；多人同時使用時，每人在主機上設定不同的值再啟動：

```bash
export ROS_DOMAIN_ID=23   # 0–101 任選，跟別人不同即可
docker compose up -d
```

## 4. 啟動光達（容器內）

```bash
ros2 launch hrc_livox livox_mid360s.launch.py               # 第 1 台 + RViz
ros2 launch hrc_livox livox_mid360s.launch.py lidar:=2      # 第 2 台
ros2 launch hrc_livox livox_mid360s.launch.py rviz:=false   # 不開 RViz
ros2 launch hrc_livox livox_mid360s.launch.py xfer_format:=1   # Livox CustomMsg（給 FAST-LIO 等用）
ros2 launch hrc_livox livox_mid360s.launch.py lidar:=all    # 兩台同時（需網路交換器）
```

| 參數 | 預設 | 說明 |
|---|---|---|
| `lidar` | `1` | `1`、`2`、`all` 或 `1,2` |
| `rviz` | `true` | 是否開 RViz |
| `xfer_format` | `0` | `0`：PointCloud2，`1`：Livox CustomMsg |
| `frame_id` | `livox_frame` | 點雲與 IMU 的 frame |
| `publish_freq` | `10.0` | 點雲發布頻率 (Hz) |
| `lidars_file` | `config/lidars.yaml` | 光達 IP 清單 |

注意：

- `xfer_format:=1`（Livox CustomMsg）時 RViz 無法顯示點雲，通常搭配 `rviz:=false`，用 `ros2 topic hz` 確認資料。
- 改了 `frame_id` 的話，RViz 左側的 Fixed Frame 也要改成同一個名稱。

## 5. 檢查資料（另開一個終端）

```bash
docker compose exec livox bash
ros2 topic hz /livox/lidar         # 約 10 Hz（剛開始幾秒可能偏高，跑 15 秒會穩定）
ros2 topic hz /livox/imu           # 約 200 Hz
ros2 topic echo /livox/imu --once  # 靜止時 linear_acceleration z ≈ 1
```

| 項目 | 正常值 |
|---|---|
| `/livox/lidar` | 約 10 Hz，RViz 看得到 360° 點雲 |
| `/livox/imu` | 約 200 Hz |
| IMU 靜止時 | z ≈ 1、x ≈ 0、y ≈ 0（**單位是 g**，不是 m/s²；接 SLAM 時注意） |
| IMU orientation | 全 0、w = 1（6 軸 IMU，不算姿態，正常） |

`lidar:=all` 時每台各有自己的 topic，名稱會帶光達 IP，用 `ros2 topic list` 查看。兩台的外參（extrinsic）目前都是 0，實際安裝後需要另外標定。

## 6. 常見問題

| 症狀 | 原因 / 解法 |
|---|---|
| `ping` 不通 | 確認 `ip a show enp5s0` 有 `192.168.1.5`（沒有就 `sudo nmcli con up livox`）；確認電源、M12 接頭有鎖緊；用 tcpdump 看光達實際 IP |
| driver 印出 `GetFreeIndex key:livox_lidar_...` 但 `ros2 topic hz` 沒有輸出 | 用錯型號設定（Mid-360 vs Mid-360S），或 `lidars.yaml` 裡的 IP 跟實際接的光達不一樣 |
| RViz 顯示 `Fixed Frame: No tf data` | 還沒收到資料，先用 `ros2 topic hz` 確認 |
| `docker compose up` 出現 `/dev/dri` 錯誤 | 電腦沒有顯示卡裝置，把 `docker-compose.yml` 裡 `devices` 那兩行刪掉 |
| RViz 開不起來 / `cannot open display` | 主機上先執行 `xhost +local:docker` |

## 7. 檔案結構

```
.
├── Dockerfile                 # ROS 2 Humble + Livox-SDK2 + livox_ros_driver2 + hrc_livox
├── docker-compose.yml         # host 網路、顯示、GPU、掛載 hrc_livox 原始碼
├── .dockerignore
├── .gitignore
├── hrc_livox/                 # ROS 2 package（ament_cmake）
│   ├── package.xml
│   ├── CMakeLists.txt
│   ├── config/lidars.yaml     # 光達 IP 清單
│   └── launch/
│       ├── livox_mid360s.launch.py
│       └── livox_config_utils.py   # 用官方 MID360s_config.json 當範本產生設定
└── scripts/
    ├── entrypoint.sh
    └── setup_host_network.sh  # 主機網路設定
```

修改 `hrc_livox/` 底下**現有的** launch 或 config **不需要重新 build image**，因為原始碼是掛載進容器的。

**新增**檔案的話，可以先在容器內執行 `cd /hrc_ws && colcon build --symlink-install` 立即使用；但這個 build 結果只存在目前的容器裡，`docker compose down` 之後就會消失。要永久生效請在主機上重新 build image：`docker compose build && docker compose up -d`。

## 版本

- Livox-SDK2：commit `c0796f0`（Dockerfile 的 `LIVOX_SDK2_REF`）
- livox_ros_driver2：1.2.8，commit `2144554`（Dockerfile 的 `LIVOX_DRIVER_REF`）
- 測試電腦：Ubuntu 24.04 主機 + ROS 2 Humble 容器
