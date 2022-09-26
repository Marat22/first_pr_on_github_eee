from pathlib import Path
import math
from typing import List, Optional

rts_f = Path(r"DATA\rts2013.3.csv")  # rts2013.3.csv
games_f = Path(r"DATA\games-rts2013.3-50-1-10.csv")  # games-rts2013.3-50-1-10.csv

res_p = Path(r"result\result.csv")

# a: Optional[int] = None
# a: int | None = None

def make_closes(closes: dict[str, dict[int, int]], datetime: str, price_close: int) -> dict[str, dict[int, int]]:
    """function gets information about close(datetime, price of closing)
     and then add it to closes dict"""
    if closes.get(datetime) is None:
        closes[datetime] = {int(price_close): 1}
    else:
        if closes[datetime].get(int(price_close)) is None:
            closes[datetime][int(price_close)] = 1
        else:
            closes[datetime][int(price_close)] += 1
    return closes


def make_games_dict(games_path) -> tuple[dict[str, dict[int, int]], dict[str, dict[int, int]], dict[str, str]]:
    open_dict = {}

    longs_close = {}
    shorts_close = {}

    with games_path.open("r", encoding="utf-8") as file:
        for line in file:
            bar_games = line.split(";")
            close_datetime: str = bar_games[3]
            open_datetime: str = bar_games[2]
            price_close = bar_games[-1]
            action = bar_games[1]

            if action == "B":
                open_dict[open_datetime] = "B"
                longs_close = make_closes(longs_close, close_datetime, price_close)
            if action == "S":
                open_dict[open_datetime] = "S"
                shorts_close = make_closes(shorts_close, close_datetime, price_close)

    return longs_close, shorts_close, open_dict


def closing(closes: dict, datetime: str, AC: int, pos: int, previous_close: int, action: str) -> tuple[int, int, int]:
    """function counts the change in AC when trades close"""
    (k, reverse) = (1, True) if action == "B" else (-1, False)
    closes_l = sorted(list(closes[datetime].keys()), reverse=reverse)
    for close in closes_l:
        AC += (close - previous_close) * pos * k
        pos -= closes[datetime][close]
        previous_close = close
    return AC, pos, previous_close


def opening(action: str, current_close: int, pos_for_opening: int, pos_for_another: int, previous_close_for_opening: int,
            previous_close_for_another: int,
            AC_for_opening: int, AC_for_another: int) -> (int, int, int):
    """function opens trade
    and also counts the AC changes since last bar"""
    k = 1 if action == "B" else -1

    AC_for_opening += k * (current_close - previous_close_for_opening) * pos_for_opening
    pos_for_opening += 1
    AC_for_another += (k * -1) * (current_close - previous_close_for_another) * pos_for_another

    return pos_for_opening, AC_for_opening, AC_for_another


def every_bar_run(rts_path: Path, games_path: Path) -> None:
    pos_l, pos_s, AC_longs, AC_shorts, previous_close_l, previous_close_s = 0, 0, 0, 0, 0, 0
    longs_close, shorts_close, open_dict = make_games_dict(games_path)

    result_file = res_p.open("w")
    result_file.write("DATETIME;AC;AC_LONGS;AC_SHORTS;POS_LONGS;POS_SHORTS\n")

    with rts_path.open("r", encoding="utf-8") as rts_file:
        next(rts_file)
        for line in rts_file:
            bar_rts = line.split(",")
            if (not (70000 <= int(bar_rts[3]) < 70005) and
                    not (100000 <= int(bar_rts[3]) < 100500) and
                    not (140000 <= int(bar_rts[3]) < 141000) and
                    not (184500 <= int(bar_rts[3]) < 191000)):

                datetime = bar_rts[2] + bar_rts[3]
                current_close = round(float(bar_rts[-2]))

                if longs_close.get(datetime) is not None:  # longs
                    AC_longs, pos_l, previous_close_l = closing(closes=longs_close,
                                                                AC=AC_longs, pos=pos_l,
                                                                previous_close=previous_close_l,
                                                                datetime=datetime, action="B")

                if shorts_close.get(datetime) is not None:  # shorts
                    AC_shorts, pos_s, previous_close_s = closing(closes=shorts_close,
                                                                 AC=AC_shorts, pos=pos_s,
                                                                 previous_close=previous_close_s,
                                                                 datetime=datetime, action="S")

                if open_dict.get(datetime) == "B":
                    pos_l, AC_longs, AC_shorts = opening(action="B", current_close=current_close,
                                                         pos_for_opening=pos_l, pos_for_another=pos_s,
                                                         previous_close_for_opening=previous_close_l,
                                                         previous_close_for_another=previous_close_s,
                                                         AC_for_opening=AC_longs, AC_for_another=AC_shorts)

                elif open_dict.get(datetime) == "S":
                    pos_s, AC_shorts, AC_longs = opening(action="S", current_close=current_close,
                                                         pos_for_opening=pos_s, pos_for_another=pos_l,
                                                         previous_close_for_opening=previous_close_s,
                                                         previous_close_for_another=previous_close_l,
                                                         AC_for_opening=AC_shorts, AC_for_another=AC_longs)

                previous_close_l = current_close
                previous_close_s = current_close

                result_file.write(
                    f"{datetime};{AC_longs + AC_shorts};{AC_longs};{AC_shorts};"
                    f"{pos_l};{pos_s}\n")

            # if i == len(rts_list) - 3:
            #     datetime = rts_list[i+1].split(",")[2] + rts_list[i+1].split(",")[3]
            #     AC_shorts += (previous_close_s - float(current_close)) * pos_s
            #     AC_longs += (float(current_close) - previous_close_l) * pos_l
            #     result_file.write(
            #         f"{datetime};{AC_longs + AC_shorts};{AC_longs};{AC_shorts};"
            #         f"0;0\n")
            #     break
    result_file.close()


every_bar_run(rts_path=rts_f, games_path=games_f)
