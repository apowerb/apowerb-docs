#!/usr/bin/env python3
"""Le site sert-il ce qui vient d'etre merge ?

L'API de declenchement de Mintlify demande un plan superieur -- elle rend
`401 {"error":"Please upgrade to access this route."}`. Mais Mintlify deploie
ce depot tout seul, mesure le 08/09/2026 : deux merges consecutifs etaient en
ligne dix minutes plus tard sans geste manuel, et le check << Mintlify
Deployment >> passe en 36 secondes sur une PR.

Alors plutot que de declencher la publication, ce controle verifie la
propriete qui compte : la page servie contient-elle ce que le commit vient
d'ecrire ? Il teste le resultat, pas le mecanisme -- et il reste vrai quel que
soit le plan ou la facon dont la publication se fait.

Le temoin est une PHRASE, pas un mot. La premiere version cherchait un mot
long absent de la version d'avant, et elle est sortie verte sans rien prouver
des son premier vrai passage : une page de prose enrichie ne gagne presque
jamais de mot inedit. Une suite de mots, elle, est neuve meme quand chaque mot
est deja la.

Cote page, on compare du TEXTE VISIBLE : Mintlify decoupe le rendu en balises
(coloration syntaxique, composants), donc chercher une phrase dans le HTML brut
echoue toujours. On retire les balises d'abord.

Usage :
    check_docs_live.py <sha_avant> <sha_apres>
"""
from __future__ import annotations

import html as html_mod
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

SITE = "https://docs.apowerb.com"
# Reglables pour eprouver le chemin rouge sans attendre dix minutes.
DEADLINE_S = int(os.environ.get("DOCS_LIVE_DEADLINE", "600"))
INTERVAL_S = int(os.environ.get("DOCS_LIVE_INTERVAL", "20"))

# Assez long pour ne pas se produire par hasard, assez court pour qu'une
# retouche de paragraphe en fournisse un.
MIN_WORDS = 6
MIN_CHARS = 45


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout


def visible_text(raw: str) -> str:
    """Le texte qu'un lecteur voit, balises et scripts retires."""
    out = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    out = re.sub(r"(?s)<[^>]+>", " ", out)
    return re.sub(r"\s+", " ", html_mod.unescape(out)).strip()


def prose(line: str) -> str:
    """Une ligne de .mdx ramenee a ce qu'elle donnera a l'ecran.

    Le balisage inline disparait ici parce qu'il disparait aussi du rendu :
    garder un backtick ou une balise dans le temoin, c'est chercher sur la
    page un caractere qui n'y sera jamais.
    """
    s = line.strip()
    if s.startswith(("<", ">", "|", "#", "---", "import ", "export ")):
        return ""
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)   # liens : on garde le texte
    s = re.sub(r"<[^>]+>", " ", s)                    # composants MDX
    s = s.replace("`", "").replace("**", "").replace("*", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def body_lines(text: str) -> list[str]:
    """Le corps de la page, frontmatter exclu.

    `title:` et `description:` sont du texte, et ils ressemblent a de la
    prose -- mais ils vont dans les metadonnees, jamais dans le corps rendu.
    Un temoin pris la reste introuvable sur une page pourtant a jour : c'est
    le faux rouge qu'a produit `deployment/kubernetes` au retest.
    """
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                return lines[i + 1:]
        return []  # frontmatter jamais referme : rien de fiable a lire
    return lines


def witness(path: str, before: str, after: str) -> str | None:
    """La plus longue phrase que ce commit ajoute au CORPS de cette page."""
    try:
        old_lines = set(body_lines(git("show", f"{before}:{path}")))
    except subprocess.CalledProcessError:
        old_lines = set()  # page nouvelle
    new = body_lines(git("show", f"{after}:{path}"))

    best = ""
    for line in new:
        if line in old_lines:
            continue
        candidate = prose(line)
        if len(candidate) >= MIN_CHARS and len(candidate.split()) >= MIN_WORDS:
            if len(candidate) > len(best):
                best = candidate
    # Une ligne entiere peut deborder du rendu (retours a la ligne dans le
    # HTML) : on garde un debut suffisamment long, pas la ligne complete.
    if best:
        words = best.split()
        return " ".join(words[:14])
    return None


def page_url(path: str) -> str:
    return f"{SITE}/{path[:-len('.mdx')]}"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "docs-live-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return visible_text(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return f"__HTTP_{exc.code}__"
    except Exception as exc:  # reseau, TLS, redirection exotique
        return f"__ERR_{exc}__"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    before, after = sys.argv[1], sys.argv[2]

    pages = [p for p in git("diff", "--name-only", "--diff-filter=AM",
                            before, after).splitlines() if p.endswith(".mdx")]
    if not pages:
        print("Aucune page modifiée par ce push — rien à vérifier en ligne.")
        return 0

    targets: list[tuple[str, str]] = []
    for path in pages:
        w = witness(path, before, after)
        if w is None:
            print(f"  {path} : aucune phrase ajoutée, page non vérifiable")
            continue
        targets.append((path, w))

    if not targets:
        print("Aucun témoin utilisable : ce push ne touche que du balisage, du "
              "code ou du frontmatter — rien qui s'affiche comme une phrase "
              "dans le corps de la page. Rien à conclure, et rien à signaler.")
        return 0

    print(f"{len(targets)} page(s) à retrouver en ligne :")
    for path, w in targets:
        print(f"  {page_url(path)}\n      « {w} »")

    deadline = time.time() + DEADLINE_S
    pending = list(targets)
    while pending and time.time() < deadline:
        still: list[tuple[str, str]] = []
        for path, w in pending:
            if w in fetch(page_url(path)):
                print(f"  ✓ {path}")
            else:
                still.append((path, w))
        pending = still
        if pending:
            print(f"  … {len(pending)} en attente")
            time.sleep(INTERVAL_S)

    if not pending:
        print("\nLe site sert ce commit. Le déploiement automatique a suivi.")
        return 0

    print("\nCes pages ne servent toujours pas ce commit :")
    for path, w in pending:
        print(f"  {page_url(path)}\n      « {w} » introuvable")
    print("\nLe déploiement automatique de Mintlify n'a pas suivi. Regardez le")
    print("journal du projet : un `mint validate` en échec empêche la mise en")
    print("ligne, et c'est la cause la plus fréquente ici — c'est exactement ce")
    print("qui s'est passé le 08/09, une balise `</Steps>` fermée trop tôt.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
