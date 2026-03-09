"""
AI diary service — synthesizes fragments into a diary entry.
Supports mock mode (no API key needed) and real Claude API mode.
"""

from __future__ import annotations

import logging
from datetime import date

from config import Config
from models import Fragment

logger = logging.getLogger(__name__)

# Singleton
_instance: "DiaryAIService | None" = None


def get_claude() -> "DiaryAIService":
    global _instance
    if _instance is None:
        _instance = DiaryAIService(Config.from_env())
    return _instance


SYSTEM_PROMPT = """\
你是一位温暖且文笔细腻的私人日记作家。用户一天中会随手记录各种碎片——
文字、语音转录、照片描述。你的任务是把这些碎片整合成一篇连贯、有温度的日记。

规则：
1. 用第一人称（"我"）书写，保持用户的语气和情感。
2. 按照时间线自然串联，但不要生硬地列流水账。
3. 捕捉情绪和细节，适当添加过渡和感悟。
4. 如果有照片描述，自然融入文字里。
5. 输出 Markdown 格式，标题为日期。
6. 字数在 200-800 字之间，视碎片量而定。
"""


class DiaryAIService:
    def __init__(self, config: Config):
        self.mock_mode = not config.claude_api_key
        self.model = config.claude_model

        if not self.mock_mode:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.claude_api_key)
            logger.info("AI Service: Claude API mode ✓")
        else:
            self.client = None
            logger.info("AI Service: Mock mode (no CLAUDE_API_KEY set)")

    async def synthesize_diary(
        self, fragments: list[Fragment], diary_date: date
    ) -> str:
        """Turn a list of fragments into a coherent diary entry."""
        if not fragments:
            return ""

        if self.mock_mode:
            return self._mock_diary(fragments, diary_date)

        user_message = self._build_prompt(fragments, diary_date)
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text

    async def describe_photo(self, image_url: str) -> str:
        """Use Claude's vision to describe a photo fragment."""
        if self.mock_mode:
            return "[照片 — 一张记录生活瞬间的照片]"

        import anthropic
        message = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "url", "url": image_url},
                        },
                        {
                            "type": "text",
                            "text": "用中文简洁描述这张照片的内容和氛围，2-3 句话即可，用于日记写作素材。",
                        },
                    ],
                }
            ],
        )
        return message.content[0].text

    # ---- Mock mode ----

    @staticmethod
    def _mock_diary(fragments: list[Fragment], diary_date: date) -> str:
        """Generate a simple template diary when no AI API is available."""
        lines = [f"# {diary_date.isoformat()} 的日记\n"]
        lines.append(f"今天记录了 {len(fragments)} 个生活碎片。\n")

        for i, f in enumerate(fragments, 1):
            time_str = f.created_at.strftime("%H:%M") if f.created_at else ""
            tag = {"text": "📝", "voice": "🎙️", "photo": "📷"}.get(f.type, "💬")

            if f.content:
                lines.append(f"**{time_str}** {tag} {f.content}\n")

        lines.append("\n---\n*（Mock 模式 — 接入 Claude API 后将生成更自然的日记）*")
        return "\n".join(lines)

    # ---- Prompt building ----

    @staticmethod
    def _build_prompt(fragments: list[Fragment], diary_date: date) -> str:
        lines = [f"以下是 {diary_date.isoformat()} 的生活碎片，请帮我整合成日记：\n"]

        for i, f in enumerate(fragments, 1):
            time_str = f.created_at.strftime("%H:%M") if f.created_at else "??:??"
            tag = {"text": "📝", "voice": "🎙️", "photo": "📷"}.get(f.type, "💬")

            lines.append(f"【碎片 {i}】{tag} {time_str}")
            if f.content:
                lines.append(f.content)
            lines.append("")

        return "\n".join(lines)
