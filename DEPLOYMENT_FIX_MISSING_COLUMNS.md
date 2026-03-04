# Instructions de déploiement - Fix colonnes manquantes

## Problème
L'erreur `(1054, "Colonne inconnue 'bulletins_paie.abattement_forfaitaire'")` indique que les colonnes ajoutées en développement n'existent pas sur le serveur de production.

## Solution √ (Recommandée: Exécuter Django Migration)

### Option 1: Via Django (Préféré - applique toutes les migrations)

Connectez-vous au serveur et exécutez:

```bash
cd /home/guineerh/gestionrh
source venv/bin/activate
python manage.py migrate paie
```

Cela va:
- Appliquer la migration `0110_bulletinpaie_abattement_forfaitaire_and_more.py`
- Créer les 3 colonnes manquantes de manière sûre
- Mettre à jour le schéma Django

### Option 2: Script SQL Direct (Si Django Migration échoue)

Si la migration Django échoue, exécutez directement le script SQL:

```bash
mysql -h localhost -u root -p gestionrh < /path/to/add_missing_columns.sql
```

Ou depuis votre client MySQL:

```sql
-- Copier-coller le contenu de add_missing_columns.sql
ALTER TABLE bulletins_paie 
ADD COLUMN IF NOT EXISTS abattement_forfaitaire DECIMAL(15, 2) DEFAULT 0.00;

ALTER TABLE bulletins_paie 
ADD COLUMN IF NOT EXISTS base_vf DECIMAL(15, 2) DEFAULT 0.00;

ALTER TABLE bulletins_paie 
ADD COLUMN IF NOT EXISTS nombre_salaries INT DEFAULT 0;
```

## Vérification √

Après application, vérifiez que les colonnes existent:

```sql
DESCRIBE bulletins_paie;
-- Ou
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'bulletins_paie' 
AND COLUMN_NAME IN ('abattement_forfaitaire', 'base_vf', 'nombre_salaries');
```

Vous devriez voir 3 lignes d'affichage.

## Après la migration

1. Redémarrez l'application Django/uWSGI:
```bash
sudo systemctl restart uwsgi-gestionrh
sudo systemctl restart nginx  # ou apache2
```

2. Testez en accédant à `/paie/periodes/11/`
   - L'erreur 1054 doit disparaître
   - Les bulletins s'affichent avec tous les champs

## Migration appliquée: 
- Fichier: `paie/migrations/0110_bulletinpaie_abattement_forfaitaire_and_more.py`
- Colonnes:
  - `abattement_forfaitaire` (Decimal 15,2) - Abattement 25% RTS
  - `base_vf` (Decimal 15,2) - Base de calcul Versement Forfaitaire
  - `nombre_salaries` (Integer) - Effectif entreprise pour TA/ONFPP

## Support
Si vous avez un doute:
1. Commencez par `python manage.py migrate paie` (plus sûr)
2. Si ça échoue, utilisez le script SQL
3. Vérifiez à chaque étape que les colonnes sont présentes
