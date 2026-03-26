- **改完就把下面的checkbox checked**

Mar26.2026 16:15
- [x] 我现在README里对版本的显示是动态的，但是你frontend里的代码加载版本却是写死的，我要求能够把版本唯一的写在一个地方，所有需要的文件或代码都去加载那个地方，唯一化。
- [x] frontend目前只有日/周/月，没有年，还有我切换到月，就每次都是显示2023～2024,很奇怪。你帮我加入年，而且正确识别年份为当前运行的服务器所在的timezone。
- [x] 我为了安全，希望从obsidian vault进来的所有projects,能够按照tags来过滤，当然，默认是all，或者我也可以输入tags，有这个tags的我才拉进来。
- [x] 我尝试export to vault，报错：Export failed: [Errno 30] Read-only file system: '/vault/1_PROJECT/2025.15_Project_AI_Quantitative_HardCore_Demo/tasks/task_测试看看有没有.md.tmp'这是为啥？
- [x] 当前以db为绝对核心，当然我也希望在obsidian sync这个page里显示当前obsidian有几个projects，几个tasks, 当然，不要是消耗大量cpu和内存。你看看能做吗？必须消耗轮训的话告诉我，我来做选择是否要做。


Mar26.2026 15:30
- [x] .env.docker加入gitignore
- [x] 我希望docs目录下顶层只有00_INDEX.md，我要在hierarchy上也体现内容之间的层级关系和逻辑。
- [x] 00_INDEX.md的navigation居然还有9个大类，实在太多了，我的要求是做成多叉树，最多不超过4个大类，可以有子类。然后在文件命名和文件夹的设置上，也体现层级关系。就按照我之前说的：三个大类，to ai/dev progress/项目亮点。
- [x] NEED_TO_DO.md也不能放在顶层，看能不能归入其中一大类里。
- [x] 你在00_INDEX里做3张表格，每张就是体现一个大类。非常清晰。
- [x] 我看见虽然我写了ai agent不要全盘扫描，但是你一开始context=0的时候还是查看了大量的src files,然后写了好几个长篇的md到/tmp下面，是不是代表我的prompt对你优先级不够，你并没有按照我的说法来做呢？我需不需要整个claude.md重写，甚至删掉它呢？因为我用00_INDEX来取代？看我的整个00_INDEX的文档集合就够了，根本不需要看代码（实际解决才需要直接进去）


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




Mar26.2026 13:56
- [x] 现在我无法清除已有的docker,就算我./synapse clean都不行。我知道了，你是用docker:down，这个表达很docker,但是对于陌生的user,会想象down只是stop or pause and will not be clean and remove the container and even should we need to create the image remover?
- [x] 现在的README.md还没有更新，都是旧的
- [x] 在frontend的顶部一直都是这个错误的版本信息：v0.9.0-alpha admin admin，我希望它可以是动态的
- [x] Obsidian Sync Phase 5.3–5.5 — DB-Primary + Obsidian-Mirror，其实不需要列出这是哪一个版本的代码才有的功能。
- [x] Uncomment the line below AND set OBSIDIAN_VAULT_PATH in .env.docker，我希望不要是这样的做法，能不能动态控制呢？除非compose机制无法做动态条件选择，否则我希望只要有这个env，就默认打开挂载，是one move not two
- [x] 而且我按照你说的去挂host volume，然后frontend出现错误：Failed to save vault path: Path does not exist or is not a directory: /mnt/2tb_wd_purpleSurveillance_hdd/system-redirection/Development/documents/PARA-Vault-new

