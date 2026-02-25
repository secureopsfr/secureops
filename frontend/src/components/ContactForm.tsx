"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import TurnstileWidget, { TurnstileRef } from "./TurnstileWidget";
import { DropdownSelector, GenericButton } from "./buttons";
import Checkbox from "./inputs/Checkbox";
import AnimateInView from "./AnimateInView";
import {
  sendContactMessage,
  ContactMessageRequest,
} from "../services/contactService";
import { showSuccessToast, showErrorToast } from "../utils/toastNotifications";
import { useLanguage } from "./LanguageProvider";

/**
 * Client component — contact form with captcha, validation, and submission logic.
 */
export default function ContactForm() {
  const { t, lp } = useLanguage();

  const CONTACT_SUBJECTS = [
    { value: "", label: t("contact.subjects.default") },
    { value: "question", label: t("contact.subjects.question") },
    { value: "collaboration", label: t("contact.subjects.collaboration") },
    { value: "rgpd", label: t("contact.subjects.gdpr") },
    { value: "autre", label: t("contact.subjects.other") },
  ];

  const [formData, setFormData] = useState<ContactMessageRequest>({
    first_name: "",
    last_name: "",
    email: "",
    subject: "",
    message: "",
    turnstile_token: "",
  });
  const [loading, setLoading] = useState(false);
  const [verifyingCaptcha, setVerifyingCaptcha] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const turnstileRef = useRef<TurnstileRef>(null);
  const formDataRef = useRef(formData);

  useEffect(() => {
    formDataRef.current = formData;
  }, [formData]);

  useEffect(() => {
    if (textareaRef.current) {
      const textarea = textareaRef.current;
      textarea.style.height = "auto";
      const maxHeight = 200;
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = `${newHeight}px`;
    }
  }, [formData.message]);

  const handleInvalid = (
    e: React.InvalidEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) => {
    e.preventDefault();

    const target = e.target as
      | HTMLInputElement
      | HTMLTextAreaElement
      | HTMLSelectElement;

    if (target.name === "email" && target.validity.typeMismatch) {
      const message = t("contact.emailInvalid");
      target.setCustomValidity(message);
      setEmailError(message);
    } else {
      target.setCustomValidity("");
    }

    const form = target.form;
    if (form) {
      const fieldOrder = [
        "first_name",
        "last_name",
        "email",
        "subject",
        "message",
        "privacy",
      ];

      for (const fieldName of fieldOrder) {
        const field = form[fieldName] as
          | HTMLInputElement
          | HTMLTextAreaElement
          | HTMLSelectElement;
        if (field && !field.validity.valid) {
          field.focus();
          return;
        }
      }
    }

    target.focus();
  };

  const handleInvalidInput = (e: React.InvalidEvent<HTMLInputElement>) => {
    handleInvalid(
      e as React.InvalidEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    );
  };

  const handleInvalidTextarea = (
    e: React.InvalidEvent<HTMLTextAreaElement>,
  ) => {
    handleInvalid(
      e as React.InvalidEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    );
  };

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    if (name === "email") {
      setEmailError(null);
      e.target.setCustomValidity("");
    }
  };

  const handleCaptchaSuccess = useCallback(
    async (token: string) => {
      if (!token) {
        setVerifyingCaptcha(false);
        return;
      }

      setVerifyingCaptcha(false);

      const currentFormData = formDataRef.current;
      const dataToSend = {
        ...currentFormData,
        turnstile_token: token,
      };

      setLoading(true);
      try {
        const response = await sendContactMessage(dataToSend);
        showSuccessToast(response.message || t("contact.successMessage"));
        setFormData({
          first_name: "",
          last_name: "",
          email: "",
          subject: "",
          message: "",
          turnstile_token: "",
        });
        setPrivacyAccepted(false);
      } catch (err: unknown) {
        showErrorToast(
          err instanceof Error ? err.message : t("contact.sendError"),
        );
      } finally {
        setLoading(false);
      }
    },
    [t],
  );

  const isFormComplete =
    formData.first_name.trim() !== "" &&
    formData.last_name.trim() !== "" &&
    formData.email.trim() !== "" &&
    formData.subject !== "" &&
    formData.message.trim() !== "" &&
    privacyAccepted;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (turnstileRef.current) {
      setVerifyingCaptcha(true);
      try {
        turnstileRef.current.execute();
      } catch {
        setVerifyingCaptcha(false);
        showErrorToast(t("contact.captchaError"));
      }
    } else {
      showErrorToast(t("contact.captchaUnavailable"));
    }
  };

  return (
    <AnimateInView
      initialOnly
      delay={80}
      className="page-section landing-reveal-page"
      as="section"
      aria-label="Contact page"
    >
      <div className="page-container space-y-6">
        {/* Header */}
        <div className="page-header">
          <h1 className="page-title">{t("contact.title")}</h1>
          <p className="page-subtitle mt-4">{t("contact.subtitle")}</p>
        </div>

        <div className="form-container">
          <div className="card no-hover">
            <h2 className="section-title !text-left -mt-2">
              {t("contact.formTitle")}
            </h2>

            <form
              onSubmit={handleSubmit}
              aria-label="Contact form"
              className="space-y-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="firstName" className="label-form">
                    {t("contact.firstNameLabel")}
                  </label>
                  <input
                    type="text"
                    id="firstName"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    onInvalid={handleInvalidInput}
                    tabIndex={1}
                    maxLength={100}
                    required
                    className="auth-input"
                    placeholder={t("contact.firstNamePlaceholder")}
                  />
                </div>
                <div>
                  <label htmlFor="lastName" className="label-form">
                    {t("contact.lastNameLabel")}
                  </label>
                  <input
                    type="text"
                    id="lastName"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    onInvalid={handleInvalidInput}
                    tabIndex={2}
                    maxLength={100}
                    required
                    className="auth-input"
                    placeholder={t("contact.lastNamePlaceholder")}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="label-form">
                  {t("contact.emailLabel")}
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  onInvalid={handleInvalidInput}
                  onBlur={(e) => {
                    const emailInput = e.target as HTMLInputElement;
                    if (emailInput.value && !emailInput.validity.valid) {
                      if (emailInput.validity.typeMismatch) {
                        const message = t("contact.emailInvalid");
                        emailInput.setCustomValidity(message);
                        setEmailError(message);
                      }
                    } else {
                      emailInput.setCustomValidity("");
                      setEmailError(null);
                    }
                  }}
                  tabIndex={3}
                  maxLength={255}
                  required
                  className="auth-input"
                  placeholder={t("contact.emailPlaceholder")}
                />
                {emailError && (
                  <p
                    className="mt-1 text-sm text-[rgb(var(--danger))]"
                    role="alert"
                  >
                    {emailError}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="subject" className="label-form">
                  {t("contact.subjectLabel")}
                </label>
                <DropdownSelector
                  selectedValue={formData.subject || ""}
                  onChange={(value) => {
                    setFormData((prev) => ({
                      ...prev,
                      subject: value,
                    }));
                  }}
                  options={CONTACT_SUBJECTS}
                  width="100%"
                />
                <input
                  type="text"
                  id="subject"
                  name="subject"
                  value={formData.subject}
                  required
                  aria-required="true"
                  onInvalid={handleInvalidInput}
                  tabIndex={-1}
                  readOnly
                  onChange={() => {}}
                  className="sr-hidden"
                />
              </div>

              <div>
                <label htmlFor="message" className="label-form">
                  {t("contact.messageLabel")}
                </label>
                <textarea
                  ref={textareaRef}
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleInputChange}
                  onInvalid={handleInvalidTextarea}
                  tabIndex={5}
                  rows={3}
                  maxLength={5000}
                  required
                  aria-required="true"
                  className="auth-input min-h-[60px] overflow-hidden resize-none"
                  placeholder={t("contact.messagePlaceholder")}
                />
                <div className="char-counter">
                  {formData.message.length.toLocaleString()}/5 000
                </div>
              </div>

              {/* Invisible Turnstile widget */}
              <TurnstileWidget
                key="contact-turnstile"
                ref={turnstileRef}
                onSuccess={handleCaptchaSuccess}
              />

              <div className="flex items-start">
                <Checkbox
                  label={
                    <>
                      {t("contact.privacyConsent")}{" "}
                      <Link
                        href={lp("/politique-confidentialite")}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent hover:underline"
                      >
                        {t("contact.privacyLink")}
                      </Link>
                      . *
                    </>
                  }
                  checked={privacyAccepted}
                  onChange={setPrivacyAccepted}
                  dataTestId="privacy-checkbox"
                />
              </div>

              <div className="flex justify-center w-full">
                <GenericButton
                  type="submit"
                  label={
                    verifyingCaptcha
                      ? t("contact.verifyingCaptcha")
                      : t("contact.submitBtn")
                  }
                  variant="primary"
                  disabled={!isFormComplete || loading || verifyingCaptcha}
                  loading={loading}
                  loadingLabel={t("contact.sendingBtn")}
                  style={{
                    opacity: !isFormComplete ? 0.5 : 1,
                    cursor: !isFormComplete ? "not-allowed" : undefined,
                    transition: "opacity 0.2s ease",
                  }}
                />
              </div>
            </form>
          </div>
        </div>
      </div>
    </AnimateInView>
  );
}
