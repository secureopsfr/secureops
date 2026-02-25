/**
 * Utilitaire de logging centralisé avec niveaux configurables par environnement.
 *
 * Niveaux de log (du plus verbeux au moins verbeux) :
 *   debug < log < warn < error < silent
 *
 * - En développement : niveau "debug" (tous les logs)
 * - En production : niveau "warn" (seulement warn et error)
 * - Configurable via NEXT_PUBLIC_LOG_LEVEL
 *
 * Adapté pour Next.js
 */

const LOG_LEVELS = {
  debug: 0,
  log: 1,
  info: 1,
  warn: 2,
  error: 3,
  silent: 4,
} as const;

type LogLevel = keyof typeof LOG_LEVELS;

const isProduction = process.env.NODE_ENV === "production";

/**
 * Détermine le niveau de log actif en fonction de l'environnement.
 * Priorité : NEXT_PUBLIC_LOG_LEVEL > valeur par défaut selon NODE_ENV
 */
const getLogLevel = (): LogLevel => {
  const envLevel = process.env.NEXT_PUBLIC_LOG_LEVEL as LogLevel | undefined;
  if (envLevel && envLevel in LOG_LEVELS) {
    return envLevel;
  }
  return isProduction ? "warn" : "debug";
};

const currentLevel = getLogLevel();

const shouldLog = (level: LogLevel): boolean => {
  return LOG_LEVELS[level] >= LOG_LEVELS[currentLevel];
};

/**
 * Logger de débogage.
 * Affiché uniquement si le niveau est "debug".
 */
export const debug = (...args: unknown[]) => {
  if (shouldLog("debug")) {
    console.debug("[DEBUG]", ...args);
  }
};

/**
 * Logger standard.
 * Affiché si le niveau est "log" ou inférieur.
 */
export const log = (...args: unknown[]) => {
  if (shouldLog("log")) {
    console.log(...args);
  }
};

/**
 * Logger d'information.
 * Même niveau que log, alias sémantique.
 */
export const info = (...args: unknown[]) => {
  if (shouldLog("info")) {
    console.info("[INFO]", ...args);
  }
};

/**
 * Logger d'avertissement.
 * Affiché si le niveau est "warn" ou inférieur.
 */
export const warn = (...args: unknown[]) => {
  if (shouldLog("warn")) {
    console.warn(...args);
  }
};

/**
 * Logger d'erreur.
 * Toujours affiché sauf en mode "silent".
 */
export const error = (...args: unknown[]) => {
  if (shouldLog("error")) {
    console.error(...args);
  }
};

/**
 * Vérifie si on est en mode production.
 */
export const isProd = () => isProduction;

/**
 * Retourne le niveau de log actuel.
 */
export const getLevel = () => currentLevel;

const logger = { debug, log, info, warn, error, isProd, getLevel };
export default logger;
