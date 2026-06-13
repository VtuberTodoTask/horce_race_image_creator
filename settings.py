"""設定の保存・読み込みモジュール."""

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_SETTINGS_PATH = "settings.json"


@dataclass
class ParticipantSetting:
    """参加者1人分の設定."""

    name: str = ""
    avatar_path: str = ""


@dataclass
class BackgroundSetting:
    """背景画像の設定."""

    image_path: str = ""
    size_mode: str = "auto"  # "auto" | "background" | "custom"
    custom_width: int = 1280
    custom_height: int = 720


@dataclass
class AppSettings:
    """アプリケーション全体の設定."""

    participant_count: int = 4
    participants: list[ParticipantSetting] = field(default_factory=list)
    output_path: str = "output.png"
    background: BackgroundSetting = field(default_factory=BackgroundSetting)

    def to_dict(self) -> dict:
        return {
            "participant_count": self.participant_count,
            "participants": [
                {"name": p.name, "avatar_path": p.avatar_path}
                for p in self.participants
            ],
            "output_path": self.output_path,
            "background": {
                "image_path": self.background.image_path,
                "size_mode": self.background.size_mode,
                "custom_width": self.background.custom_width,
                "custom_height": self.background.custom_height,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        participants = [
            ParticipantSetting(
                name=p.get("name", ""),
                avatar_path=p.get("avatar_path", ""),
            )
            for p in data.get("participants", [])
        ]
        bg_data = data.get("background", {})
        background = BackgroundSetting(
            image_path=bg_data.get("image_path", ""),
            size_mode=bg_data.get("size_mode", "auto"),
            custom_width=bg_data.get("custom_width", 1280),
            custom_height=bg_data.get("custom_height", 720),
        )
        return cls(
            participant_count=data.get("participant_count", 4),
            participants=participants,
            output_path=data.get("output_path", "output.png"),
            background=background,
        )


def save_settings(settings: AppSettings, path: str = DEFAULT_SETTINGS_PATH) -> None:
    """設定をJSONファイルに保存する."""
    Path(path).write_text(
        json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_settings(path: str = DEFAULT_SETTINGS_PATH) -> AppSettings:
    """設定をJSONファイルから読み込む."""
    settings_path = Path(path)
    if not settings_path.exists():
        return AppSettings()
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        return AppSettings.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return AppSettings()
