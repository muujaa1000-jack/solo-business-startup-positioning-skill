from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT

EXPECTED_TRIGGER_DESCRIPTION = (
    "Use when a person wants to start a solo business, independent project, or side "
    "business and has no direction, too many directions, or only a vague direction "
    "that needs formation and comparison before commercial validation; do not use "
    "for a clear existing project that only needs demand, payment, acquisition, or "
    "delivery validation."
)

READINESS_GATES = [
    "当前状态和访谈目标已明确；",
    "至少有一条创始人经历、能力或资源线索；",
    "至少有一类可描述具体情境的人群；",
    "至少有一个具体问题或明确标为`未知`；",
    "已形成两到三个候选定位；",
    "使用者已经选择一条、组合，或明确要求保留多个方向。",
]


class SoloBusinessStartupPositioningSkillTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (SKILL_DIR / relative_path).read_text(encoding="utf-8")

    def test_required_files_exist(self) -> None:
        expected = {
            "README.md",
            "SKILL.md",
            "agents/openai.yaml",
            "references/interview-guide.md",
            "references/output-contract.md",
        }
        actual = {
            path.relative_to(SKILL_DIR).as_posix()
            for path in SKILL_DIR.rglob("*")
            if path.is_file()
        }
        self.assertTrue(expected.issubset(actual))

    def test_metadata_matches_name_and_invocation(self) -> None:
        skill = self.read("SKILL.md")
        metadata = self.read("agents/openai.yaml")
        self.assertIn("name: interview-solo-business-startup-positioning", skill)
        self.assertIn('display_name: "一人公司起步定位访谈"', metadata)
        self.assertIn("$interview-solo-business-startup-positioning", metadata)

    def test_trigger_description_routes_only_direction_formation(self) -> None:
        skill = self.read("SKILL.md")
        description = next(
            line.removeprefix("description: ")
            for line in skill.splitlines()
            if line.startswith("description: ")
        )
        self.assertEqual(EXPECTED_TRIGGER_DESCRIPTION, description)
        for positive_trigger in (
            "has no direction",
            "too many directions",
            "only a vague direction",
            "formation and comparison before commercial validation",
        ):
            self.assertIn(positive_trigger, description)

    def test_trigger_description_excludes_clear_project_validation(self) -> None:
        skill = self.read("SKILL.md")
        description = next(
            line.removeprefix("description: ")
            for line in skill.splitlines()
            if line.startswith("description: ")
        )
        self.assertIn(
            "do not use for a clear existing project that only needs demand, payment, "
            "acquisition, or delivery validation",
            description,
        )
        self.assertNotIn("uncertainty about founder fit", description)

    def test_skill_enforces_single_question_interview_turns(self) -> None:
        text = self.read("SKILL.md")
        for phrase in (
            "一次只问一个问题",
            "可选的一句复述",
            "一个问题",
            "停止并等待回答",
            "当前最大信息缺口",
        ):
            self.assertIn(phrase, text)

    def test_first_turn_shape_excludes_process_refusal_and_transition_prose(self) -> None:
        text = self.read("SKILL.md") + self.read("references/interview-guide.md")
        for phrase in (
            "首轮没有可复述的既有回答时，只输出一个问题，然后停止",
            "只能复述或确认使用者在上一轮回答中提供的信息",
            "不添加流程说明、拒绝说明或过渡语",
        ):
            self.assertIn(phrase, text)

    def test_immediate_conclusion_pressure_does_not_bypass_first_turn_shape(self) -> None:
        text = self.read("SKILL.md") + self.read("references/interview-guide.md")
        for phrase in (
            "首轮规则不因使用者要求立即结论、唯一方向或跳过访谈而改变",
            "只有在使用者至少回答过一个访谈问题后，阶段性结束规则才可用",
            "首次请求要求立即结束时，仍只输出一个问题",
        ):
            self.assertIn(phrase, text)

    def test_single_question_is_the_entire_final_unit(self) -> None:
        text = self.read("SKILL.md") + self.read("references/interview-guide.md")
        for phrase in (
            "单个问题必须是回复的最后一个单元",
            "问号`？`必须是回复去除空白后的最后一个字符",
            "问号后不添加指令、示例、澄清、过渡语或第二个句子",
            "可选复述只能出现在问题之前",
        ):
            self.assertIn(phrase, text)

    def test_one_question_has_one_decision_gap_and_answer_slot(self) -> None:
        for relative_path, question_mark_phrase in (
            ("SKILL.md", "不能仅以一个`？`判断为一个问题"),
            ("references/interview-guide.md", "不能仅以一个中文问号判断为一个问题"),
        ):
            text = self.read(relative_path)
            for phrase in (
                "一个问题只对应一个决策缺口和一个回答槽位",
                question_mark_phrase,
                "不得把目标人、问题、行动、结果、证据等多个独立回答字段压进同一句",
                "追问具体案例时，每轮只从事件、行动、结果、材料中选择一个当前最大缺口",
            ):
                self.assertIn(phrase, text)

    def test_skill_uses_exactly_five_evidence_states(self) -> None:
        states = (
            "材料已核实",
            "用户陈述",
            "外部推断",
            "待验证假设",
            "未知",
        )
        exact_contract = "信息状态只允许以下五种，不能新增第六种：" + "、".join(
            f"`{state}`" for state in states
        ) + "。"
        for relative_path in ("SKILL.md", "references/output-contract.md"):
            self.assertIn(exact_contract, self.read(relative_path))

    def test_choose_one_enters_final_output(self) -> None:
        text = self.read("SKILL.md") + self.read("references/interview-guide.md")
        self.assertIn("选择一条后进入最终输出", text)

    def test_combine_enters_final_output(self) -> None:
        text = self.read("SKILL.md") + self.read("references/interview-guide.md")
        self.assertIn("组合候选后进入最终输出", text)

    def test_explicitly_retaining_multiple_enters_final_output(self) -> None:
        text = self.read("SKILL.md") + self.read("references/interview-guide.md")
        self.assertIn("明确保留多个方向后进入最终输出", text)

    def test_rejecting_all_candidates_returns_to_generation_without_handoff(self) -> None:
        text = self.read("SKILL.md") + self.read("references/interview-guide.md")
        for phrase in (
            "否定全部候选后回到机会线索和候选生成",
            "不生成最终报告或定位交接卡",
        ):
            self.assertIn(phrase, text)

    def test_final_output_requires_all_exact_readiness_gates(self) -> None:
        guide = self.read("references/interview-guide.md")
        gate_block = guide.split("## 进入最终输出的条件", 1)[1]
        actual_gates = [
            line.removeprefix("- ")
            for line in gate_block.splitlines()
            if line.startswith("- ")
        ]
        self.assertEqual(READINESS_GATES, actual_gates)

    def test_interview_guide_avoids_compound_questions(self) -> None:
        text = self.read("references/interview-guide.md")
        for question in (
            "你已有的模糊方向是什么？",
            "其中最不确定的是什么？",
            "你每周能投入多少时间？",
            "你能承受怎样的资金压力？",
            "你能承受怎样的交付压力？",
            "他们现在通常如何解决这个问题？",
            "现有解决方式哪里最麻烦、昂贵、缓慢或不稳定？",
        ):
            self.assertIn(question, text)
        for compound_question in (
            "你已有的模糊方向是什么，最不确定的又是什么？",
            "你每周能投入多少时间，能够承受怎样的资金和交付压力？",
            "现在他们如何解决，哪里最麻烦、昂贵、缓慢或不稳定？",
        ):
            self.assertNotIn(compound_question, text)

    def test_interview_guide_questions_end_with_one_question_mark_and_choice_is_explicit(self) -> None:
        guide = self.read("references/interview-guide.md")
        question_lines = [line.strip() for line in guide.splitlines() if "？" in line]
        self.assertTrue(question_lines)
        for line in question_lines:
            self.assertEqual(1, line.count("？"), line)
            self.assertTrue(line.rstrip().endswith("？"), line)

        choice_prompt = "面对这些候选定位，你决定选择一条、组合、明确保留多个方向，还是全部否定并回到机会线索？"
        normalized_questions = [
            line.removeprefix("- ").removeprefix("> ") for line in question_lines
        ]
        self.assertIn(choice_prompt, normalized_questions)
        for option in ("选择一条", "组合", "明确保留多个方向", "全部否定并回到机会线索"):
            self.assertIn(option, choice_prompt)

    def test_output_contract_contains_exact_semantic_sections(self) -> None:
        text = self.read("references/output-contract.md")
        headings = [
            line.removeprefix("### ").strip()
            for line in text.splitlines()
            if line.startswith("### ")
        ]
        self.assertEqual(
            [
                "当前访谈结论",
                "创始人底盘",
                "机会线索",
                "候选定位比较",
                "使用者选择",
                "完整定位组合",
                "商业验证交接卡",
            ],
            headings,
        )

    def test_output_contract_allows_exactly_three_final_decision_states(self) -> None:
        text = self.read("references/output-contract.md")
        conclusion_block = text.split("### 当前访谈结论", 1)[1].split(
            "### 创始人底盘", 1
        )[0]
        decision_states = [
            line.removeprefix("- `").split("`", 1)[0]
            for line in conclusion_block.splitlines()
            if line.startswith("- `")
        ]
        self.assertEqual(
            [
                "已形成一个优先定位假设",
                "已组合形成一个定位假设",
                "建议保留多个方向进入验证",
            ],
            decision_states,
        )

    def test_output_contract_covers_nine_positioning_dimensions(self) -> None:
        text = self.read("references/output-contract.md")
        for dimension in (
            "身份定位",
            "客户定位",
            "问题定位",
            "价值定位",
            "产品或服务定位",
            "收费定位",
            "获客定位",
            "交付定位",
            "内容或品牌定位",
        ):
            self.assertIn(dimension, text)

    def test_handoff_card_is_self_contained_and_bounded(self) -> None:
        text = self.read("references/output-contract.md")
        for phrase in (
            "目标付费者及其具体处境",
            "当前替代方式",
            "最小产品或服务设想",
            "收费、获客和交付假设",
            "三个最可能改变定位的未知项",
            "优先检查的一个假设",
        ):
            self.assertIn(phrase, text)
        self.assertIn("不等于市场已验证", text)

    def test_retained_multiple_directions_get_independent_handoff_subcards(self) -> None:
        text = self.read("references/output-contract.md")
        for phrase in (
            "保留多个方向时",
            "每个保留方向分别生成一张独立的交接子卡",
            "不得把多个方向合并在同一张子卡",
        ):
            self.assertIn(phrase, text)

    def test_readme_is_user_facing_and_separates_validation(self) -> None:
        text = self.read("README.md")
        for phrase in ("适合谁", "如何开始", "会得到什么", "能力边界"):
            self.assertIn(phrase, text)
        self.assertIn("一次只问一个问题", text)
        self.assertIn("商业化验证", text)

    def test_skill_does_not_force_a_business_format_or_external_action(self) -> None:
        text = self.read("SKILL.md")
        for phrase in (
            "不默认AI是核心能力或正确方向",
            "不默认自媒体是正确产品形态",
            "不默认内容是正确产品形态",
            "不默认课程是正确产品形态",
            "不默认咨询是正确产品形态",
            "不默认软件是正确产品形态",
            "不执行联系客户",
            "不执行发布内容",
            "不执行收费",
            "不执行花钱",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
