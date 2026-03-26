- **改完就把下面的checkbox checked**

Mar26.2026 14:50
- [x] docker:up的时候，第一次执行会遇到如下报错，已遇到两次，确认是否是bug，并解决之：
    ```bash
                                                                                                                    0.0s
    ------
    > [nginx internal] load metadata for docker.io/library/node:20-alpine:
    ------
    [+] up 0/2
    ⠙ Image synapseerpgit-backend Building                                                                                                                                                  27.4s
    ⠙ Image synapseerpgit-nginx   Building                                                                                                                                                  27.4s
    Dockerfile.nginx:14

    --------------------

    12 |

    13 |     # --- Stage 1: Build Vue 3 SPA ---

    14 | >>> FROM node:20-alpine AS builder

    15 |

    16 |     WORKDIR /app

    --------------------

    target nginx: failed to solve: failed to do request: Head "https://docker.mirrors.ustc.edu.cn/v2/library/node/manifests/20-alpine?ns=docker.io": EOF


    ```
- [x] 我的00_INDEX.md中原先有大量具体的每一个Phase的子任务，因为之前要写入给AI Agent的留言，合并的时候，AI删除了里面的内容，请你翻阅git，去查找这里面被删除的部分，已有的部分也不删除。
- [x] 我的00_INDEX.md里的内容在增多，我希望你把这个文档做成一个真正的index only。将对AI说的具体的要求，单独到一个文档里。
- [x] 我很不喜欢现在的docs目录，逻辑性很弱，请你提个方案，把docs目录重写，例如我们按照层级，顶层Lv-1是00_INDEX.md，然后分几个部分：给AI Agent阅读的部分；介绍当前项目中的技术亮点（或精华点）的一块；介绍当前工作进度（包括未来还可以做哪些，已经做过哪些，每一个具体计划）的一块。我目前想到的就是这样，请你先按照我说的来重构，你可以改我docs里面具体md的内容，把过时的扔到archived里面去。我最后看见外面的md都要是与我当前项目一一对应完全匹配的，尽可能精炼，但不能敷衍潦草。
- [x] frontend的右上角的版本号当前居然是v0.5.0-alpha，胡扯啊，我现在早就已经是新版本了。请修改确认。
- [ ]



Mar26.2026 13:56
- [x] 现在我无法清除已有的docker,就算我./synapse clean都不行。我知道了，你是用docker:down，这个表达很docker,但是对于陌生的user,会想象down只是stop or pause and will not be clean and remove the container and even should we need to create the image remover?
- [x] 现在的README.md还没有更新，都是旧的
- [x] 在frontend的顶部一直都是这个错误的版本信息：v0.9.0-alpha admin admin，我希望它可以是动态的
- [x] Obsidian Sync Phase 5.3–5.5 — DB-Primary + Obsidian-Mirror，其实不需要列出这是哪一个版本的代码才有的功能。
- [x] Uncomment the line below AND set OBSIDIAN_VAULT_PATH in .env.docker，我希望不要是这样的做法，能不能动态控制呢？除非compose机制无法做动态条件选择，否则我希望只要有这个env，就默认打开挂载，是one move not two
- [x] 而且我按照你说的去挂host volume，然后frontend出现错误：Failed to save vault path: Path does not exist or is not a directory: /mnt/2tb_wd_purpleSurveillance_hdd/system-redirection/Development/documents/PARA-Vault-new

