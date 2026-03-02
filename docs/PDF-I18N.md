# i18n du rapport PDF (fr/en)

Ce document décrit comment le rapport PDF gère les traductions et comment ajouter une nouvelle langue ou un nouveau finding.

## Architecture

- **`app/services/pdf_report/pdf_i18n.py`** : libellés UI (Sommaire, Preuve, Détail, Comment corriger, etc.)
- **`app/catalogue/recommendations.json`** : contenu des findings (titre, evidence, recommendation, detail) par slug

## Champs du catalogue par slug

Pour chaque finding (slug), le catalogue peut contenir :

| Champ | Description | Obligatoire |
|-------|-------------|-------------|
| `recommendation` | Recommandation en français | Oui (fallback) |
| `recommendation_en` | Recommandation en anglais | Non |
| `title_fr` | Titre en français | Non (sinon titre du finding) |
| `title_en` | Titre en anglais | Non |
| `evidence_fr` | Evidence en français | Non |
| `evidence_en` | Evidence en anglais | Non |
| `detail_fr` | Explication détaillée en français | Non |
| `detail_en` | Explication détaillée en anglais | Non |
| `references` | URLs de référence | Non |

## Ajouter un nouveau finding

1. Créer une entrée dans `app/catalogue/recommendations.json` avec au minimum `recommendation` et `references`.
2. Pour un PDF 100 % anglais avec `lang=en`, ajouter :
   - `recommendation_en`
   - `title_fr` et `title_en` (si le titre est fixe)
   - `evidence_fr` et `evidence_en` (si l'evidence est fixe)
   - `detail_fr` et `detail_en` (pour les explications longues)

## Ajouter une nouvelle langue

Actuellement seuls `fr` et `en` sont supportés. Pour une nouvelle langue (ex. `de`) :

1. Étendre `_PDF_STRINGS` dans `pdf_i18n.py` avec des clés `{"fr": "...", "en": "...", "de": "..."}`.
2. Étendre le catalogue avec `recommendation_de`, `title_de`, `evidence_de`, `detail_de`.
3. Adapter `_lang_key()` dans `recommendations.py` pour retourner la bonne clé selon la langue.
4. Mettre à jour `_normalize_lang()` dans `pdf_i18n.py` pour accepter la nouvelle langue.

## Fallback

- Si `title_en` est absent : on utilise le titre du finding (généralement en français).
- Si `evidence_en` est absent : on utilise l'evidence du finding.
- Si `recommendation_en` est absent : on utilise `recommendation` (français).
- Si `detail_en` est absent : on utilise `detail_fr` ou chaîne vide.
