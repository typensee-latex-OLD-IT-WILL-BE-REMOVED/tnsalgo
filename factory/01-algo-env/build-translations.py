#! /usr/bin/env python3

from collections import defaultdict
import re

from mistool.os_use import PPath
from mistool.string_use import between, joinand
from orpyste.data import ReadBlock

BASENAME = PPath(__file__).stem.replace("build-", "")
THIS_DIR = PPath(__file__).parent

TEX_FILE = THIS_DIR / "02-5-text-version[fr].tex"

KEYWORDS_FINAL_DIR = THIS_DIR.parent.parent / "tnsalgo" / "translate"
TRANSLATIONS_DIR   = THIS_DIR / KEYWORDS_FINAL_DIR.name
LANG_PEUF_DIR      = TRANSLATIONS_DIR / "config"

THIS_EXA_DIR       = THIS_DIR / "examples" / "algo-basic" / "additional-macros"


LATEX_N_OUPUT_TEMP = """
\\begin{{algo}}
{latexcode}
\\end{{algo}}
""".lstrip()

DECO   = " "*4
DECO_2 = DECO*2

ALL_LANGS = [
    ppath.name
    for ppath in LANG_PEUF_DIR.walk("dir::")
    if ppath.parent == LANG_PEUF_DIR
]

DEFAULT_LANG = "EN"

ALL_MACROS = set()

ALL_TRANS = defaultdict(dict)


# ----------- #
# -- TOOLS -- #
# ----------- #

def protect(word):
    word = word.strip()

    if " " in word:
        word = f"{{{word}}}"

    return word


def normalize(trans):
    for word, wtrans in trans.items():
        ALL_MACROS.add(word)

# Auto tranlation !
        if not wtrans:
            lastchar = word[-1]

            if lastchar in ["s", "m"]:
                basename = word[:-1]

                if basename in trans:
                    if lastchar == "m":
                        lastchar = ""

                    wtrans = trans[basename] + lastchar.lower()

                else:
                    wtrans = word

            else:
                wtrans = word

# Add the translation
        trans[word] = wtrans

# Protect and split translations
    for word, wtrans in trans.items():
        if " " in wtrans:
            wtrans = protect(wtrans)

        trans[word] = wtrans

# Nothing more to do.
    return trans


def macrodef(kind):
    if kind == "word":
        kind = ""

    elif kind == "ifelif":
        kind = "IF"

    else:
        kind = kind.title()

    return f"\\SetKw{kind}"


def rawgather(macroname, trans, suffix = ""):
    tex_trans = []

    for word, wtrans in trans.items():
        tex_trans.append(
            f"{macroname}{{{word}}}{{{wtrans}}}{suffix}"
        )

    return tex_trans


def texify(kind, trans):
    tex_trans = [
        '',
        '% ' + kind.title(),
    ]

# Common def
    macroname = f"{macrodef(kind)}"

# \SetKw{Text}{Traduction}
    if kind in ["input", "word"]:
        tex_trans += rawgather(macroname, trans)

# \SetKwBlock{Text}{Traduction}
    elif kind == "block":
        tex_trans += rawgather(macroname, trans, suffix = "{}")

# \SetKwFor{For}{Pour}{:}{}
    elif kind == "for":
        tex_trans += rawgather(macroname, trans, suffix = "{:}{}")

# \SetKwRepeat{Repeat}{Répéter}{{Jusqu'à Avoir}}
    elif kind == "repeat":
        tex_trans.append(
            f"{macroname}{{Repeat}}"
            f"{{{trans['Repeat']}}}{{{trans['Until']}}}"
        )

# \SetKwIF{If}{ElseIf}{Else}{Si}{:}{{Sinon Si}}{{Sinon}}{}
    elif kind == "ifelif":
        tex_trans.append(
            f"{macroname}{{If}}{{ElseIf}}{{Else}}"
            f"{{{trans['If']}}}{{:}}"
            f"{{{trans['ElseIf']}}}{{{trans['Else']}}}{{}}"
        )

# \SetKwSwitch{Switch}{Case}{Other}{Selon}{:}{Cas}{Autre}{}
    elif kind == "switch":
        tex_trans.append(
            f"{macroname}{{Switch}}{{Case}}{{Other}}"
            f"{{{trans['Switch']}}}{{:}}"
            f"{{{trans['Case']}}}{{{trans['Other']}}}{{}}{{}}"
        )

    else:
        print('', kind, trans, sep="\n");exit()

    return tex_trans


def build_tex_trans(lang):
    global ALL_TRANS

    tex_trans = []

    for peufpath in (
        LANG_PEUF_DIR / lang
    ).walk("file::*.peuf"):
        with ReadBlock(
            content = peufpath,
            mode    = 'keyval:: ='
        ) as data:
            for kind, trans in data.mydict("std mini").items():
                trans      = normalize(trans)
                tex_trans += texify(kind, trans)

                ALL_TRANS[lang].update(trans)

    return tex_trans


# ------------------------- #
# -- LANG SPECIFICATIONS -- #
# ------------------------- #

TEX_TRANS = {}

for lang in ALL_LANGS:
    TEX_TRANS[lang] = build_tex_trans(lang)
    TEX_TRANS[lang] = [
        l if l.startswith("%") else DECO + l
        for l in TEX_TRANS[lang][1:]
    ]
    TEX_TRANS[lang] = "\n".join(TEX_TRANS[lang])


# -------------------- #
# -- TEXTUAL MACROS -- #
# -------------------- #

latexmacros    = set()
stytxtmacros   = defaultdict(list)
template_macro = """
    \\protected\\def\\{macroname}{{\@ifstar\\tnsalgo@{macroname}@star\\tnsalgo@{macroname}@no@star}}
    \\def\\tnsalgo@{macroname}@no@star{{\\textbf{{{sdtver}}}}}
    \\def\\tnsalgo@{macroname}@star{{\\texttt{{{truetypever}}}}}"""

unbreakablespace = " "

for lang in ALL_TRANS:
    for control, pieces in {
        "If"          : [],
        "IfElse"      : ["If", "Else"],
        "IfElseIf"    : ["If", "Else", "If"],
        "IfElseIfElse": ["If", "Else If", "Else"],
        "For"         : [],
        "While"       : [],
        "Repeat"      : ["Repeat", "Until"],
        "Switch"      : ["Switch", "Case"],
    }.items():
        macroname = f"txt{control}"

        latexmacros.add(macroname)

        if pieces:
            macrotxt = []

            for p in pieces:
                seq = []

                for subp in p.split(" "):
                    seq.append(ALL_TRANS[lang][subp])

                macrotxt.append(" ".join(seq))

        else:
            macrotxt = [ALL_TRANS[lang][control]]


        truetypever = "\\,-\\,".join(macrotxt)
        sdtver      = "\\,--\\,".join(macrotxt)

        truetypever = truetypever.replace("{", "") \
                                 .replace("}", "") \
                                 .replace(" ", unbreakablespace)

        sdtver = sdtver.replace("{", "") \
                       .replace("}", "") \
                       .replace(" ", unbreakablespace)


        stytxtmacros[lang].append(
            template_macro.format(
                macroname   = macroname,
                truetypever = truetypever,
                sdtver      = sdtver
            )
        )


    stytxtmacros[lang] = "\n".join(stytxtmacros[lang])
    stytxtmacros[lang] = DECO + stytxtmacros[lang].lstrip()


# -------------------- #
# -- BUILD LANG STY -- #
# -------------------- #

for lang, tex_trans in TEX_TRANS.items():
    with open(
        file     = TRANSLATIONS_DIR / f"tnsalgo_{lang.upper()}.sty",
        mode     = 'w',
        encoding = 'utf-8'
    ) as texlang:
        texlang.write(f"""
\\newcommand\\uselang{lang}{{
% Textual versions
{stytxtmacros[lang]}

{tex_trans}
}}
        """.lstrip())


# --------------------------------------- #
# -- COPY LANG STY TO THE FINAL FOLDER -- #
# --------------------------------------- #

KEYWORDS_FINAL_DIR.create("dir")

for peufpath in (TRANSLATIONS_DIR).walk("file::*.sty"):
    peufpath.copy_to(
        dest     = KEYWORDS_FINAL_DIR / peufpath.name,
        safemode = False
    )


# ------------------------- #
# -- TEMPLATES TO UPDATE -- #
# ------------------------- #

with open(
    file     = TEX_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as docfile:
    template_tex = docfile.read()


with ReadBlock(
    content = TRANSLATIONS_DIR / "config" / "for-doc[fr].peuf",
    mode    = {
        'verbatim'  : ":default:",
        'keyval:: =': "titles",
    }
) as data:
    docinfos = data.mydict("std mini")

    peuftitles = docinfos["titles"]
    del docinfos["titles"]


with open(
    file     = TRANSLATIONS_DIR / "tnsalgo_EN.sty",
    mode     = 'r',
    encoding = 'utf-8'
) as docfile:
    lang_sty = docfile.read()


# ------------------------------ #
# -- USEFUL TEXT MACROS - DOC -- #
# ------------------------------ #

text_start, _, text_end = between(
    text = template_tex,
    seps = [
        "% == Text tools - START == %\n",
        "\n% == Text tools - END == %"
    ],
    keepseps = True
)


latexmacros = list(latexmacros)

latexmacros.sort(
    key = lambda x: len(x)
)

specialsort = [
    "I",   # If...
    "S",   # Switch
    "F",   # For
    "W",   # While
    "R",   # Repeat
]

latexmacros.sort(
    key = lambda x: specialsort.index(x[3])
)


maxlenmacronanme = max(
    len(x) for x in latexmacros
)

texcode = ["\n\\begin{enumerate}"]


for suffix, kind in [
    ("" , "algorithme"),
    ("*", "True Type"),
]:
    texcode += [
        f"""
{DECO}\\item Liste des commandes de type \\og {kind} \\fg{{}}.

{DECO}\\begin{{enumerate}}[label=\\alph*)]
        """.rstrip()
    ]

    if suffix == "*":
        maxlenmacronanme += 1

    for macroname in latexmacros:
        macroname += suffix

        if "For" in macroname:
            texcode.append(f"{DECO}\\smallskip")

        texcode.append(
            f"{DECO*2}\\item \\verb#\\{macroname: <{maxlenmacronanme}}# "
            f"\,donne\, \\{macroname}."
        )

    texcode.append(f"{DECO}\\end{{enumerate}}")


texcode.append("\\end{enumerate}")

texcode = "\n".join(texcode + [""])

template_tex = text_start + texcode + text_end


# ----------------------------- #
# -- UPDATING THE LATEX FILE -- #
# ----------------------------- #

with open(
    file     = TEX_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(template_tex)
