- **改完就把下面的checkbox checked**

Mar26.2026 13:56
- [x] 现在我无法清除已有的docker,就算我./synapse clean都不行。我知道了，你是用docker:down，这个表达很docker,但是对于陌生的user,会想象down只是stop or pause and will not be clean and remove the container and even should we need to create the image remover?
- [x] 现在的README.md还没有更新，都是旧的
- [x] 在frontend的顶部一直都是这个错误的版本信息：v0.9.0-alpha admin admin，我希望它可以是动态的
- [x] Obsidian Sync Phase 5.3–5.5 — DB-Primary + Obsidian-Mirror，其实不需要列出这是哪一个版本的代码才有的功能。
- [x] Uncomment the line below AND set OBSIDIAN_VAULT_PATH in .env.docker，我希望不要是这样的做法，能不能动态控制呢？除非compose机制无法做动态条件选择，否则我希望只要有这个env，就默认打开挂载，是one move not two
- [x] 而且我按照你说的去挂host volume，然后frontend出现错误：Failed to save vault path: Path does not exist or is not a directory: /mnt/2tb_wd_purpleSurveillance_hdd/system-redirection/Development/documents/PARA-Vault-new

