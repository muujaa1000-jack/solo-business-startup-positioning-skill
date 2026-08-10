# 一人公司起步定位访谈

`interview-solo-business-startup-positioning` 是一个 Agent Skill，帮助希望在商业化验证前形成并比较一人公司、独立项目或副业方向的人。

它通过一次只问一个问题的访谈，把真实经历、能力、资源、兴趣、约束和可触达人群整理为两到三个定位假设；它不替代商业化验证。

## 适合谁

适合完全没有方向、方向太多，或已有模糊方向但需要先形成和比较的人。若你已有明确项目，只需验证需求、付款、获客或交付经济性，请改用[solo-business-validation-skill](https://github.com/muujaa1000-jack/solo-business-validation-skill)。

## 安装

请使用你的 Agent Skills 宿主提供的安装方式安装本仓库。仓库根目录就是 Skill 目录；调用名称和 frontmatter 中的名称均为 `interview-solo-business-startup-positioning`。

具体安装步骤以宿主官方文档为准。本仓库提供标准的 `SKILL.md`、元数据和参考资料；这不表示已经在所有宿主上实测安装或运行行为。

## 开始访谈

请让宿主使用此 Skill，例如：

```text
请使用一人公司起步定位访谈。一次只问我一个问题，帮我找到可以优先验证的方向。
```

若宿主支持按名称调用，也可以使用：

```text
$interview-solo-business-startup-positioning
```

## 访谈会产出什么

- 对经历、能力、资源、兴趣、可触达人群和现实约束的边界清晰整理；
- 两到三个可比较的定位假设；
- 由使用者明确选择、组合或保留候选；
- 七个同级部分的最终交接内容，以及下一阶段使用的交接卡。

可查看[完整虚构定位示例](examples/complete-positioning.md)和[证据不足示例](examples/insufficient-evidence.zh-CN.md)。公开的全新上下文提示与复核方法见[行为评测](evals/README.md)。它们是书面示例和静态评测规范，不是模型行为已经通过验证的证明。

## 商业化验证器

交接卡是`待验证假设`，不等于市场已经证明。请把它交给[solo-business-validation-skill](https://github.com/muujaa1000-jack/solo-business-validation-skill)，验证需求、付款、获客和交付经济性。本 Skill 不批准直接完整开发，也不执行联系、发布、收费或花钱。

## 兼容性与验证边界

本仓库遵循公开 Agent Skills 目录模式：`SKILL.md`、可选的 `agents/` 元数据文件和被引用的说明资料。它面向愿意解释此模式的 Codex、Claude Code 和其他宿主；目录结构相似不等于已声明某个宿主或版本安装成功、行为稳定或兼容。

安装前请阅读宿主当前官方说明：[Codex Skills](https://developers.openai.com/codex/skills/)、[Claude Code](https://docs.anthropic.com/en/docs/claude-code) 和 [Agent Skills specification](https://agentskills.io/specification)。

可运行以下静态仓库契约测试：

```text
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
```

这些测试只检查书面规则和仓库产物。若有带日期的模型或宿主观察，应记录在 `docs/validation.md`；它们不证明完整多轮稳定性、跨模型表现或真实商业结果。

## 证据边界

五种信息状态只能是`材料已核实`、`用户陈述`、`外部推断`、`待验证假设`和`未知`。Skill 不得编造客户、市场需求、价格、渠道、结果或个人优势。完成定位访谈不等于市场已验证，也不承诺收入或长期适配。

## 开发与发布

贡献应保持首轮只问一个问题、五种信息状态、候选决策路径和七部分最终交接不变。改变行为前先新增或更新契约测试或评测。详见[CONTRIBUTING.md](CONTRIBUTING.md)、[SECURITY.md](SECURITY.md) 和 [CHANGELOG.md](CHANGELOG.md)；当前源码版本见[VERSION](VERSION)。

使用以下命令生成确定性发布制品，并对照源码重新生成的规范制品进行复验：

```text
python -X utf8 scripts/package.py --output-dir dist
python -X utf8 scripts/verify_artifacts.py dist/interview-solo-business-startup-positioning-0.1.0.zip dist/interview-solo-business-startup-positioning-0.1.0.skill
```

### Release 制品

发布工作流已配置为在 `v0.1.0` 时发布以下三个制品：

- `interview-solo-business-startup-positioning-0.1.0.zip`
- `interview-solo-business-startup-positioning-0.1.0.skill`
- `SHA256SUMS`

在远端 GitHub Release 及下载后的三个制品完成核验前，不得把本次发布写成已完成。

## 许可证

[MIT](LICENSE)
