from banknarrativeparser.parsers.LAT_AM.pattern1 import is_pattern1, parse_pattern1
from banknarrativeparser.parsers.LAT_AM.pattern2 import is_pattern2, parse_pattern2
from banknarrativeparser.parsers.LAT_AM.pattern3 import is_pattern3, parse_pattern3
from banknarrativeparser.parsers.LAT_AM.pattern4 import is_pattern4, parse_pattern4
from banknarrativeparser.parsers.LAT_AM.pattern5 import is_pattern5, parse_pattern5
from banknarrativeparser.parsers.LAT_AM.pattern6 import is_pattern6, parse_pattern6
from banknarrativeparser.parsers.LAT_AM.pattern7 import is_pattern7, parse_pattern7
from banknarrativeparser.parsers.LAT_AM.pattern8 import is_pattern8, parse_pattern8
from banknarrativeparser.parsers.LAT_AM.pattern9 import is_pattern9, parse_pattern9
from banknarrativeparser.parsers.LAT_AM.pattern10 import is_pattern10, parse_pattern10
from banknarrativeparser.parsers.LAT_AM.pattern11 import is_pattern11, parse_pattern11
from banknarrativeparser.parsers.LAT_AM.pattern12 import is_pattern12, parse_pattern12


def is_LATAM(line: str) -> int | None:
    if not line:
        return None

    line = line.strip()
    if not line:
        return None

    if is_pattern1(line):
        return 1
    if is_pattern2(line):
        return 2
    if is_pattern3(line):
        return 3
    if is_pattern4(line):
        return 4
    if is_pattern5(line):
        return 5
    if is_pattern6(line):
        return 6
    if is_pattern7(line):
        return 7
    if is_pattern8(line):
        return 8
    if is_pattern9(line):
        return 9
    if is_pattern10(line):
        return 10
    if is_pattern11(line):
        return 11
    if is_pattern12(line):
        return 12

    return None

def LATAM_parse(line: str) -> dict | None:
    
    pat_no = is_LATAM(line)
    if pat_no is None:
        return None

    print(f"LATIN AMERICAN Pattern-{pat_no}\n")

    res = None
    if pat_no == 1:
        res = parse_pattern1(line)
    elif pat_no == 2:
        res = parse_pattern2(line)
    elif pat_no == 3:
        res = parse_pattern3(line)
    elif pat_no == 4:
        res = parse_pattern4(line)
    elif pat_no == 5:
        res = parse_pattern5(line)
    elif pat_no == 6:
        res = parse_pattern6(line)
    elif pat_no == 7:
        res = parse_pattern7(line)
    elif pat_no == 8:
        res = parse_pattern8(line)
    elif pat_no == 9:
        res = parse_pattern9(line)
    elif pat_no == 10:
        res = parse_pattern10(line)
    elif pat_no == 11:
        res = parse_pattern11(line)
    elif pat_no == 12:
        res = parse_pattern12(line)

    if isinstance(res, dict):
        # Ensure RAW is first key
        return {
            "RAW": line,
            **res
        }

    return res
