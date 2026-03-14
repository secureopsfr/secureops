# Vérifications actives — Upload abuse

Ce document décrit les vérifications actives d'upload : type, extension, execution et traversal via nom de fichier.

---

## Contexte et méthodologie

### Objectif

Verifier que les mecanismes d'upload filtrent correctement type/contenu/nom et n'autorisent pas execution ou exposition non voulue.

### Tests

- MIME spoofing et double extension.
- Fichier malforme.
- Nom de fichier avec traversal.
- Acces direct au fichier upload.
- Verification de stockage hors webroot et des ACL de lecture.

---

## 1. Validation type/extension

### Résumé

Verifier que type MIME, extension et contenu reel sont coherents et controles.

### Exemple

- **OK** : fichiers non autorises rejetes.
- **Finding** : acceptation d'un fichier non autorise par spoof MIME.

## 2. Execution/serving insecurise

### Résumé

Verifier qu'un fichier upload ne peut pas etre execute/interprete cote serveur.

### Exemple

- **OK** : fichier servi comme binaire inerte.
- **Finding** : execution interpretee cote serveur.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne a forte.
- **Impact** : Importante a majeure.

### Matrice gravité / vraisemblance

<table style="border-collapse: collapse">
<thead><tr>
<th style="border:2px solid #1f2937; padding:8px">Gravité \ Vraisemblance</th>
<th style="border:2px solid #1f2937; padding:8px">Très faible</th>
<th style="border:2px solid #1f2937; padding:8px">Faible</th>
<th style="border:2px solid #1f2937; padding:8px">Forte</th>
<th style="border:2px solid #1f2937; padding:8px">Très forte</th>
</tr></thead>
<tbody>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Mineure</strong></td><td style="border:2px solid #1f2937; background-color:#22c55e"> </td><td style="border:2px solid #1f2937; background-color:#22c55e"> </td><td style="border:2px solid #1f2937; background-color:#facc15"> </td><td style="border:2px solid #1f2937; background-color:#facc15"> </td></tr>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Significative</strong></td><td style="border:2px solid #1f2937; background-color:#22c55e"> </td><td style="border:2px solid #1f2937; background-color:#facc15"> </td><td style="border:2px solid #1f2937; background-color:#f97316"> </td><td style="border:2px solid #1f2937; background-color:#f97316"> </td></tr>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Importante</strong></td><td style="border:2px solid #1f2937; background-color:#facc15"> </td><td style="border:2px solid #1f2937; background-color:#f97316"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td></tr>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Majeure</strong></td><td style="border:2px solid #1f2937; background-color:#f97316"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td></tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : élevé.**

### Conseils

- Validation triple (extension, MIME, signature fichier).
- Renommer fichiers (UUID), stocker hors document root.
- Interdire execution dans le repertoire d'upload.
- Servir via proxy de download controle.

### Références

- [OWASP – File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [CWE-434 – Unrestricted Upload](https://cwe.mitre.org/data/definitions/434.html)
