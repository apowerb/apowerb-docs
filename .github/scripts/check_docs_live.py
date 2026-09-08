#!/usr/bin/env python3
"""Le site sert-il ce qui vient d'etre merge ?

L'API de declenchement de Mintlify demande un plan superieur -- elle rend
`401 {"error":"Please upgrade to access this route."}`. Mais Mintlify deploie
ce depot tout seul, mesure le 08/09/2026 : deux merges consecutifs (#7 a 15h11,
#8 a 15h15) etaient en ligne dix minutes plus tard sans geste manuel.

Alors plutot que de declencher la publication, ce controle verifie la
propriete qui compte vraiment : la page servie contient ce que le commit a
ecrit. Il teste le resultat, pas le mecanisme -- et il reste vrai quel que
soit le plan, l'API ou le mode de deploiement.

Les << Failed >> vus dans le journal Mintlify ce matin n'etaient d'ailleurs
pas une panne de deploiement : le depot portait une balise `</Steps>` fermee
trop tot, `mint validate` echouait, et le contenu invalide ne partait pas.
Le contenu etait en cause, pas le tuyau.

Usage :
    check_docs_live.py <sha_avant> <sha_apres>
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

SITE = "https://docs.apowerb.com"
# Mintlify construit et propage : quelques minutes en temps normal, et
# au-dela c'est une panne, pas de la lenteur.
# Reglables pour eprouver le chemin rouge sans attendre dix minutes.
DEADLINE_S = int(os.environ.get("DOCS_LIVE_DEADLINE", "600"))
INTERVAL_S = int(os.environ.get("DOCS_LIVE_INTERVAL", "20"))

# Un mot assez long pour ne pas apparaitre par hasard, et assez simple pour
# traverser le rendu : Mintlify decoupe le code en `<span>` par coloration
# syntaxique, ce qui casse toute recherche de PHRASE, mais laisse les mots
# entiers.
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{11,}")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout


def changed_pages(before: str, after: str) -> list[str]:
    out = git("diff", "--name-only", "--diff-filter=AM", before, after)
    return [p for p in out.splitlines() if p.endswith(".mdx")]


def witness(path: str, before: str, after: str) -> str | None:
    """Un mot ajoute par ce commit, absent de la version d'avant.

    Absent d'avant : sinon on prouverait seulement que la page existait deja.
    """
    try:
        old = git("show", f"{before}:{path}")
    except subprocess.CalledProcessError:
        old = ""  # fichier nouveau
    new = git("show", f"{after}:{path}")

    added = {w for w in WORD_RE.findall(new)} - {w for w in WORD_RE.findall(old)}
    if not added:
        return None
    # Le plus long : le plus improbable ailleurs sur la page.
    return max(added, key=len)


def page_url(path: str) -> str:
    return f"{SITE}/{path[:-len('.mdx')]}"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "docs-live-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return f"__HTTP_{exc.code}__"
    except Exception as exc:  # reseau, TLS, redirection exotique
        return f"__ERR_{exc}__"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    before, after = sys.argv[1], sys.argv[2]

    pages = changed_pages(before, after)
    if not pages:
        print("Aucune page modifiée par ce push — rien à vérifier en ligne.")
        return 0

    targets: list[tuple[str, str]] = []
    for path in pages:
        w = witness(path, before, after)
        if w is None:
            print(f"  {path} : aucun mot distinctif ajouté, page non vérifiable")
            continue
        targets.append((path, w))

    if not targets:
        print("Aucun témoin utilisable — modification trop courte ou purement "
              "structurelle. Rien à conclure, et rien à signaler.")
        return 0

    print(f"{len(targets)} page(s) à retrouver en ligne :")
    for path, w in targets:
        print(f"  {page_url(path)}  ← « {w} »")

    deadline = time.time() + DEADLINE_S
    pending = list(targets)
    while pending and time.time() < deadline:
        still: list[tuple[str, str]] = []
        for path, w in pending:
            body = fetch(page_url(path))
            if w in body:
                print(f"  ✓ {path}")
            else:
                still.append((path, w))
        pending = still
        if pending:
            waited = int(DEADLINE_S - (deadline - time.time()))
            print(f"  … {len(pending)} en attente ({waited}s)")
            time.sleep(INTERVAL_S)

    if not pending:
        print("\nLe site sert ce commit. Le déploiement automatique a suivi.")
        return 0

    print("\nCes pages ne servent toujours pas ce commit :")
    for path, w in pending:
        print(f"  {page_url(path)} — « {w} » introuvable")
    print("\nLe déploiement automatique de Mintlify n'a pas suivi. Regardez le")
    print("journal du projet : un `mint validate` en échec empêche la mise en")
    print("ligne, et c'est la cause la plus fréquente ici. Sinon, un")
    print("« Manual update » depuis le tableau de bord débloque la situation.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
