from decimal import Decimal, ROUND_HALF_UP


def money(value) -> Decimal:
    """
    Arrondi standard GNF — règle d'or GestionRH :
    - Calculs internes : précision maximale (Decimal)
    - Résultat final   : arrondi ROUND_HALF_UP
    - Répartition      : dernier élément absorbe le reste
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def money_int(value) -> int:
    """Retourne un int GNF — pour les contextes qui attendent un entier."""
    return int(money(value))
