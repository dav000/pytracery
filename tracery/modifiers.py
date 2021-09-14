def replace(text: str, *params: str) -> str:
    return text.replace(params[0], params[1])


def capitalizeAll(text: str, *params: str) -> str:
    return text.title()


def capitalize_(text: str, *params: str) -> str:
    return text[0].upper() + text[1:]


def a(text: str, *params: str) -> str:
    if len(text) > 0:
        if text[0] in "uU":
            if len(text) > 2:
                if text[2] in "iI":
                    return "a " + text
        if text[0] in "aeiouAEIOU":
            return "an " + text
    return "a " + text


def firstS(text: str, *params: str) -> str:
    text2 = text.split(" ")
    return " ".join([s(text2[0])] + text2[1:])


def s(text: str, *params: str) -> str:
    if text[-1] in "shxSHX":
        return text + "es"
    if text[-1] in "yY":
        if text[-2] not in "aeiouAEIOU":
            return text[:-1] + "ies"
        else:
            return text + "s"
    return text + "s"


def ed(text: str, *params: str) -> str:
    if len(text) > 0 and text[-1] in "eE":
        return text + "d"
    if len(text) > 1 and text[-1] in "yY" and text[-2] not in "aeiouAEIOU":
        return text[:-1] + "ied"
    if len(text) > 0:
        return text + "ed"
    return text


def uppercase(text: str, *params: str) -> str:
    return text.upper()


def lowercase(text: str, *params: str) -> str:
    return text.lower()


base_english = {
    "replace": replace,
    "capitalizeAll": capitalizeAll,
    "capitalize": capitalize_,
    "a": a,
    "firstS": firstS,
    "s": s,
    "ed": ed,
    "uppercase": uppercase,
    "lowercase": lowercase,
}
