/**
 * Formate un nombre avec des points comme séparateurs décimaux :
 * - Utilise le point comme séparateur décimal
 * - Utilise l'espace comme séparateur des milliers
 * @param num - Le nombre à formater
 * @param decimals - Nombre de décimales (optionnel, défaut auto avec max 1)
 * @returns Le nombre formaté
 */
export const formatNumberFrench = (
  num: number | null | undefined,
  decimals: number | null = null,
): string => {
  if (num === null || num === undefined || isNaN(num)) return "—";

  const number = Number(num);

  // Si decimals n'est pas spécifié, on utilise la logique avec maximum 1 décimale
  if (decimals === null) {
    if (Number.isInteger(number)) {
      // Pour les entiers, on utilise le formatage avec espaces pour les milliers
      return number.toLocaleString("fr-FR").replace(",", ".");
    } else {
      // Pour les décimaux, on garde maximum 1 décimale
      return number
        .toLocaleString("fr-FR", {
          minimumFractionDigits: 0,
          maximumFractionDigits: 1,
        })
        .replace(",", ".");
    }
  } else {
    // Si decimals est spécifié, on l'utilise
    return number
      .toLocaleString("fr-FR", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })
      .replace(",", ".");
  }
};

/**
 * Formate un nombre avec des espaces pour les milliers (sans décimales).
 * Utilisé pour les champs de saisie de nombres entiers.
 * @param num - Le nombre à formater
 * @returns Le nombre formaté avec espaces pour les milliers, ou chaîne vide si invalide
 */
export const formatNumberWithSpaces = (num: number): string => {
  if (typeof num !== "number" || isNaN(num)) return "";
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
};

/**
 * Formate une valeur de croissance/évolution en pourcentage.
 * Gère les valeurs décimales (0-1) et les pourcentages déjà formatés.
 * @param growth - Valeur de croissance (peut être décimal 0-1 ou pourcentage)
 * @returns Pourcentage formaté avec signe '+' si positif (ex: "+5.2%" ou "-3.1%")
 */
export const formatGrowth = (
  growth: number | string | null | undefined,
): string => {
  if (growth === null || growth === undefined || growth === "N/A") return "—";
  const growthValue = typeof growth === "string" ? parseFloat(growth) : growth;
  if (isNaN(growthValue)) return "—";
  // Si la valeur est entre 0 et 1, c'est un décimal, on le multiplie par 100
  const growthPercent = growthValue <= 1 ? growthValue * 100 : growthValue;
  const sign = growthPercent >= 0 ? "+" : "";
  return `${sign}${growthPercent.toFixed(1)}%`;
};

/**
 * Formate un taux de rotation en pourcentage.
 * Gère les valeurs décimales (0-1) et les pourcentages déjà formatés.
 * @param rate - Taux de rotation brut (peut être décimal 0-1 ou pourcentage)
 * @returns Pourcentage formaté (ex: "5.2%" ou "-3.1%")
 */
export const formatRotationRate = (
  rate: number | string | null | undefined,
): string => {
  if (
    rate === null ||
    rate === undefined ||
    rate === "A définir" ||
    rate === "N/A"
  ) {
    return "—";
  }

  const numericRate = typeof rate === "string" ? parseFloat(rate) : rate;

  if (Number.isNaN(numericRate)) {
    return "—";
  }

  // Si la valeur est entre 0 et 1, c'est un décimal, on le multiplie par 100
  const percentage =
    Math.abs(numericRate) <= 1 ? numericRate * 100 : numericRate;
  const sign = percentage >= 0 ? "" : "-";
  const absolutePercentage = Math.abs(percentage).toFixed(1);

  return `${sign}${absolutePercentage}%`;
};

/**
 * Formate un prix en euros avec formatage standard.
 * Utilise Intl.NumberFormat avec style currency pour un formatage cohérent.
 * @param price - Prix à formater
 * @returns Prix formaté (ex: "150 000 €") ou "—" si invalide
 */
export const formatPrice = (price: number | null | undefined): string => {
  if (price === null || price === undefined || isNaN(price)) return "—";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
};

/**
 * Formate un prix au m² en euros.
 * Alias de formatPrice pour compatibilité.
 * @param price - Prix au m² à formater
 * @returns Prix formaté (ex: "3 500 €") ou "—" si invalide
 */
export const formatPricePerSqm = formatPrice;

/**
 * Formate un montant avec unités adaptées (millions, milliards).
 * Pour les montants >= 1 Md €, affiche en milliards.
 * Pour les montants >= 1 M €, affiche en millions.
 * Sinon, utilise formatPrice.
 * @param amount - Montant à formater
 * @returns Montant formaté (ex: "1.5 M €", "2.3 Md €", "150 000 €") ou "—" si invalide
 */
export const formatAmount = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined || isNaN(amount)) return "—";
  if (amount <= 0) return "—";

  const numericAmount = Number(amount);

  if (numericAmount >= 1000000000) {
    const milliards = numericAmount / 1000000000;
    const formattedMilliards =
      milliards % 1 === 0
        ? Math.floor(milliards)
        : milliards.toFixed(1).replace(".", ",");
    return `${formattedMilliards} Md €`;
  }

  if (numericAmount >= 1000000) {
    const millions = numericAmount / 1000000;
    const formattedMillions =
      millions % 1 === 0
        ? Math.floor(millions)
        : millions.toFixed(1).replace(".", ",");
    return `${formattedMillions} M €`;
  }

  return formatPrice(numericAmount);
};

/**
 * Formate une taille de fichier en unité lisible (B, KB, MB, GB).
 * @param bytes - Taille en octets
 * @returns Taille formatée (ex: "1.5 MB", "256 KB") ou "0 B" si 0
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};
