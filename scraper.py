"""netkeibaの出馬表ページをスクレイピングして馬情報を取得するモジュール."""

from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class HorseEntry:
    """出馬表の1行分のデータ."""

    waku: int  # 枠番
    umaban: int  # 馬番
    name: str  # 馬名
    sex_age: str  # 性齢
    weight: str  # 斤量
    jockey: str  # 騎手


def fetch_shutuba(url: str) -> tuple[str, list[HorseEntry]]:
    """出馬表URLからレース名と馬リストを取得する.

    Args:
        url: netkeibaの出馬表URL

    Returns:
        (レース名, 馬エントリーリスト)
    """
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "lxml", from_encoding="euc-jp")

    # レース名取得
    race_name_tag = soup.select_one(".RaceName")
    race_name = race_name_tag.get_text(strip=True) if race_name_tag else "レース"

    rows = soup.select("tr.HorseList")
    entries: list[HorseEntry] = []

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 6:
            continue

        # 枠番
        waku_td = tds[0]
        waku_classes = waku_td.get("class", [])
        waku_num = 0
        for cls in waku_classes:
            if cls.startswith("Waku") and cls != "Waku":
                try:
                    waku_num = int(cls.replace("Waku", "").replace("Txt_C", "").strip())
                except ValueError:
                    pass

        # 馬番
        umaban_text = tds[1].get_text(strip=True)
        try:
            umaban = int(umaban_text)
        except ValueError:
            continue

        # 馬名
        horse_name_tag = row.select_one(".HorseName a")
        horse_name = horse_name_tag.get("title", "") if horse_name_tag else ""
        if not horse_name:
            horse_name = horse_name_tag.get_text(strip=True) if horse_name_tag else ""
        if not horse_name:
            continue

        # 性齢
        barei_tag = row.select_one(".Barei")
        sex_age = barei_tag.get_text(strip=True) if barei_tag else ""

        # 斤量 (Bareiの次のtd)
        weight = ""
        if barei_tag:
            weight_td = barei_tag.find_next_sibling("td")
            if weight_td:
                weight = weight_td.get_text(strip=True)

        # 騎手
        jockey_tag = row.select_one(".Jockey a")
        jockey = jockey_tag.get("title", "") if jockey_tag else ""
        if not jockey:
            jockey = jockey_tag.get_text(strip=True) if jockey_tag else ""

        entries.append(
            HorseEntry(
                waku=waku_num,
                umaban=umaban,
                name=horse_name,
                sex_age=sex_age,
                weight=weight,
                jockey=jockey,
            )
        )

    return race_name, entries
