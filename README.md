# 🤖 lerobot_piper3

**LeRobot × Piper Arm — Real-World Low-Cost Manipulation Stack**

<img src="https://hackster.imgix.net/uploads/attachments/1711216/image_oknKDbrt1n.png?auto=compress%2Cformat&w=830&h=466.875&fit=min&dpr=2.625" width="70%" />
<img src="https://media.licdn.com/dms/image/v2/D4D05AQERe2QXVLINxA/feedshare-thumbnail_720_1280/feedshare-thumbnail_720_1280/0/1730105448536?e=2147483647&v=beta&t=_BSbWckZMMLJERIcf1Z5vdm46C-lJ6rJexCbIwzzp1Q" width="22%" />

> **Native integration of AgileX Piper manipulators into the LeRobot v2 ecosystem.** > *Infrastructure as Code | Type-Safe Configuration | End-to-End Imitation Learning*

> A third-party, community-driven continuation of `lerobot_piper2`,  
> providing **robust Piper robot arm support** for the LeRobot ecosystem (as of Feb. 2026).

* * *

## 🔗 Lineage & Scope

* **Upstream framework**:  
    👉 [LeRobot (HuggingFace)](https://github.com/huggingface/lerobot)

    
* **Previous generation**:  
    👉 [lerobot_piper2](https://github.com/Kane1440/lerobot_piper2)

* **Piper SDK**:  
    👉 [Piper SDK](https://github.com/agilexrobotics/piper_sdk)
    
* **This repository**:  
    😋 **lerobot_piper3** (current, maintained, extended)
    

This repository is **NOT an official LeRobot repository**.  
It is a **hardware adaptation + engineering continuation** focused on:

* Piper leader–follower teleoperation
    
* RealSense / OpenCV multi-camera setups
    
* Dataset collection, editing, conversion, and training
    
* ACT / Diffusion-style policies on real robots
    

* * *

## 📦 Installation

```bash
git clone https://github.com/WilbertYuan/lerobot_piper3.git
cd lerobot_piper3
pip install -e .
```

Make sure you have already installed **LeRobot** and **piper_sdk**:

```bash
pip install lerobot piper_sdk
```

* * *

## 🔐 HuggingFace Authentication

LeRobot datasets and trained policies rely on HuggingFace Hub.

### Login & environment setup

```bash
hf auth login --token <YOUR_TOKEN> --add-to-git-credential
export HF_USER=$(hf auth whoami | head -n 1 | awk '{print $3}')
```



* * *

## 🕹️ Teleoperation（Leader–Follower）

### 基础遥操作（无相机）

```bash
lerobot-teleoperate \
  --robot.type=piper_follower \
  --robot.id=black \
  --teleop.type=piper_leader \
  --teleop.id=blue
```

* `robot.type`: 被控机械臂（Follower）
    
* `teleop.type`: 主控机械臂（Leader）
    
* `id`: 用于区分多机械臂实例
    

* * *

### 带相机遥操作（实时可视化）

```bash
lerobot-teleoperate \
  --robot.type=piper_follower \
  --robot.id=black \
  --robot.cameras="{
    laptop: {type: intelrealsense, serial_number_or_name: '152222072122', width: 640, height: 480, fps: 30}
  }" \
  --teleop.type=piper_leader \
  --teleop.id=blue \
  --display_data=true
```

* * *

## 🎥 Dataset Recording（真实数据采集）

```bash
lerobot-record \
  --robot.type=piper_follower \
  --robot.id=black \
  --robot.cameras="{
    laptop: {type: intelrealsense, serial_number_or_name: '152222072122', width: 640, height: 480, fps: 30},
    left_wrist: {type: intelrealsense, serial_number_or_name: '153222071788', width: 640, height: 480, fps: 30}
  }" \
  --teleop.type=piper_leader \
  --teleop.id=blue \
  --display_data=true \
  --dataset.repo_id=${HF_USER}/piper_pick_toy_mini_10eps \
  --dataset.num_episodes=10 \
  --dataset.single_task="Pick up the toy" \
  --dataset.push_to_hub=True
```

关键参数说明：

* `dataset.repo_id`: HuggingFace 数据集名
    
* `num_episodes`: 采集 episode 数
    
* `single_task`: 任务自然语言描述（用于 policy conditioning）
    
* `push_to_hub`: 是否自动上传
    

* * *

## 🧠 Training（Policy Learning）

### ACT Policy

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/piper_pick_toy_mini_10eps \
  --policy.type=act \
  --output_dir=outputs/train/act_piper_pick_toy_mini \
  --job_name=act_piper_pick_toy_mini \
  --policy.device=cuda \
  --wandb.enable=true \
  --policy.repo_id=${HF_USER}/piper_pick_toy_mini
```

* `policy.type`: `act` / `diffusion`
    
* `policy.repo_id`: 训练完成后上传的模型 repo
    
* `wandb.enable`: 实验追踪（可选）
    

* * *

## ✅ Evaluation / Replay

```bash
lerobot-record \
  --robot.type=piper_follower \
  --robot.id=black \
  --robot.cameras="{
    up: {type: opencv, index_or_path: /dev/video10, width: 640, height: 480, fps: 30}
  }" \
  --display_data=false \
  --dataset.repo_id=${HF_USER}/eval_piper \
  --dataset.single_task="Put lego brick into the transparent box" \
  --policy.path=${HF_USER}/my_policy
```

* 不指定 `teleop` 即为 **纯策略执行**
    
* 可用于 quantitative evaluation / video logging
    

* * *

## 🧩 Dataset Operations (lerobot-edit-dataset)

### 删除 Episodes（原数据集上直接操作）

```bash
lerobot-edit-dataset \
  --repo_id ${HF_USER}/pick_toy \
  --operation.type delete_episodes \
  --operation.episode_indices "[50]"
```

* `repo_id`: HuggingFace dataset repo
    
* `delete_episodes`: 删除指定 episode
    
* `episode_indices`: episode 索引（0-based）
    

* * *

### 删除后新建一个数据集（推荐）

```bash
lerobot-edit-dataset \
  --repo_id ${HF_USER}/pick_toy \
  --new_repo_id ${HF_USER}/pick_toy_new \
  --operation.type delete_episodes \
  --operation.episode_indices "[50]"
```

> 原始数据保持不变，新建干净版本，**工程上更安全**。

* * *

### 数据集合并（Merge）

```bash
lerobot-edit-dataset \
  --repo_id ${HF_USER}/piper_pick_toy_mini_60eps \
  --operation.type merge \
  --operation.repo_ids "['${HF_USER}/piper_pick_toy_mini_10eps', 'Zzming/pick_toy']"
```

* 将多个数据集拼接为一个
    
* 常用于跨人/跨场景收集的数据整合
    

* * *

### 数据集分离（Split）

#### 按比例划分

```bash
lerobot-edit-dataset \
  --repo_id lerobot/pusht \
  --operation.type split \
  --operation.splits '{"train": 0.8, "test": 0.2, "val": 0.2}'
```

#### 按 episode index 精确划分

```bash
lerobot-edit-dataset \
  --repo_id lerobot/pusht \
  --operation.type split \
  --operation.splits '{"task1": [0,1,2,3], "task2": [4,5]}'
```

* * *

### 旧版 → 新版数据集转换

```bash
python -m lerobot.datasets.v30.convert_dataset_v21_to_v30 \
  --repo-id ${HF_USER}/pick_toy \
  --root /home/<user>/.cache/huggingface/lerobot
```

用于 **LeRobot v2.x → v3.x** 数据格式升级。

📖 官方文档：  
[https://huggingface.co/docs/lerobot/using_dataset_tools](https://huggingface.co/docs/lerobot/using_dataset_tools)


* * *

## 📜 License & Acknowledgement

* License: **Apache-2.0**
    
* Based on **LeRobot** by HuggingFace
    
* Piper hardware integration is community-maintained
    

* * *

## ✨ Final Note

This repository is intended for:

* **Real-world manipulation research**
    
* **Low-cost robot learning**
    
* **Reproducible ACT / Diffusion pipelines**
    
