"use client";

import { useState, useCallback } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import { useModal } from "../../../../hooks/useModal";
import adminService from "../../../../services/admin";
import type {
  UserRecord,
  SubscriptionRecord,
} from "../../../../services/admin";
import type { SubscriptionEditTarget } from "../../SubscriptionEditModal";
import { error as logError } from "../../../../utils/logger";
import {
  showSuccessToast,
  showErrorToast,
} from "../../../../utils/toastNotifications";
import {
  adminUsersKey,
  ADMIN_USER_STATS_KEY,
  ADMIN_SUB_STATS_KEY,
  adminSubHistoryKey,
} from "../../../../hooks/swr/keys";
import { useLanguage } from "../../../LanguageProvider";

export function useUserManagement() {
  const { t } = useLanguage();
  /* ── état UI (non-data) ── */
  const [selectedUser, setSelectedUser] = useState<UserRecord | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [groupLoading, setGroupLoading] = useState(false);
  const [error] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [planFilter, setPlanFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  /* ── vue active (table utilisateurs / historique abonnements) ── */
  const [viewMode, setViewMode] = useState<"table" | "history">("table");

  /* ── modals avec hook personnalisé ── */
  const detailModal = useModal<UserRecord>();
  const groupModal = useModal<UserRecord>();
  const suspendModal = useModal<UserRecord>();
  const editSubModal = useModal<SubscriptionEditTarget>();

  /* ── SWR : liste des utilisateurs ── */
  const usersSwrKey = adminUsersKey({
    search: searchTerm || null,
    plan: planFilter,
    status: statusFilter,
    limit,
    offset,
  });

  const {
    data: usersData,
    isLoading: usersLoading,
    mutate: mutateUsers,
  } = useSWR(usersSwrKey, () =>
    adminService.getUsers({
      search: searchTerm || null,
      plan: planFilter,
      status: statusFilter,
      limit,
      offset,
    }),
  );

  const users = usersData?.users || [];
  const total = usersData?.total || 0;

  /* ── SWR : stats utilisateurs ── */
  const { data: stats, mutate: mutateUserStats } = useSWR(
    ADMIN_USER_STATS_KEY,
    () => adminService.getUsersStats(),
    { dedupingInterval: 60_000 },
  );

  /* ── SWR : stats abonnements ── */
  const { data: subStats, mutate: mutateSubStats } = useSWR(
    ADMIN_SUB_STATS_KEY,
    () => adminService.getSubscriptionStats(),
    { dedupingInterval: 60_000 },
  );

  /* ── SWR : historique abonnements (lazy – uniquement quand viewMode === "history") ── */
  const historySwrKey = viewMode === "history" ? adminSubHistoryKey(50) : null;
  const { data: historyData } = useSWR(historySwrKey, () =>
    adminService.getSubscriptionHistory({ limit: 50 }),
  );
  const history = (historyData?.history as SubscriptionRecord[]) || [];
  const historyTotal = historyData?.total || 0;

  /* ── loading unifié ── */
  const loading = {
    main: usersLoading,
    stats: !stats && !subStats,
    detail: detailLoading,
    group: groupLoading,
    history: viewMode === "history" && !historyData,
  };

  /* ── recherche ── */
  const handleSearch = () => {
    setSearchTerm(searchInput.trim());
    setOffset(0);
  };
  const clearSearch = () => {
    setSearchInput("");
    setSearchTerm("");
    setOffset(0);
  };

  /* ── pagination ── */
  const handlePrevious = () => setOffset(Math.max(0, offset - limit));
  const handleNext = () => setOffset(offset + limit);

  /* ── détail utilisateur ── */
  const openUserDetail = useCallback(
    async (user: UserRecord) => {
      detailModal.open(user);
      setDetailLoading(true);
      try {
        const detail = await adminService.getUserDetail(user.id);
        setSelectedUser(detail);
      } catch {
        setSelectedUser(user);
      } finally {
        setDetailLoading(false);
      }
    },
    [detailModal],
  );

  /* ── helpers pour revalider après mutation ── */
  const revalidateAll = useCallback(() => {
    mutateUsers();
    mutateUserStats();
    mutateSubStats();
  }, [mutateUsers, mutateUserStats, mutateSubStats]);

  /* ── changement de groupe ── */
  const openGroupModal = useCallback(
    (user: UserRecord) => {
      groupModal.open(user);
    },
    [groupModal],
  );

  const handleGroupChange = async (group: string) => {
    if (!groupModal.data) return;
    setGroupLoading(true);
    try {
      await adminService.updateUserGroup(groupModal.data.id, group);
      showSuccessToast(
        `Groupe de ${groupModal.data.email} mis à jour en "${group}"`,
      );
      groupModal.close();
      revalidateAll();
    } catch (err) {
      logError("Error updating user group:", err);
      showErrorToast(t("admin.toast.groupChange"));
    } finally {
      setGroupLoading(false);
    }
  };

  /* ── suspension / réactivation ── */
  const openSuspendModal = useCallback(
    (user: UserRecord) => {
      suspendModal.open(user);
    },
    [suspendModal],
  );

  const handleToggleStatus = async () => {
    if (!suspendModal.data) return;
    const action =
      suspendModal.data.status === "suspended" ? "enable" : "disable";
    try {
      await adminService.toggleUserStatus(suspendModal.data.id, action);
      showSuccessToast(
        action === "disable"
          ? `${suspendModal.data.email} a été suspendu`
          : `${suspendModal.data.email} a été réactivé`,
      );
      suspendModal.close();
      revalidateAll();
    } catch (err) {
      logError("Error toggling user status:", err);
      showErrorToast(t("admin.toast.statusChange"));
    }
  };

  /* ── modifier l'abonnement ── */
  const openEditSubscription = useCallback(
    (user: UserRecord) => {
      if (!user.subscription_id) {
        showErrorToast(t("admin.toast.noSubscription"));
        return;
      }
      editSubModal.open({
        email: user.email,
        subscription_id: user.subscription_id,
        plan: user.plan,
        status: user.status,
        stripe_customer_id: user.stripe_customer_id,
        current_period_end: user.current_period_end,
      });
    },
    [editSubModal, t],
  );

  const handleSaveSubscription = async (
    subscriptionId: string,
    updates: { plan?: string; status?: string },
  ) => {
    await adminService.updateSubscription(subscriptionId, updates);
    showSuccessToast(t("admin.toast.subscriptionUpdated"));
    revalidateAll();
    // Invalider aussi le cache de l'historique
    globalMutate(adminSubHistoryKey(50));
  };

  const refreshAll = () => {
    revalidateAll();
  };

  // Expose loadUsers for backward compat (just revalidate)
  const loadUsers = () => mutateUsers();

  return {
    // Data
    users,
    total,
    stats: stats ?? null,
    subStats: subStats ?? null,
    selectedUser,
    setSelectedUser,
    history,
    historyTotal,
    // UI state
    loading,
    error,
    searchInput,
    setSearchInput,
    searchTerm,
    planFilter,
    setPlanFilter,
    statusFilter,
    setStatusFilter,
    limit,
    offset,
    setOffset,
    viewMode,
    setViewMode,
    // Actions
    loadUsers,
    handleSearch,
    clearSearch,
    handlePrevious,
    handleNext,
    refreshAll,
    // User detail
    openUserDetail,
    // Group
    openGroupModal,
    handleGroupChange,
    // Suspend
    openSuspendModal,
    handleToggleStatus,
    // Subscription
    openEditSubscription,
    handleSaveSubscription,
    // Modals
    detailModal,
    groupModal,
    suspendModal,
    editSubModal,
  };
}
