"""
GestionnaireRH Guinée — Système de Protection Anti-Vol & Anti-Falsification
=============================================================================
Auteur  : ICG Guinea
Version : 2.0.0

Ce module protège le projet contre :
  1. Vol du code source et redistribution non autorisée
  2. Modification / falsification du code par des développeurs tiers
  3. Génération de licences non autorisée (seule la machine propriétaire peut générer)
  4. Contournement du système de licence
  5. Manipulation des fichiers critiques

AVERTISSEMENT LÉGAL :
  Ce logiciel est la propriété exclusive de ICG Guinea.
  Toute copie, modification, redistribution ou ingénierie inverse
  est strictement interdite et constitue une violation du droit d'auteur.
  Les contrevenants s'exposent à des poursuites judiciaires.
"""

import os
import sys
import hmac
import json
import hashlib
import socket
import platform
import uuid
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger('project_guardian')

# ─── Empreinte de la machine propriétaire (obfusquée) ─────────────────────────
# Seule cette machine peut générer des licences et modifier le projet.
# L'empreinte est fragmentée et vérifiée dynamiquement.
def _rk():
    """Reconstruit l'empreinte propriétaire (fragments obfusqués)."""
    _f = [
        bytes([0x41 ^ 0x00, 0x44 ^ 0x00, 0x30 ^ 0x00, 0x41 ^ 0x00]),
        bytes([0x36 ^ 0x00, 0x35 ^ 0x00, 0x35 ^ 0x00, 0x36 ^ 0x00]),
        bytes([0x41 ^ 0x00, 0x42 ^ 0x00, 0x43 ^ 0x00, 0x30 ^ 0x00]),
        bytes([0x33 ^ 0x00, 0x31 ^ 0x00, 0x33 ^ 0x00, 0x37 ^ 0x00]),
        bytes([0x36 ^ 0x00, 0x42 ^ 0x00, 0x38 ^ 0x00, 0x43 ^ 0x00]),
        bytes([0x43 ^ 0x00, 0x31 ^ 0x00, 0x34 ^ 0x00, 0x30 ^ 0x00]),
        bytes([0x31 ^ 0x00, 0x39 ^ 0x00, 0x44 ^ 0x00, 0x41 ^ 0x00]),
        bytes([0x31 ^ 0x00, 0x33 ^ 0x00, 0x30 ^ 0x00, 0x42 ^ 0x00]),
    ]
    return b''.join(_f).decode('ascii')

_OWNER_FINGERPRINT = _rk()
del _rk

# ─── Clé secrète interne pour la signature d'intégrité (obfusquée) ────────────
def _ik():
    """Reconstruit la clé de signature d'intégrité."""
    _d = [73, 67, 71, 45, 71, 117, 105, 110, 101, 97, 45, 80, 114, 111,
          116, 101, 99, 116, 105, 111, 110, 45, 50, 48, 50, 53, 45,
          65, 110, 116, 105, 84, 104, 101, 102, 116]
    return bytes(_d)

_INTEGRITY_KEY = _ik()
del _ik

# ─── Watermark propriétaire (encodé dans chaque vérification) ─────────────────
_WATERMARK = "© 2025 ICG Guinea - GestionnaireRH - Tous droits réservés - Licence propriétaire"
_WATERMARK_HASH = hashlib.sha256(_WATERMARK.encode()).hexdigest()

# ─── Obtention de l'ID machine local ──────────────────────────────────────────
def _get_local_machine_id() -> str:
    """Génère un identifiant unique et stable pour cette machine."""
    parts = []
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r'SOFTWARE\Microsoft\Cryptography')
        machine_guid, _ = winreg.QueryValueEx(key, 'MachineGuid')
        parts.append(machine_guid)
    except Exception:
        pass
    try:
        parts.append(socket.gethostname())
    except Exception:
        pass
    try:
        parts.append(str(uuid.getnode()))
    except Exception:
        pass
    parts.append(platform.system() + platform.machine())
    combined = '|'.join(parts).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()[:32].upper()


# ─── Vérification : est-ce la machine propriétaire ? ──────────────────────────
def is_owner_machine() -> bool:
    """Vérifie si l'exécution a lieu sur la machine du propriétaire."""
    try:
        local_id = _get_local_machine_id()
        return hmac.compare_digest(local_id, _OWNER_FINGERPRINT)
    except Exception:
        return False


# ─── Liste des fichiers critiques à protéger ──────────────────────────────────
def _get_project_root() -> Path:
    """Retourne le dossier racine du projet."""
    if getattr(sys, 'frozen', False):
        # En mode PyInstaller, les fichiers .py sont dans _internal/
        internal = Path(sys.executable).parent / '_internal'
        if internal.exists():
            return internal
        return Path(sys.executable).parent
    return Path(__file__).parent


CRITICAL_FILES = [
    'license_manager.py',
    'project_guardian.py',
    'run_server.py',
    'manage.py',
    'core/middleware_licence.py',
    'core/middleware.py',
    'core/decorators.py',
    'core/models_licence.py',
    'gestionnaire_rh/settings.py',
]


# ─── Calcul du hash d'un fichier ──────────────────────────────────────────────
def _hash_file(filepath: Path) -> str:
    """Calcule le SHA-256 HMAC signé d'un fichier."""
    try:
        content = filepath.read_bytes()
        return hmac.new(_INTEGRITY_KEY, content, hashlib.sha256).hexdigest()
    except Exception:
        return ''


# ─── Génération de la carte d'intégrité ───────────────────────────────────────
def generate_integrity_manifest() -> dict:
    """
    Génère une carte d'intégrité de tous les fichiers critiques.
    RÉSERVÉ à la machine propriétaire uniquement.
    """
    if not is_owner_machine():
        raise PermissionError(
            "ACCÈS REFUSÉ : Seule la machine propriétaire ICG Guinea peut "
            "générer la carte d'intégrité du projet."
        )

    root = _get_project_root()
    manifest = {
        'version': '2.0.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'machine_id': _get_local_machine_id()[:8],
        'watermark': _WATERMARK_HASH,
        'files': {},
    }

    for rel_path in CRITICAL_FILES:
        fpath = root / rel_path
        if fpath.exists():
            manifest['files'][rel_path] = _hash_file(fpath)

    # Signer le manifest complet
    manifest_str = json.dumps(manifest['files'], sort_keys=True)
    manifest['signature'] = hmac.new(
        _INTEGRITY_KEY, manifest_str.encode(), hashlib.sha256
    ).hexdigest()

    return manifest


def save_integrity_manifest(output_path: str = None):
    """
    Sauvegarde la carte d'intégrité dans un fichier.
    RÉSERVÉ à la machine propriétaire.
    """
    manifest = generate_integrity_manifest()
    if output_path is None:
        output_path = str(_get_project_root() / '.integrity_manifest.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    return output_path


# ─── Vérification de l'intégrité du projet ────────────────────────────────────
def verify_project_integrity() -> dict:
    """
    Vérifie que les fichiers critiques n'ont pas été modifiés.
    Retourne un dict avec 'intact', 'tampered_files', 'missing_files'.
    """
    root = _get_project_root()
    manifest_path = root / '.integrity_manifest.json'
    result = {
        'intact': True,
        'tampered_files': [],
        'missing_files': [],
        'missing_manifest': False,
        'signature_valid': True,
    }

    if not manifest_path.exists():
        result['intact'] = False
        result['missing_manifest'] = True
        return result

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception:
        result['intact'] = False
        result['missing_manifest'] = True
        return result

    # Vérifier la signature du manifest lui-même
    stored_sig = manifest.get('signature', '')
    files_data = manifest.get('files', {})
    expected_sig = hmac.new(
        _INTEGRITY_KEY,
        json.dumps(files_data, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(stored_sig, expected_sig):
        result['intact'] = False
        result['signature_valid'] = False
        return result

    # Vérifier le watermark
    if manifest.get('watermark') != _WATERMARK_HASH:
        result['intact'] = False
        result['signature_valid'] = False
        return result

    # Vérifier chaque fichier critique
    for rel_path, expected_hash in files_data.items():
        fpath = root / rel_path
        if not fpath.exists():
            result['missing_files'].append(rel_path)
            result['intact'] = False
        else:
            current_hash = _hash_file(fpath)
            if not hmac.compare_digest(current_hash, expected_hash):
                result['tampered_files'].append(rel_path)
                result['intact'] = False

    return result


# ─── Vérification anti-contournement ──────────────────────────────────────────
def _check_anti_bypass() -> bool:
    """
    Vérifie que les mécanismes de protection n'ont pas été contournés.
    Détecte les tentatives de monkey-patching et injection.
    """
    try:
        # Vérifier que le module license_manager existe et n'est pas un mock
        import license_manager
        if not hasattr(license_manager, '_DEV_SECRET'):
            return False
        if not hasattr(license_manager, 'get_machine_id'):
            return False
        if not callable(license_manager.get_machine_id):
            return False

        # Vérifier que les fonctions critiques ne sont pas remplacées par des stubs
        mid = license_manager.get_machine_id()
        if not mid or len(mid) < 16:
            return False

        return True
    except ImportError:
        return False
    except Exception:
        return False


# ─── Vérification anti-débogage (basique) ─────────────────────────────────────
def _check_anti_debug() -> bool:
    """Détecte certaines tentatives de débogage/instrumentation."""
    # Vérifier si un débogueur Python est attaché
    if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
        # Autorisé seulement sur la machine propriétaire
        if not is_owner_machine():
            return False
    return True


# ─── Vérification combinée complète ───────────────────────────────────────────
def full_security_check() -> dict:
    """
    Exécute une vérification de sécurité complète.
    Retourne un rapport avec le statut de chaque vérification.
    """
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'machine_id': _get_local_machine_id()[:8],
        'is_owner': is_owner_machine(),
        'checks': {},
        'blocked': False,
        'reason': '',
    }

    # 1) Intégrité des fichiers
    integrity = verify_project_integrity()
    report['checks']['integrity'] = integrity

    # 2) Anti-contournement
    anti_bypass = _check_anti_bypass()
    report['checks']['anti_bypass'] = anti_bypass

    # 3) Anti-débogage
    anti_debug = _check_anti_debug()
    report['checks']['anti_debug'] = anti_debug

    # 4) Vérification du watermark
    report['checks']['watermark'] = _WATERMARK_HASH

    # Décision de blocage
    if not integrity['intact']:
        report['blocked'] = True
        if integrity.get('missing_manifest'):
            report['reason'] = (
                "ALERTE SÉCURITÉ : Le fichier de vérification d'intégrité est manquant. "
                "Contactez ICG Guinea pour obtenir une copie authentique."
            )
        elif not integrity.get('signature_valid'):
            report['reason'] = (
                "ALERTE SÉCURITÉ : La signature d'intégrité est invalide. "
                "Le projet a été falsifié."
            )
        elif integrity['tampered_files']:
            files = ', '.join(integrity['tampered_files'])
            report['reason'] = (
                f"ALERTE SÉCURITÉ : Fichiers modifiés détectés : {files}. "
                "Le projet a été altéré par un tiers non autorisé."
            )
        elif integrity['missing_files']:
            files = ', '.join(integrity['missing_files'])
            report['reason'] = (
                f"ALERTE SÉCURITÉ : Fichiers critiques manquants : {files}."
            )

    if not anti_bypass:
        report['blocked'] = True
        report['reason'] = (
            "ALERTE SÉCURITÉ : Le système de licence a été altéré ou contourné. "
            "Contactez ICG Guinea."
        )

    if not anti_debug:
        report['blocked'] = True
        report['reason'] = (
            "ALERTE SÉCURITÉ : Tentative de débogage non autorisée détectée."
        )

    if report['blocked']:
        logger.critical(
            "GUARDIAN BLOCK | machine=%s | reason=%s",
            report['machine_id'], report['reason']
        )

    return report


# ─── Protection de la génération de licence ────────────────────────────────────
def guard_license_generation():
    """
    Vérification de sécurité avant toute génération de licence.
    Bloque si exécuté sur une machine non autorisée.
    """
    if not is_owner_machine():
        machine_id = _get_local_machine_id()[:8]
        logger.critical(
            "TENTATIVE DE GÉNÉRATION DE LICENCE NON AUTORISÉE | machine=%s",
            machine_id
        )
        raise PermissionError(
            "\n╔══════════════════════════════════════════════════════════════╗\n"
            "║  ACCÈS REFUSÉ — GÉNÉRATION DE LICENCE NON AUTORISÉE       ║\n"
            "║                                                            ║\n"
            "║  Cette opération est réservée exclusivement à la machine   ║\n"
            "║  propriétaire de ICG Guinea.                               ║\n"
            "║                                                            ║\n"
            "║  Votre machine n'est PAS autorisée à générer des licences. ║\n"
            "║  Toute tentative est journalisée et signalée.              ║\n"
            "║                                                            ║\n"
            f"║  Machine détectée : {machine_id:<39}║\n"
            "║                                                            ║\n"
            "║  Contactez ICG Guinea pour obtenir une licence valide.     ║\n"
            "╚══════════════════════════════════════════════════════════════╝\n"
        )
    return True


# ─── Watermark du code source ──────────────────────────────────────────────────
def embed_watermark(data: dict) -> dict:
    """Ajoute un watermark ICG Guinea invisible dans les données de licence."""
    data['_wm'] = hashlib.sha256(
        (_WATERMARK + str(time.time())).encode()
    ).hexdigest()[:16]
    data['_origin'] = 'ICG-GN'
    return data


def verify_watermark(data: dict) -> bool:
    """Vérifie la présence du watermark ICG Guinea."""
    return data.get('_origin') == 'ICG-GN' and '_wm' in data


# ─── Point d'entrée CLI ───────────────────────────────────────────────────────
if __name__ == '__main__':
    import io
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\n" + "=" * 60)
    print("  GESTIONNAIRE RH GUINÉE — GUARDIAN DE SÉCURITÉ")
    print("  © 2025 ICG Guinea — Tous droits réservés")
    print("=" * 60)

    machine_id = _get_local_machine_id()
    owner = is_owner_machine()
    print(f"\n  Machine ID   : {machine_id}")
    print(f"  Propriétaire : {'OUI ✓' if owner else 'NON ✗'}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == 'check':
            print("\n  Vérification de sécurité en cours...")
            report = full_security_check()
            integrity = report['checks']['integrity']
            print(f"  Intégrité    : {'OK ✓' if integrity['intact'] else 'ÉCHEC ✗'}")
            print(f"  Anti-bypass  : {'OK ✓' if report['checks']['anti_bypass'] else 'ÉCHEC ✗'}")
            print(f"  Anti-debug   : {'OK ✓' if report['checks']['anti_debug'] else 'ÉCHEC ✗'}")
            if integrity.get('tampered_files'):
                print(f"  Fichiers modifiés : {', '.join(integrity['tampered_files'])}")
            if integrity.get('missing_files'):
                print(f"  Fichiers manquants : {', '.join(integrity['missing_files'])}")
            if report['blocked']:
                print(f"\n  ⛔ BLOQUÉ : {report['reason']}")
            else:
                print(f"\n  ✓ Toutes les vérifications sont passées.")

        elif cmd == 'sign':
            if not owner:
                print("\n  ⛔ ACCÈS REFUSÉ : Seule la machine propriétaire peut signer le projet.")
                sys.exit(1)
            print("\n  Génération de la carte d'intégrité...")
            path = save_integrity_manifest()
            print(f"  ✓ Carte d'intégrité sauvegardée : {path}")
            # Vérifie immédiatement
            integrity = verify_project_integrity()
            print(f"  Vérification : {'OK ✓' if integrity['intact'] else 'ÉCHEC ✗'}")

        else:
            print(f"\n  Commande inconnue : {cmd}")
            print("  Commandes : check, sign")
    else:
        print("\n  Commandes :")
        print("    python project_guardian.py check  — Vérifier l'intégrité")
        print("    python project_guardian.py sign   — Signer le projet (propriétaire)")
