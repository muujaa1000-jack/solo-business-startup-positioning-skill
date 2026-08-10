# 一人公司起步定位访谈 Skill 开源同级补齐设计

日期：2026-08-10

## 背景

当前仓库已经公开核心 Skill、中文 README、24 项文本契约测试、历史验证记录和一个手工生成的 ZIP。核心访谈规则可用，但与 `solo-business-validation-skill` 相比，仍缺少双语文档、公开示例、行为评测、仓库校验、确定性打包、CI、自动 Release、版本管理和维护规范。

本次目标不是重写访谈逻辑，而是把仓库补到与现有商业化验证 Skill 相同的开源工程成熟度。

## 目标

- 建立中英文一致的安装、使用、兼容性和证据边界说明。
- 提供完全虚构或复合化的完整示例与不足证据示例。
- 提供公开、可重复运行的行为评测定义，并区分静态契约与真实模型行为证据。
- 建立无第三方运行依赖的仓库校验、确定性打包和制品复验工具。
- 在 GitHub Actions 中自动运行多版本 Python 测试、候选制品构建和标签发布。
- 发布 `v0.1.0`，包含 ZIP、`.skill` 和 `SHA256SUMS`。

## 非目标

- 不修改 `solo-business-validation-skill` 仓库。
- 不改变“起步定位访谈”和“商业化验证”的阶段分工。
- 不因为工程对齐而改写已经通过验证的访谈核心规则。
- 不声称完整多轮、所有模型或真实商业结果已经验证。
- 不增加运行时第三方依赖，也不建立跨仓库公共工具包。

## 方案

采用同级镜像式补齐：沿用成熟仓库的公开结构、测试思路、打包接口和 GitHub 发布模式，但所有文档、示例、评测字段和契约均针对定位访谈重新设计。两个仓库保持相似维护体验，同时彼此独立发布。

## 目标结构

```
README.md
README.zh-CN.md
SKILL.md
agents/openai.yaml
references/interview-guide.md
references/output-contract.md
examples/complete-positioning.md
examples/insufficient-evidence.zh-CN.md
evals/README.md
evals/cases.json
scripts/__init__.py
scripts/validate.py
scripts/package.py
scripts/verify_artifacts.py
tests/test_skill.py
tests/test_repository_contract.py
tests/test_packaging.py
.github/workflows/ci.yml
.github/workflows/release.yml
.gitattributes
.gitignore
VERSION
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
LICENSE
docs/validation.md
docs/superpowers/specs/2026-08-10-open-source-parity-design.md
docs/superpowers/plans/2026-08-10-open-source-parity.md
```

## 公开文档

- `README.md` 为英文主说明，`README.zh-CN.md` 为同结构中文说明。
- 两份 README 均覆盖适用对象、安装、调用、输出、与商业化验证 Skill 的分工、兼容性、验证边界、开发和发布。
- Codex、Claude Code 和开放 Agent Skills 格式只声明文档与目录层面的兼容性；没有日期行为结果时，不声称特定宿主或模型已验证。
- `CHANGELOG.md` 使用 Keep a Changelog 结构，初始公开版本为 `0.1.0`。
- `CONTRIBUTING.md` 要求行为变化先更新评测或契约，示例必须虚构或复合化。
- `SECURITY.md` 使用 GitHub 私密漏洞报告链接，覆盖凭据泄露、目录穿越、危险归档和提示注入风险。

## 示例与评测

### 示例

- 英文完整示例：从完全没有方向开始，经过逐轮信息收集、候选比较和使用者选择，生成一个明确标为待验证假设的交接卡。
- 中文不足证据示例：使用者要求立即给唯一方向，但没有回答过访谈问题；输出只问一个问题。若使用者在回答至少一轮后结束，才提供阶段性假设、依据、最大缺口和最值得补充的一项信息。
- 示例不得包含真实客户、公司、账号、交易、联系方式或可识别经营信息。

### 评测

`evals/cases.json` 至少包含五个公开虚构场景：

1. 完全没有方向；
2. 方向太多并要求助手直接选择；
3. 刚学会 AI 工具并要求写成核心优势；
4. 否定全部候选后返回机会线索；
5. 明确保留多个方向时生成独立交接子卡。

每个用例包含 `id`、`prompt`、`stage` 和 `expected_behaviors`。自动测试只校验评测模式和书面契约；真实模型行为必须在全新上下文中运行并单独发布有日期结果。

## 仓库校验

`scripts/validate.py` 负责：

- 检查所有必需文件；
- 检查 `VERSION` 为稳定语义化版本；
- 检查 `SKILL.md` 只有 `name` 和 `description` 两个 frontmatter 字段、触发描述以 `Use when` 开头且不超过 1024 字符；
- 检查 Skill 名称、界面调用名和引用文件一致；
- 检查两个 README 的官方兼容性链接；
- 检查评测 JSON 结构、用例数量和必需字段；
- 扫描私钥、GitHub token、疑似嵌入密钥、用户主目录、本机仓库路径和无效 UTF-8；
- 忽略 `.git`、`dist`、临时输出和虚拟环境。

## 确定性打包

运行文件集合固定为：

- `LICENSE`
- `SKILL.md`
- `agents/openai.yaml`
- `references/interview-guide.md`
- `references/output-contract.md`

`scripts/package.py` 使用固定 ZIP 时间戳、固定排序、统一权限和 LF 换行，生成：

- `interview-solo-business-startup-positioning-0.1.0.zip`
- `interview-solo-business-startup-positioning-0.1.0.skill`
- `SHA256SUMS`

ZIP 与 `.skill` 必须逐字节一致。`scripts/verify_artifacts.py` 拒绝绝对路径、反斜杠、空路径段、`.`、`..`、额外文件、缺失文件、源码哈希差异、无效 UTF-8 和校验和不一致。

当前提交到源码仓库的 `dist/interview-solo-business-startup-positioning.zip` 和根目录 `SHA256SUMS` 将删除。制品只由本地构建、CI 候选制品和 GitHub Release 生成，防止源码长期携带过期包。

## 自动化

### CI

- 在 `push` 到 `main` 和所有 pull request 上运行。
- Python 3.10、3.12、3.14 分别执行全部测试和仓库校验。
- Python 3.12 构建两次候选制品，验证确定性、内容和校验和，并上传 7 天候选制品。
- GitHub Actions 使用固定提交 SHA，权限默认为只读。

### Release

- 仅响应 `v*` 标签。
- 标签必须等于 `v` 加 `VERSION`。
- 重新运行测试、仓库校验、打包和制品复验。
- 以写入内容的最小权限创建或更新 GitHub Release。
- `v0.1.0` 发布后，远端 Release 必须真实包含 ZIP、`.skill` 和 `SHA256SUMS`。

## 测试策略

- 保留现有访谈契约测试，防止工程补齐改变首轮形状、五种信息状态、候选决策路径、准备门槛和交接卡。
- 新增仓库契约测试，先以缺失文件、错误版本、评测缺口和隐私扫描断言进入 RED，再补最小文件和校验逻辑进入 GREEN。
- 新增打包测试，先断言确定性、运行文件清单、LF、路径安全和校验和，再实现脚本。
- 对示例和评测使用静态契约测试；已有有日期首轮行为记录继续保留，不伪造新的模型运行结论。

## 安全与隐私

- 所有公开业务内容必须为虚构或复合案例。
- 校验器扫描文本文件和发布包；发现密钥、私钥、用户主目录或本机路径时失败。
- 打包器不跟随动态文件发现，只打包显式白名单。
- Release 工作流不接触客户数据、付款系统或外部业务动作。
- 本项目只发布指令、文档、测试和本地工具，不安装到用户级 Skill 目录。

## 验收标准

- 全部现有和新增测试退出状态为 0。
- `python scripts/validate.py` 退出状态为 0。
- 源目录和解压后的 ZIP、`.skill` 均通过官方 Skill 快速校验。
- 两次构建的 ZIP、`.skill` 和 `SHA256SUMS` 逐字节一致。
- `python scripts/verify_artifacts.py dist/*.zip dist/*.skill` 退出状态为 0。
- PR 的全部 GitHub Actions 检查通过。
- 合并后 `main` 与预期提交树一致。
- 标签 `v0.1.0` 指向已验证的 `main` 提交。
- GitHub Release `v0.1.0` 包含三个制品且校验和与下载内容一致。
- 新旧仓库均保持公开；原商业化验证仓库没有文件变化。

## 发布顺序

1. 在隔离工作树按 TDD 完成仓库契约、文档、示例和评测。
2. 按 TDD 完成验证、打包和制品复验脚本。
3. 增加 CI、Release、版本和维护文件并运行完整本地验证。
4. 请求整分支复审，修复所有重要问题。
5. 推送发布分支并创建 PR。
6. 等待并核验 GitHub CI。
7. 合并 PR 后同步本地 `main`。
8. 创建并推送 `v0.1.0` 标签。
9. 等待 Release 工作流完成并下载复验三个公开制品。
