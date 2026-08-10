# 一人公司起步定位访谈

这是一个帮助普通人从零梳理一人公司方向的Codex Skill。它不会先要求你准备商业计划，而是通过一次只问一个问题的访谈，从真实经历、能力、资源、兴趣、约束和可触达人群中寻找起步定位。

## 适合谁

适合完全没有方向、方向太多难以选择，或者知道自己会什么但说不清客户、问题和产品的人。

如果你已经有明确项目，只想判断是否值得继续投入，请改用一人公司商业化验证Skill。

## 如何开始

告诉Codex：

> 请用一人公司起步定位访谈，一次问我一个问题，帮我找到可以优先验证的一人公司方向。

也可以直接调用：

```text
$interview-solo-business-startup-positioning
```

## 安装

让Codex安装本仓库：

```text
使用 $skill-installer 安装 https://github.com/muujaa1000-jack/solo-business-startup-positioning-skill
```

仓库根目录就是标准Skill目录，名称和frontmatter中的`name`均为`interview-solo-business-startup-positioning`。

## 会得到什么

- 对经历、能力、资源、兴趣、可触达人群和现实约束的整理；
- 两到三个可以比较的候选定位；
- 身份、客户、问题、价值、产品、收费、获客、交付和内容定位；
- 由你确认的定位选择；
- 可以直接交给商业化验证器的定位交接卡。

## 能力边界

输出是`待验证假设`，不等于市场需求已经得到证明，也不承诺一定赚钱。Skill不会替你编造优势、客户、价格或需求，也不会替你联系客户、发布内容、收费或花钱。

定位形成后，如果需要判断需求、付款、获客和交付经济性，请继续使用[一人公司商业化验证Skill](https://github.com/muujaa1000-jack/solo-business-validation-skill)。

## 验证

本仓库包含文本契约测试和完整的[验证记录](docs/validation.md)：

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

验证记录中的行为证据只覆盖所列首轮场景，不证明完整多轮访谈、跨模型稳定性或真实商业需求。

## 许可证

[MIT](LICENSE)
