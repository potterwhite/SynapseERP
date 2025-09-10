<!--
Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
All rights reserved.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

T-HEAD-GR-V0.8.0-20250910 (Chinese README for SynapseERP)
-->

<div align="center">
  <h2>SynapseERP</h2>
  <p><i>一个用于数据分析工具的模块化 Django 框架</i></p>
</div>

<p align="center">
  <img src="./assets/logo.jpg" alt="SynapseERP Logo" width="100%"/>
</p>

<p align="center">
  <a href="https://github.com/potterwhite/SynapseERP/releases"><img src="https://img.shields.io/badge/version-v0.8.0-orange" alt="版本"></a>
  <a href="https://github.com/potterwhite/SynapseERP/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="许可证"></a>
</p>

<p align="center">
  <a href="./README.md">English</a> | <strong>简体中文</strong>
</p>

<p align="center">
  <a href="#1-快速开始">🚀 快速开始</a> •
  <a href="#2-正式部署">⚙️ 正式部署</a> •
  <a href="#3-附录">📚 附录</a>
</p>

---

# 1. 快速开始

本指南旨在帮助你以最快的速度搭建并运行一个本地开发环境。

**先决条件:**
*   Python 3.8+
*   Git (用于克隆仓库)

### 第 1.1 步：获取代码

克隆仓库并进入项目目录：
```bash
git clone git@github.com:potterwhite/SynapseERP.git
cd SynapseERP
```

### 第 1.2 步：准备环境

本项目使用一个完全自动化的准备脚本。

1.  **为脚本赋予执行权限:**
    ```bash
    chmod +x run.sh
    ```

2.  **运行脚本:**
    ```bash
    ./run.sh prepare
    ```
    这一个命令会处理所有事情：它会创建一个 Python 虚拟环境，安装所有依赖，生成一个安全的 `.env` 配置文件，并初始化数据库。

### 第 1.3 步：运行应用

在准备工作完成后：

1.  **创建一个管理员用户:**
    ```bash
    ./run.sh superuser
    ```
    根据提示创建你的管理员账户。

2.  **运行开发服务器:**
    ```bash
    ./run.sh run
    ```
    现在你可以通过 **http://127.0.0.1:8000** 访问应用程序，并通过 **http://127.0.0.1:8000/admin/** 访问后台管理面板。

---

# 2. 正式部署

`./run.sh run` 命令**仅供开发使用**。对于真实的生产环境，你必须使用一个专业的 WSGI 服务器（如 Gunicorn）和一个反向代理（如 Nginx）。本项目包含脚本来简化此过程。

### 第 2.1 步：生成配置文件

在你的生产服务器上，运行交互式的配置生成器：
```bash
./run.sh deploy:config
```
该脚本会询问你：
1.  **你的服务器域名或 IP 地址。**
2.  **将要运行此应用服务的 Linux 用户名。**

然后，它会在你的项目根目录下生成两个生产就绪的文件：`synapse.service` (用于 Systemd/Gunicorn) 和 `synapse_nginx.conf` (用于 Nginx)。

### 第 2.2 步：执行部署指令

生成文件后，脚本会打印出清晰的、分步的指令清单。作为服务器上拥有 `sudo` 权限的用户，你需要遵循这些指令来：

1.  **收集静态文件**，以便 Nginx 可以直接提供服务。
2.  **将生成的服务和 Nginx 配置文件移动**到正确的系统目录中。
3.  **启用并启动服务。**
4.  **关键一步：为生产环境更新你的 `.env` 文件**，设置 `DJANGO_DEBUG='False'` 并用你的域名/IP更新 `DJANGO_ALLOWED_HOSTS`。

脚本的输出会提供你可以直接复制和粘贴的精确命令。

---

# 3. 附录

### 3.1 考勤分析器规则

考勤分析器由一个 TOML 规则文件控制。系统使用一个三层优先级策略来决定加载哪个规则文件：

**`远程 URL > 本地自定义文件 > 默认文件`**

这提供了最大的灵活性。

#### 方法 A (生产环境推荐)：使用远程 URL
当你需要为用户提供一个特定的规则集而无需修改代码时，这是最理想的方法。

*   **设置一个远程规则 URL:**
    ```bash
    # 将此 URL 替换为你自己的 Gist 或原始文件 URL
    ./run.sh set-rule "https://your-url/path/to/rules.toml"
    ```
    此命令会安全地将 URL 保存到你本地的 `.env` 文件中。

*   **清除远程规则 URL** (以恢复使用本地或默认规则):
    ```bash
    ./run.sh set-rule
    ```

#### 方法 B (本地开发使用)：使用本地文件
这对于离线开发或快速测试规则变更非常有用。

1.  在 `src/synapse_attendance/engine/rules/` 目录下创建一个名为 `local_rules.toml` 的文件。
2.  你可以将 `default_rules.toml` 的内容复制进去作为起点。

如果 `.env` 文件中没有设置远程 URL，应用将自动检测并使用此文件。此文件被 Git 忽略。

#### 方法 C (默认)：开箱即用的规则
如果既没有找到远程 URL，也没有找到本地文件，系统将回退使用 `src/synapse_attendance/engine/rules/default_rules.toml`。

### 3.2 开发者命令

这些命令是为**希望修改应用程序源代码或数据库结构**的贡献者或开发者准备的。普通用户在日常使用中**无需**接触这些命令。

*   **`./run.sh dev:migrate`**
    *   **作用:** 创建并应用数据库迁移。
    *   **使用时机:** 在你**修改了 `models.py` 文件之后**，用此命令来更新数据库的结构。

*   **`./run.sh dev:makemessages`**
    *   **作用:** 扫描所有源代码和模板，查找可翻译的字符串，并更新 `.po` 翻译源文件。
    *   **使用时机:** 在你**添加或更改了需要被翻译的用户界面文本之后**使用。

*   **`./run.sh dev:compilemessages`**
    *   **作用:** 将文本格式的 `.po` 文件编译成 Django 使用的二进制 `.mo` 文件。
    *   **使用时机:** 在运行 `dev:makemessages` 或从代码库拉取了翻译更新之后使用。

*   **`./run.sh dev:test`**
    *   **作用:** 运行项目的自动化测试套件。
    *   **使用时机:** 在**开发新功能的过程中**频繁使用，以确保你的更改没有破坏现有功能。

---
