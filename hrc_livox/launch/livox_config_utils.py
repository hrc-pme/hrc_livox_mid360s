"""Build a livox_ros_driver2 JSON config for HRC Mid-360S units.

The official driver ships config/MID360s_config.json. Instead of copying it
(and drifting from upstream), we load it as a template and only replace:
  - every non-empty "*_ip" value under "host_net_info" -> host_ip
  - "lidar_configs" -> one entry per selected lidar IP
"""
import copy
import json

import yaml


def load_lidars(lidars_file):
    with open(lidars_file, 'r') as f:
        data = yaml.safe_load(f)
    host_ip = str(data['host_ip'])
    lidars = {str(k): str(v) for k, v in data['lidars'].items()}
    return host_ip, lidars


def select_ips(lidar_arg, lidars):
    """lidar_arg: '1', '2', 'all', or a comma list like '1,2'."""
    lidar_arg = str(lidar_arg).strip()
    if lidar_arg == 'all':
        names = list(lidars.keys())
    else:
        names = [n.strip() for n in lidar_arg.split(',') if n.strip()]
    unknown = [n for n in names if n not in lidars]
    if unknown or not names:
        raise ValueError(
            f"Unknown lidar '{lidar_arg}'. Choose from: {', '.join(lidars)} or 'all'")
    return [lidars[n] for n in names]


def _replace_host_ips(node, host_ip):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str) and key.endswith('_ip') and value:
                node[key] = host_ip
            else:
                _replace_host_ips(value, host_ip)
    elif isinstance(node, list):
        for item in node:
            _replace_host_ips(item, host_ip)


def build_config(template, host_ip, lidar_ips):
    cfg = copy.deepcopy(template)
    found_host = False
    for value in cfg.values():
        if isinstance(value, dict) and 'host_net_info' in value:
            _replace_host_ips(value['host_net_info'], host_ip)
            found_host = True
    if not found_host:
        raise ValueError('Template has no "host_net_info" section')

    if not cfg.get('lidar_configs'):
        raise ValueError('Template has no "lidar_configs" entry')
    base = cfg['lidar_configs'][0]
    entries = []
    for ip in lidar_ips:
        entry = copy.deepcopy(base)
        entry['ip'] = ip
        entries.append(entry)
    cfg['lidar_configs'] = entries
    return cfg


def write_config(template_path, lidars_file, lidar_arg, out_path):
    with open(template_path, 'r') as f:
        template = json.load(f)
    host_ip, lidars = load_lidars(lidars_file)
    ips = select_ips(lidar_arg, lidars)
    cfg = build_config(template, host_ip, ips)
    with open(out_path, 'w') as f:
        json.dump(cfg, f, indent=2)
    return ips
