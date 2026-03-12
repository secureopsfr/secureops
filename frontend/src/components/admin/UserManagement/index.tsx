"use client";

import {
  Users,
  RefreshCw,
  UserCheck,
  UserX,
  Calendar,
  Search,
} from "lucide-react";
import { useUserManagement } from "./hooks/useUserManagement";
import { useUserColumns, useHistoryColumns } from "./UserColumns";
import UserKpiStats from "./UserKpiStats";
import Card from "../../ui/cards/Card";
import { GenericButton, DropdownSelector } from "../../buttons";
import Pagination from "../Pagination";
import Table from "../../Table";
import ConfirmModal from "../../ConfirmModal";
import { AdminInlineLoading } from "../AdminSectionLoading";
import UserDetailModal from "../UserDetailModal";
import UserGroupModal from "../UserGroupModal";
import SubscriptionEditModal from "../SubscriptionEditModal";
import SubscriptionChart from "../SubscriptionChart";
import SearchToolbar from "../SearchToolbar";
import { useLanguage } from "../../LanguageProvider";

export default function UserManagement() {
  const { t } = useLanguage();
  const {
    // Data
    users,
    total,
    stats,
    subStats,
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
  } = useUserManagement();

  const columns = useUserColumns({
    openUserDetail,
    openGroupModal,
    openSuspendModal,
    openEditSubscription,
  });

  const historyColumns = useHistoryColumns();

  const isSuspended = suspendModal.data?.status === "suspended";

  return (
    <div className="space-y-6">
      {/* ═══════════ En-tête ═══════════ */}
      <Card disableHover style={{ overflow: "visible" }}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-[var(--text)]">
              {t("admin.users.title")}
            </h2>
            <p className="text-[var(--muted)] mt-1">
              {t("admin.users.description")}
            </p>
          </div>
          <GenericButton
            label={t("admin.common.refresh")}
            onClick={refreshAll}
            disabled={loading.main}
            variant="secondary"
            icon={
              <RefreshCw
                className={`w-4 h-4 ${loading.main ? "animate-spin" : ""}`}
              />
            }
            iconPosition="left"
          />
        </div>
      </Card>

      {/* ═══════════ KPI Cards ═══════════ */}
      <UserKpiStats stats={stats} subStats={subStats} loading={loading.stats} />

      {/* ═══════════ Filtres et recherche ═══════════ */}
      <SearchToolbar
        searchValue={searchInput}
        onSearchChange={setSearchInput}
        onSearchSubmit={handleSearch}
        onSearchClear={clearSearch}
        searchPlaceholder={t("admin.users.searchPlaceholder")}
        enableDebounce={true}
        debounceDelay={300}
      >
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[var(--muted)]">
              {t("admin.users.planLabel")}
            </span>
            <DropdownSelector
              selectedValue={planFilter || ""}
              onChange={(value) => {
                setPlanFilter(value || null);
                setOffset(0);
              }}
              options={[
                { value: "", label: t("admin.users.allPlans") },
                { value: "free", label: t("admin.users.free") },
                { value: "premium", label: t("admin.users.premiumPlan") },
              ]}
              width="8rem"
            />
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[var(--muted)]">
              {t("admin.users.statusLabel")}
            </span>
            <DropdownSelector
              selectedValue={statusFilter || ""}
              onChange={(value) => {
                setStatusFilter(value || null);
                setOffset(0);
              }}
              options={[
                { value: "", label: t("admin.users.allStatuses") },
                { value: "active", label: t("admin.users.active") },
                { value: "trial", label: t("admin.users.trial") },
                { value: "canceled", label: t("admin.users.canceled") },
                { value: "suspended", label: t("admin.users.suspended") },
              ]}
              width="9rem"
            />
          </div>
          <GenericButton
            label={t("admin.common.search")}
            onClick={handleSearch}
            variant="primary"
            size="sm"
            icon={<Search className="w-3.5 h-3.5" />}
            iconPosition="left"
          />
        </div>
      </SearchToolbar>

      {/* ═══════════ Erreur ═══════════ */}
      {error && (
        <Card disableHover>
          <div className="p-4 rounded-lg border border-[rgba(var(--danger),0.3)] bg-[rgba(var(--danger),0.1)]">
            <p className="text-sm text-[rgb(var(--danger))]">{error}</p>
            <button
              onClick={loadUsers}
              className="mt-2 text-sm text-[rgba(var(--danger),0.8)] hover:text-[rgba(var(--danger),0.6)] underline"
            >
              {t("admin.common.retry")}
            </button>
          </div>
        </Card>
      )}

      {/* ═══════════ Graphique évolution inscriptions ═══════════ */}
      {subStats && subStats.monthly_history.length > 0 && (
        <SubscriptionChart data={subStats.monthly_history} />
      )}

      {/* ═══════════ Sélecteur vue ═══════════ */}
      <div className="flex gap-2">
        <button
          onClick={() => setViewMode("table")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            viewMode === "table"
              ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
              : "bg-transparent text-[var(--muted)] hover:text-[var(--text)] border border-[var(--border)]"
          }`}
        >
          <Users className="w-4 h-4 inline mr-2" />
          {t("admin.users.usersTab")}
        </button>
        <button
          onClick={() => setViewMode("history")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            viewMode === "history"
              ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
              : "bg-transparent text-[var(--muted)] hover:text-[var(--text)] border border-[var(--border)]"
          }`}
        >
          <Calendar className="w-4 h-4 inline mr-2" />
          {t("admin.users.subscriptionHistory")}
        </button>
      </div>

      {/* ═══════════ Vue : Tableau des utilisateurs ═══════════ */}
      {viewMode === "table" && (
        <Card disableHover>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-[rgb(var(--primary))]" />
              <h3
                className="text-base font-semibold text-[var(--text)]"
                style={{ margin: 0 }}
              >
                {t("admin.users.registeredUsers")}
              </h3>
              <span className="text-sm text-[var(--muted)]">
                ({total} {t("admin.common.total")})
              </span>
            </div>
          </div>

          {loading.main && users.length === 0 ? (
            <AdminInlineLoading message={t("admin.users.loadingUsers")} />
          ) : users.length === 0 ? (
            <div className="py-12 text-center">
              <Users className="h-12 w-12 text-[var(--muted)] mx-auto mb-4 opacity-50" />
              <p className="text-[var(--muted)]">
                {searchTerm || planFilter || statusFilter
                  ? t("admin.users.noUsersCriteria")
                  : t("admin.users.noUsersRegistered")}
              </p>
            </div>
          ) : (
            <>
              <Table
                data={users as unknown as Record<string, unknown>[]}
                columns={columns}
                emptyMessage={t("admin.users.noUserFound")}
                cellClassName="text-xs"
              />

              <Pagination
                mode="offset"
                offset={offset}
                limit={limit}
                total={total}
                onPrevious={handlePrevious}
                onNext={handleNext}
                disabled={loading.main}
              />
            </>
          )}
        </Card>
      )}

      {/* ═══════════ Vue : Historique abonnements ═══════════ */}
      {viewMode === "history" && (
        <Card disableHover>
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-5 h-5 text-[rgb(var(--primary))]" />
            <h3
              className="text-base font-semibold text-[var(--text)]"
              style={{ margin: 0 }}
            >
              {t("admin.users.historyTitle")} ({historyTotal})
            </h3>
          </div>
          {loading.history ? (
            <AdminInlineLoading message={t("admin.users.loadingHistory")} />
          ) : (
            <Table
              data={history as unknown as Record<string, unknown>[]}
              columns={historyColumns}
              emptyMessage={t("admin.users.noHistory")}
            />
          )}
        </Card>
      )}

      {/* ═══════════ Modals ═══════════ */}
      <UserDetailModal
        isOpen={detailModal.isOpen}
        loading={loading.detail}
        user={selectedUser}
        onClose={() => {
          detailModal.close();
          setSelectedUser(null);
        }}
        onOpenGroupModal={openGroupModal}
        onOpenSuspendModal={openSuspendModal}
        onOpenEditSubscription={openEditSubscription}
      />

      <UserGroupModal
        isOpen={groupModal.isOpen}
        user={groupModal.data}
        loading={loading.group}
        onClose={groupModal.close}
        onConfirm={handleGroupChange}
      />

      <SubscriptionEditModal
        isOpen={editSubModal.isOpen}
        target={editSubModal.data}
        onClose={editSubModal.close}
        onSave={handleSaveSubscription}
      />

      <ConfirmModal
        isOpen={suspendModal.isOpen}
        onClose={suspendModal.close}
        onConfirm={handleToggleStatus}
        title={
          isSuspended
            ? t("admin.users.reactivateUser")
            : t("admin.users.suspendUser")
        }
        message={
          isSuspended
            ? t("admin.users.reactivateMessage", {
                email: suspendModal.data?.email ?? "",
              })
            : t("admin.users.suspendMessage", {
                email: suspendModal.data?.email ?? "",
              })
        }
        confirmText={
          isSuspended ? t("admin.users.reactivate") : t("admin.users.suspend")
        }
        variant={isSuspended ? "default" : "danger"}
        confirmationText={isSuspended ? undefined : suspendModal.data?.email}
        icon={isSuspended ? UserCheck : UserX}
      />
    </div>
  );
}
