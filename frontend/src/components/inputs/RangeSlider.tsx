"use client";

import React, { useState, useEffect, useCallback } from "react";
import { formatNumberWithSpaces } from "../../utils/numberFormatter";

// Fonction pour parser et nettoyer les nombres
const parseNumberInput = (input: string): number | null => {
  // Supprimer tous les espaces et caractères non numériques
  const cleaned = input.replace(/[^\d]/g, "");
  const num = parseInt(cleaned, 10);
  return isNaN(num) ? null : num;
};

interface RangeValue {
  min: number;
  max: number;
}

interface RangeSliderProps {
  label: string;
  value: RangeValue | null;
  onChange: (value: RangeValue) => void;
  min: number;
  max: number;
  scale?: number[];
  formatValue?: (value: RangeValue) => string;
  minBoundLabel?: string;
  maxBoundLabel?: string;
  step?: number;
  showInputs?: boolean;
  unit?: string | null;
  showSlider?: boolean;
}

function RangeSlider({
  label,
  value,
  onChange,
  min,
  max,
  scale,
  formatValue,
  minBoundLabel,
  maxBoundLabel,
  step = 1,
  showInputs = true,
  unit = null,
  showSlider = true,
}: RangeSliderProps) {
  // État local pour les valeurs de saisie
  const [inputMin, setInputMin] = useState("");
  const [inputMax, setInputMax] = useState("");
  const [isReset, setIsReset] = useState(false);
  const [sliderMin, setSliderMin] = useState(min);
  const [sliderMax, setSliderMax] = useState(max);

  // Validation des valeurs
  const isValidValue =
    value &&
    typeof value === "object" &&
    typeof value.min === "number" &&
    typeof value.max === "number" &&
    !isNaN(value.min) &&
    !isNaN(value.max);

  const mapToDisplay = (v: number): number => (scale ? scale[v] : v);
  const mapFromDisplay = useCallback(
    (v: number): number => {
      if (!scale) return v;
      const index = scale.indexOf(v);
      return index !== -1 ? index : 0;
    },
    [scale],
  );

  // Mise à jour des valeurs du slider quand value change
  useEffect(() => {
    if (isValidValue && value) {
      if (scale) {
        setSliderMin(mapFromDisplay(value.min));
        setSliderMax(mapFromDisplay(value.max));
      } else {
        setSliderMin(value.min);
        setSliderMax(value.max);
      }
    } else {
      setSliderMin(min);
      setSliderMax(max);
    }
  }, [value, isValidValue, min, max, scale, mapFromDisplay]);

  const handleSliderChange = (type: "min" | "max", newValue: number) => {
    const clampedValue = Math.max(min, Math.min(max, newValue));

    if (type === "min") {
      setSliderMin(clampedValue);
      const displayValue = mapToDisplay(clampedValue);
      onChange({
        min: displayValue,
        max: value?.max ?? max,
      });
    } else {
      setSliderMax(clampedValue);
      const displayValue = mapToDisplay(clampedValue);
      onChange({
        min: value?.min ?? min,
        max: displayValue,
      });
    }
  };

  // Gestion des changements de saisie manuelle
  const handleInputChange = (type: "min" | "max", inputValue: string) => {
    if (isReset) {
      setIsReset(false);
    }

    if (type === "min") {
      setInputMin(inputValue);
    } else if (type === "max") {
      setInputMax(inputValue);
    }
  };

  // Gestion de la validation des champs (Enter ou perte de focus)
  const handleInputBlur = (type: "min" | "max") => {
    if (type === "min") {
      const numValue = parseNumberInput(inputMin);
      if (inputMin === "" || numValue === null) {
        // Champ vide ou invalide - garder vide
        return;
      }
      // Valider et contraindre la valeur
      const constrainedValue = Math.max(
        min,
        Math.min(value?.max ?? max, numValue),
      );
      // Formater la valeur valide
      setInputMin(formatNumberWithSpaces(constrainedValue));
      // Mettre à jour les filtres
      onChange({
        min: constrainedValue,
        max: value?.max ?? max,
      });
    } else if (type === "max") {
      const numValue = parseNumberInput(inputMax);
      if (inputMax === "" || numValue === null) {
        // Champ vide ou invalide - garder vide
        return;
      }
      // Valider et contraindre la valeur
      const constrainedValue = Math.max(
        value?.min ?? min,
        Math.min(max, numValue),
      );
      // Formater la valeur valide
      setInputMax(formatNumberWithSpaces(constrainedValue));
      // Mettre à jour les filtres
      onChange({
        min: value?.min ?? min,
        max: constrainedValue,
      });
    }
  };

  // Mise à jour des champs de saisie quand les valeurs changent (seulement depuis l'extérieur)
  useEffect(() => {
    // Si on vient de réinitialiser, ne pas remplir les champs
    if (isReset) return;

    if (value?.min !== undefined) {
      setInputMin(formatNumberWithSpaces(value.min));
    } else {
      setInputMin("");
    }

    if (value?.max !== undefined) {
      setInputMax(formatNumberWithSpaces(value.max));
    } else {
      setInputMax("");
    }
  }, [value, isReset]);

  const displayValue =
    isValidValue && value && formatValue ? formatValue(value) : "—";

  // Calcul du pourcentage pour le style du track
  const minPercent = ((sliderMin - min) / (max - min)) * 100;
  const maxPercent = ((sliderMax - min) / (max - min)) * 100;

  return (
    <div className="space-y-3">
      <div>
        <h4 className="text-sm font-medium text-[var(--text)]">{label}</h4>
        {displayValue && (
          <p className="text-sm text-[rgb(var(--primary))] opacity-80 mt-1">
            {displayValue}
          </p>
        )}
      </div>

      {/* Champs de saisie manuelle */}
      {showInputs && (
        <div className="flex gap-2 items-center">
          <div className="w-32">
            <label className="block text-sm text-[var(--muted)] mb-1">
              Minimum
            </label>
            <div className="relative">
              <input
                type="text"
                value={inputMin}
                onChange={(e) => handleInputChange("min", e.target.value)}
                onBlur={() => handleInputBlur("min")}
                onKeyPress={(e) =>
                  e.key === "Enter" && (e.target as HTMLInputElement).blur()
                }
                className={`w-full py-2 text-sm border border-[var(--border)] rounded-md bg-[var(--color-surface-input)] text-[var(--text)] focus:border-[rgba(var(--primary),0.5)] focus:outline-none focus:ring-2 focus:ring-[rgba(var(--primary),0.1)] ${
                  unit ? "pr-6 pl-3" : "px-3"
                }`}
                placeholder={formatNumberWithSpaces(min)}
              />
              {unit && (
                <span className="absolute right-2 top-1/2 transform -translate-y-1/2 text-xs text-[var(--muted)] pointer-events-none">
                  {unit}
                </span>
              )}
            </div>
          </div>
          <div className="w-32">
            <label className="block text-sm text-[var(--muted)] mb-1">
              Maximum
            </label>
            <div className="relative">
              <input
                type="text"
                value={inputMax}
                onChange={(e) => handleInputChange("max", e.target.value)}
                onBlur={() => handleInputBlur("max")}
                onKeyPress={(e) =>
                  e.key === "Enter" && (e.target as HTMLInputElement).blur()
                }
                className={`w-full py-2 text-sm border border-[var(--border)] rounded-md bg-[var(--color-surface-input)] text-[var(--text)] focus:border-[rgba(var(--primary),0.5)] focus:outline-none focus:ring-2 focus:ring-[rgba(var(--primary),0.1)] ${
                  unit ? "pr-6 pl-3" : "px-3"
                }`}
                placeholder={formatNumberWithSpaces(max)}
              />
              {unit && (
                <span className="absolute right-2 top-1/2 transform -translate-y-1/2 text-xs text-[var(--muted)] pointer-events-none">
                  {unit}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Slider personnalisé */}
      {showSlider && (
        <div className="px-2 py-4">
          <div className="relative h-8 flex items-center">
            {/* Track de fond */}
            <div className="absolute w-full h-2 bg-[var(--color-surface-hover)] rounded-full"></div>

            {/* Track actif */}
            <div
              className="absolute h-2 bg-[rgb(var(--primary))] rounded-full"
              style={{
                left: `${minPercent}%`,
                width: `${maxPercent - minPercent}%`,
              }}
            ></div>

            {/* Thumb min */}
            <input
              type="range"
              min={min}
              max={max}
              step={step}
              value={sliderMin}
              onChange={(e) => {
                const newValue = Number(e.target.value);
                if (newValue <= sliderMax) {
                  handleSliderChange("min", newValue);
                }
              }}
              className="absolute w-full h-2 bg-transparent appearance-none cursor-pointer slider-thumb"
              style={{
                zIndex: sliderMin > sliderMax ? 2 : 1,
              }}
            />

            {/* Thumb max */}
            <input
              type="range"
              min={min}
              max={max}
              step={step}
              value={sliderMax}
              onChange={(e) => {
                const newValue = Number(e.target.value);
                if (newValue >= sliderMin) {
                  handleSliderChange("max", newValue);
                }
              }}
              className="absolute w-full h-2 bg-transparent appearance-none cursor-pointer slider-thumb"
              style={{
                zIndex: sliderMax > sliderMin ? 2 : 1,
              }}
            />
          </div>

          {/* Bornes min et max */}
          <div className="flex justify-between text-xs text-[rgb(var(--primary))] opacity-70 -mt-1">
            <span>{minBoundLabel || min}</span>
            <span>{maxBoundLabel || max}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default RangeSlider;
