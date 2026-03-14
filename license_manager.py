"""
GestionnaireRH Guinée - Système de Gestion des Licences
=========================================================
Auteur  : ICG Guinea
Version : 1.0.0

Ce module gère la validation des licences d'utilisation de GestionnaireRH.
Chaque licence est liée à l'identifiant unique de la machine.
"""

import os
import sys
import uuid
import hmac
import hashlib
import json
import base64
import socket
import platform
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Compatibilité Python 3.11+
def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

# ─── Clé secrète (obfusquée — ne pas modifier) ───────────────────────────────
def _gk():
    _d = [29,8,18,119,29,15,19,20,31,31,119,19,25,29,119,29,31,9,14,19,21,20,119,8,18,119,104,106,104,111,119,9,31,25,8,31,14,119,17,31,3,119,44,107]
    return bytes(x ^ 0x5A for x in _d)
_DEV_SECRET = _gk()
del _gk

# ─── Chemin de stockage de la licence ─────────────────────────────────────────
def _get_license_path() -> Path:
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    return base / 'license.dat'

def _get_appdata_license_path() -> Path:
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    folder = Path(appdata) / 'GestionnaireRH'
    folder.mkdir(parents=True, exist_ok=True)
    return folder / 'license.dat'

# ─── Identifiant machine ───────────────────────────────────────────────────────
def get_machine_id() -> str:
    """Génère un identifiant unique et stable pour cette machine."""
    parts = []

    # UUID Windows (registre)
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r'SOFTWARE\Microsoft\Cryptography')
        machine_guid, _ = winreg.QueryValueEx(key, 'MachineGuid')
        parts.append(machine_guid)
    except Exception:
        pass

    # Hostname
    try:
        parts.append(socket.gethostname())
    except Exception:
        pass

    # UUID du système
    try:
        parts.append(str(uuid.getnode()))
    except Exception:
        pass

    # Plateforme
    parts.append(platform.system() + platform.machine())

    combined = '|'.join(parts).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()[:32].upper()


def get_machine_id_short() -> str:
    """Version courte de 8 caractères pour affichage."""
    return get_machine_id()[:8]


# ─── Génération de fichier d'activation ───────────────────────────────────────
def generate_activation_file(machine_id: str, expiry_days: int = 365,
                               company_name: str = '', edition: str = 'Standard') -> dict:
    """
    Génère un fichier d'activation complet (à envoyer au client).
    """
    payload = {
        'mid': machine_id,
        'exp': (_now_utc() + timedelta(days=expiry_days)).strftime('%Y%m%d'),
        'company': company_name[:60],
        'edition': edition,
        'issued': _now_utc().strftime('%Y-%m-%d'),
        'issuer': 'ICG Guinea',
    }
    payload_str = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.b64encode(payload_str.encode()).decode()
    sig = hmac.new(_DEV_SECRET, payload_b64.encode(), hashlib.sha256).hexdigest().upper()

    return {
        'license_data': payload_b64,
        'signature': sig,
        'version': '1.0',
    }


# ─── Validation de licence ─────────────────────────────────────────────────────
def _validate_license_data(license_dict: dict) -> dict:
    """
    Valide un dictionnaire de licence.
    Retourne un dict avec 'valid', 'reason', 'payload'.
    """
    try:
        payload_b64 = license_dict.get('license_data', '')
        sig = license_dict.get('signature', '')

        if not payload_b64 or not sig:
            return {'valid': False, 'reason': 'Fichier de licence incomplet.'}

        # Vérifier la signature
        expected_sig = hmac.new(
            _DEV_SECRET, payload_b64.encode(), hashlib.sha256
        ).hexdigest().upper()

        if not hmac.compare_digest(sig.upper(), expected_sig):
            return {'valid': False, 'reason': 'Signature de licence invalide.'}

        # Décoder le payload
        payload = json.loads(base64.b64decode(payload_b64).decode())
        machine_id = get_machine_id()

        # Vérifier la machine (tolérance : 16 premiers chars)
        if payload.get('mid', '')[:16] != machine_id[:16]:
            return {'valid': False, 'reason': 'Cette licence appartient à une autre machine.'}

        # Vérifier l'expiration
        exp_str = payload.get('exp', '20000101')
        exp_date = datetime.strptime(exp_str, '%Y%m%d')
        now = _now_utc()
        days_left = (exp_date - now).days

        if days_left < 0:
            return {
                'valid': False,
                'reason': f"Licence expirée depuis {abs(days_left)} jour(s).",
                'payload': payload,
            }

        return {
            'valid': True,
            'reason': 'Licence valide.',
            'payload': payload,
            'days_left': days_left,
            'company': payload.get('company', ''),
            'edition': payload.get('edition', 'Standard'),
        }

    except Exception as e:
        return {'valid': False, 'reason': f'Erreur lors de la validation : {e}'}


def load_and_validate_license() -> dict:
    """
    Charge et valide la licence depuis les emplacements connus.
    """
    for path in [_get_license_path(), _get_appdata_license_path()]:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    license_dict = json.load(f)
                result = _validate_license_data(license_dict)
                result['license_path'] = str(path)
                return result
            except Exception:
                continue

    return {
        'valid': False,
        'reason': 'Aucune licence trouvée. Veuillez activer votre copie.',
    }


def save_license(license_dict: dict) -> bool:
    """Sauvegarde la licence dans les emplacements standards."""
    for path in [_get_license_path(), _get_appdata_license_path()]:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(license_dict, f, indent=2)
            return True
        except Exception:
            continue
    return False


def activate_from_file(activation_file_path: str) -> dict:
    """
    Active la licence depuis un fichier .lic fourni par le distributeur.
    """
    try:
        with open(activation_file_path, 'r', encoding='utf-8') as f:
            license_dict = json.load(f)
        result = _validate_license_data(license_dict)
        if result['valid']:
            if save_license(license_dict):
                return {**result, 'message': 'Licence activée avec succès !'}
            else:
                return {'valid': False, 'reason': 'Impossible de sauvegarder la licence.'}
        return result
    except Exception as e:
        return {'valid': False, 'reason': f'Erreur lecture du fichier : {e}'}


# ─── Mode essai (30 jours sans licence) ───────────────────────────────────────
_TRIAL_FILE_NAME = '.trial_start'

def get_or_create_trial() -> dict:
    """Gère une période d'essai de 30 jours sans licence."""
    trial_paths = [
        _get_license_path().parent / _TRIAL_FILE_NAME,
        _get_appdata_license_path().parent / _TRIAL_FILE_NAME,
    ]

    trial_start = None
    for tp in trial_paths:
        if tp.exists():
            try:
                with open(tp, 'r') as f:
                    trial_start = datetime.strptime(f.read().strip(), '%Y-%m-%d')
                break
            except Exception:
                continue

    if trial_start is None:
        trial_start = _now_utc()
        for tp in trial_paths:
            try:
                with open(tp, 'w') as f:
                    f.write(trial_start.strftime('%Y-%m-%d'))
                break
            except Exception:
                continue

    days_elapsed = (_now_utc() - trial_start).days
    days_left = max(0, 30 - days_elapsed)

    return {
        'trial': True,
        'valid': days_left > 0,
        'days_left': days_left,
        'days_elapsed': days_elapsed,
        'reason': (
            f"Mode essai : {days_left} jour(s) restant(s)."
            if days_left > 0
            else "Période d'essai expirée. Veuillez acheter une licence."
        ),
    }


# ─── Point d'entrée principal ──────────────────────────────────────────────────
def check_license_or_trial() -> dict:
    """
    Vérifie la licence. Si absente, démarre/continue le mode essai.
    """
    result = load_and_validate_license()
    if result['valid']:
        return result
    return get_or_create_trial()


# ─── Outil CLI (usage développeur) ────────────────────────────────────────────
if __name__ == '__main__':
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\nGestionnaireRH - Gestionnaire de Licences")
    print("Auteur : ICG Guinea")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nUsages :")
        print("  python license_manager.py info")
        print("  python license_manager.py generate <machine_id> <jours> <entreprise> <edition>")
        print("  python license_manager.py activate <fichier.lic>")
        print("  python license_manager.py check")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'info':
        mid = get_machine_id()
        print(f"\nID Machine complet : {mid}")
        print(f"ID Machine court   : {get_machine_id_short()}")
        print(f"\nFournissez l'ID complet à ICG Guinea pour obtenir une licence.")

    elif cmd == 'generate':
        if len(sys.argv) < 4:
            print("Usage: python license_manager.py generate <machine_id> <jours> [entreprise] [edition]")
            sys.exit(1)
        machine_id = sys.argv[2]
        days = int(sys.argv[3])
        company = sys.argv[4] if len(sys.argv) > 4 else ''
        edition = sys.argv[5] if len(sys.argv) > 5 else 'Standard'

        lic_data = generate_activation_file(machine_id, days, company, edition)
        output_file = f'licence_{machine_id[:8]}.lic'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(lic_data, f, indent=2)
        print(f"\nLicence générée : {output_file}")
        print(f"  Machine    : {machine_id}")
        print(f"  Entreprise : {company}")
        print(f"  Édition    : {edition}")
        print(f"  Durée      : {days} jours")

    elif cmd == 'activate':
        if len(sys.argv) < 3:
            print("Usage: python license_manager.py activate <fichier.lic>")
            sys.exit(1)
        result = activate_from_file(sys.argv[2])
        if result['valid']:
            print(f"\nLicence activee : {result.get('message', '')}")
        else:
            print(f"\nEchec : {result['reason']}")
            sys.exit(1)

    elif cmd == 'check':
        mid = get_machine_id()
        status = check_license_or_trial()
        print(f"\nID Machine : {mid}")
        print(f"Statut     : {'Valide' if status.get('valid') else 'Invalide'}")
        print(f"Detail     : {status.get('reason', '')}")
