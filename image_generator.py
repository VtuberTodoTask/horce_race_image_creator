"""出馬表の画像を生成するモジュール."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from scraper import HorseEntry

# 枠番の色定義 (枠番 -> (背景色, 文字色))
WAKU_COLORS: dict[int, tuple[str, str]] = {
    1: ("#FFFFFF", "#000000"),  # 白
    2: ("#000000", "#FFFFFF"),  # 黒
    3: ("#FF0000", "#FFFFFF"),  # 赤
    4: ("#0000FF", "#FFFFFF"),  # 青
    5: ("#FFD700", "#000000"),  # 黄
    6: ("#008000", "#FFFFFF"),  # 緑
    7: ("#FF8C00", "#FFFFFF"),  # 橙
    8: ("#FF69B4", "#FFFFFF"),  # 桃
}

# 凡例マーク
LEGEND_MARKS = [
    ("◎", "本命馬"),
    ("○", "対抗馬"),
    ("●", "大穴"),
    ("☆", "注目馬"),
]

# フォントパス候補 (OS別)
_FONT_CANDIDATES_LINUX = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]

_FONT_CANDIDATES_WINDOWS = [
    "C:\\Windows\\Fonts\\meiryo.ttc",
    "C:\\Windows\\Fonts\\msgothic.ttc",
    "C:\\Windows\\Fonts\\YuGothM.ttc",
    "C:\\Windows\\Fonts\\YuGothR.ttc",
    "C:\\Windows\\Fonts\\YuGothB.ttc",
]

_FONT_CANDIDATES_MACOS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]


def _get_font_candidates() -> list[str]:
    if sys.platform == "win32":
        return _FONT_CANDIDATES_WINDOWS + _FONT_CANDIDATES_LINUX
    if sys.platform == "darwin":
        return _FONT_CANDIDATES_MACOS + _FONT_CANDIDATES_LINUX
    return _FONT_CANDIDATES_LINUX


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _get_font_candidates():
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _text_size(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _parse_bg_color(color: str, transparent: bool) -> tuple[int, int, int, int]:
    """Parse hex color to RGBA tuple."""
    if transparent:
        return (0, 0, 0, 0)
    color = color.strip().lstrip("#")
    if len(color) == 6:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return (r, g, b, 255)
    return (255, 255, 255, 255)


def generate_image(
    entries: list[HorseEntry],
    participant_names: list[str] | None = None,
    avatar_paths: list[str] | None = None,
    output_path: str = "output.png",
    background_path: str = "",
    size_mode: str = "auto",
    custom_width: int = 1280,
    custom_height: int = 720,
    bg_color: str = "#FFFFFF",
    transparent: bool = False,
) -> str:
    """出馬表の画像を生成する.

    Args:
        entries: 馬エントリーリスト
        participant_names: 参加者名リスト
        avatar_paths: 参加者アバター画像パスリスト
        output_path: 出力画像パス
        background_path: 背景画像パス
        size_mode: サイズモード ("auto" | "background" | "custom")
        custom_width: カスタム幅 (size_mode="custom"時)
        custom_height: カスタム高さ (size_mode="custom"時)
        bg_color: 背景色 (hex, 例: "#FFFFFF")
        transparent: 透過背景にするか

    Returns:
        出力画像パス
    """
    if participant_names is None:
        participant_names = []
    if avatar_paths is None:
        avatar_paths = []

    num_participants = max(len(participant_names), len(avatar_paths), 0)

    # パディング調整
    while len(participant_names) < num_participants:
        participant_names.append("")
    while len(avatar_paths) < num_participants:
        avatar_paths.append("")

    # フォント設定
    font_header = _find_font(22)
    font_cell = _find_font(20)
    font_legend = _find_font(20)
    font_legend_mark = _find_font(28)

    # レイアウト定数
    row_height = 40
    header_height = 55
    avatar_height = 60
    padding = 8

    # 列幅定義
    col_waku = 45
    col_umaban = 45
    col_name = 210
    col_sex = 45
    col_weight = 50
    col_jockey = 100
    participant_col_width = 80

    data_cols_width = (
        col_waku + col_umaban + col_name + col_sex + col_weight + col_jockey
    )
    participant_cols_width = (
        participant_col_width * num_participants if num_participants > 0 else 0
    )
    legend_width = 120

    table_width = data_cols_width + participant_cols_width
    total_width = table_width + legend_width + 40  # 右余白

    num_rows = len(entries)
    table_top = 20
    avatar_row_top = table_top
    header_top = avatar_row_top + (avatar_height if num_participants > 0 else 0)
    data_top = header_top + header_height

    table_height = data_top + num_rows * row_height - table_top
    total_height = table_top + table_height + 20

    left_margin = 20

    # 背景画像・サイズ決定
    bg_img: Image.Image | None = None
    if background_path and Path(background_path).exists():
        bg_img = Image.open(background_path).convert("RGBA")

    if size_mode == "background" and bg_img is not None:
        canvas_width, canvas_height = bg_img.size
    elif size_mode == "custom":
        canvas_width = custom_width
        canvas_height = custom_height
    else:
        canvas_width = total_width
        canvas_height = total_height

    # 画像作成
    if bg_img is not None:
        img = bg_img.resize((canvas_width, canvas_height), Image.LANCZOS)
    else:
        fill_color = _parse_bg_color(bg_color, transparent)
        img = Image.new("RGBA", (canvas_width, canvas_height), fill_color)
    draw = ImageDraw.Draw(img)

    # --- アバター行 ---
    if num_participants > 0:
        for pi in range(num_participants):
            ax = left_margin + data_cols_width + pi * participant_col_width
            ay = avatar_row_top

            avatar_path = avatar_paths[pi] if pi < len(avatar_paths) else ""
            if avatar_path and Path(avatar_path).exists():
                try:
                    ava = Image.open(avatar_path).convert("RGBA")
                    ava_size = avatar_height - 4
                    ava.thumbnail((ava_size, ava_size), Image.LANCZOS)
                    ava_x = ax + (participant_col_width - ava.width) // 2
                    ava_y = ay + (avatar_height - ava.height) // 2
                    img.paste(ava, (ava_x, ava_y), ava)
                except Exception:
                    pass

    # --- ヘッダー描画 ---
    hx = left_margin
    hy = header_top

    # ヘッダー背景
    draw.rectangle(
        [hx, hy, hx + table_width, hy + header_height],
        fill="#F5F5F5",
        outline="#000000",
    )

    headers = [
        ("枠", col_waku),
        ("馬\n番", col_umaban),
        ("馬名", col_name),
        ("性\n齢", col_sex),
        ("斤\n量", col_weight),
        ("騎手", col_jockey),
    ]

    cx = hx
    for header_text, col_w in headers:
        # 縦線
        draw.line([(cx, hy), (cx, hy + header_height)], fill="#000000", width=1)

        # ヘッダーテキスト描画（改行対応）
        lines = header_text.split("\n")
        line_height = header_height // max(len(lines), 1)
        for li, line in enumerate(lines):
            tw, th = _text_size(draw, line, font_header)
            tx = cx + (col_w - tw) // 2
            ty = hy + li * line_height + (line_height - th) // 2
            draw.text((tx, ty), line, fill="#000000", font=font_header)

        cx += col_w

    # 参加者ヘッダー列
    for pi in range(num_participants):
        draw.line([(cx, hy), (cx, hy + header_height)], fill="#000000", width=1)
        # 名前があれば表示
        name = participant_names[pi] if pi < len(participant_names) else ""
        if name:
            tw, th = _text_size(draw, name, font_cell)
            tx = cx + (participant_col_width - tw) // 2
            ty = hy + (header_height - th) // 2
            draw.text((tx, ty), name, fill="#000000", font=font_cell)
        cx += participant_col_width

    # 右端線
    draw.line(
        [(hx + table_width, hy), (hx + table_width, hy + header_height)],
        fill="#000000",
        width=1,
    )

    # --- データ行描画 ---
    for ri, entry in enumerate(entries):
        ry = data_top + ri * row_height
        cx = hx

        # 行全体の背景（交互色）
        bg = "#FFFFFF" if ri % 2 == 0 else "#F9F9F9"
        draw.rectangle(
            [cx, ry, cx + table_width, ry + row_height], fill=bg, outline=None
        )

        # 枠番セル（色付き背景）
        waku_bg, waku_fg = WAKU_COLORS.get(entry.waku, ("#FFFFFF", "#000000"))
        draw.rectangle(
            [cx + 1, ry + 1, cx + col_waku - 1, ry + row_height - 1], fill=waku_bg
        )
        wt = str(entry.waku)
        tw, th = _text_size(draw, wt, font_cell)
        draw.text(
            (cx + (col_waku - tw) // 2, ry + (row_height - th) // 2),
            wt,
            fill=waku_fg,
            font=font_cell,
        )
        cx += col_waku

        # 馬番
        draw.line([(cx, ry), (cx, ry + row_height)], fill="#000000", width=1)
        ut = str(entry.umaban)
        tw, th = _text_size(draw, ut, font_cell)
        draw.text(
            (cx + (col_umaban - tw) // 2, ry + (row_height - th) // 2),
            ut,
            fill="#000000",
            font=font_cell,
        )
        cx += col_umaban

        # 馬名
        draw.line([(cx, ry), (cx, ry + row_height)], fill="#000000", width=1)
        tw, th = _text_size(draw, entry.name, font_cell)
        draw.text(
            (cx + padding, ry + (row_height - th) // 2),
            entry.name,
            fill="#000000",
            font=font_cell,
        )
        cx += col_name

        # 性齢
        draw.line([(cx, ry), (cx, ry + row_height)], fill="#000000", width=1)
        tw, th = _text_size(draw, entry.sex_age, font_cell)
        draw.text(
            (cx + (col_sex - tw) // 2, ry + (row_height - th) // 2),
            entry.sex_age,
            fill="#000000",
            font=font_cell,
        )
        cx += col_sex

        # 斤量
        draw.line([(cx, ry), (cx, ry + row_height)], fill="#000000", width=1)
        tw, th = _text_size(draw, entry.weight, font_cell)
        draw.text(
            (cx + (col_weight - tw) // 2, ry + (row_height - th) // 2),
            entry.weight,
            fill="#000000",
            font=font_cell,
        )
        cx += col_weight

        # 騎手
        draw.line([(cx, ry), (cx, ry + row_height)], fill="#000000", width=1)
        tw, th = _text_size(draw, entry.jockey, font_cell)
        draw.text(
            (cx + (col_jockey - tw) // 2, ry + (row_height - th) // 2),
            entry.jockey,
            fill="#000000",
            font=font_cell,
        )
        cx += col_jockey

        # 参加者セル（空欄）
        for pi in range(num_participants):
            draw.line([(cx, ry), (cx, ry + row_height)], fill="#000000", width=1)
            cx += participant_col_width

        # 行の外枠
        draw.line([(hx, ry), (hx + table_width, ry)], fill="#000000", width=1)
        draw.line(
            [(hx, ry + row_height), (hx + table_width, ry + row_height)],
            fill="#000000",
            width=1,
        )
        draw.line([(hx, ry), (hx, ry + row_height)], fill="#000000", width=1)
        draw.line(
            [(hx + table_width, ry), (hx + table_width, ry + row_height)],
            fill="#000000",
            width=1,
        )

    # --- 凡例描画 ---
    legend_x = hx + table_width + 20
    legend_y = header_top + 40

    for mark, label in LEGEND_MARKS:
        tw, th = _text_size(draw, mark, font_legend_mark)
        draw.text(
            (legend_x + (legend_width - tw) // 2, legend_y),
            mark,
            fill="#000000",
            font=font_legend_mark,
        )
        legend_y += th + 4

        tw2, th2 = _text_size(draw, label, font_legend)
        draw.text(
            (legend_x + (legend_width - tw2) // 2, legend_y),
            label,
            fill="#000000",
            font=font_legend,
        )
        legend_y += th2 + 20

    # 保存
    if transparent:
        img.save(output_path, "PNG")
    else:
        img.convert("RGB").save(output_path, "PNG")
    return output_path
