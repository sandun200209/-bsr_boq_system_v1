import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  ShieldCheck,
  Activity,
  Search,
  CheckCircle,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { User, AuditLog } from '../types';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const UserManagementPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [activeSubTab, setActiveSubTab] = useState<'users' | 'audit'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // New User Form State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<'ADMIN' | 'MANAGER' | 'USER' | 'VIEWER'>('USER');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Audit filter state
  const [auditSearch, setAuditSearch] = useState('');
  const [auditActionFilter, setAuditActionFilter] = useState('');

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [uList, aLogs] = await Promise.all([
        api.getUsers(0, 100).catch(() => []),
        api.getAuditLogs({ limit: 150 }).catch(() => []),
      ]);
      setUsers(uList);
      setAuditLogs(aLogs);
    } catch (err: any) {
      setError(err.message || 'Failed to load user management data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await api.createUser({
        email: newEmail.trim(),
        username: newUsername.trim(),
        full_name: newFullName.trim(),
        password: newPassword,
        role: newRole,
      });
      setSuccessMessage(`User '${newEmail}' created successfully with role ${newRole}.`);
      setShowCreateModal(false);
      setNewEmail('');
      setNewUsername('');
      setNewFullName('');
      setNewPassword('');
      setNewRole('USER');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (user: User) => {
    if (user.id === currentUser?.id) {
      alert('You cannot deactivate your own administrative account.');
      return;
    }
    const newStatus = !user.is_active;
    const confirmMsg = `Are you sure you want to ${newStatus ? 'activate' : 'deactivate'} ${user.email}?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      await api.updateUser(user.id, { is_active: newStatus });
      setSuccessMessage(`User ${user.email} is now ${newStatus ? 'active' : 'deactivated'}.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to update user status');
    }
  };

  const handleRoleChange = async (user: User, newRole: string) => {
    if (user.id === currentUser?.id && newRole !== 'ADMIN') {
      alert('You cannot remove the ADMIN role from your own account.');
      return;
    }
    try {
      await api.updateUser(user.id, { role: newRole });
      setSuccessMessage(`Updated ${user.email} role to ${newRole}.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to update user role');
    }
  };

  const filteredLogs = auditLogs.filter((log) => {
    if (auditActionFilter && log.action !== auditActionFilter) return false;
    if (auditSearch.trim()) {
      const term = auditSearch.toLowerCase();
      const matchEmail = (log.user_email || '').toLowerCase().includes(term);
      const matchDesc = (log.description || '').toLowerCase().includes(term);
      const matchAction = log.action.toLowerCase().includes(term);
      return matchEmail || matchDesc || matchAction;
    }
    return true;
  });

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-rose-500/10 text-rose-600 border-rose-200';
      case 'MANAGER':
        return 'bg-emerald-500/10 text-emerald-600 border-emerald-200';
      case 'USER':
        return 'bg-blue-500/10 text-blue-600 border-blue-200';
      case 'VIEWER':
      default:
        return 'bg-slate-500/10 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Users className="w-6 h-6 text-blue-600" />
            <span>Team Access & Audit Trail</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Centralized role-based access control (RBAC) and security audit log.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={isLoading}
            className="p-2 border border-slate-200 bg-white hover:bg-slate-50 rounded-xl text-slate-600 shadow-xs transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-xs transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add New User</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-xs sm:text-sm text-rose-700">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-rose-500 hover:text-rose-700">
            ×
          </button>
        </div>
      )}
      {successMessage && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-xs sm:text-sm text-emerald-700">
          <CheckCircle className="w-4 h-4 shrink-0 text-emerald-500" />
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="ml-auto text-emerald-500 hover:text-emerald-700">
            ×
          </button>
        </div>
      )}

      {/* Tab Switcher */}
      <div className="flex border-b border-slate-200 gap-6 text-sm font-semibold">
        <button
          onClick={() => setActiveSubTab('users')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeSubTab === 'users'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>User Accounts ({users.length})</span>
        </button>
        <button
          onClick={() => setActiveSubTab('audit')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeSubTab === 'audit'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Security Audit Trail ({auditLogs.length})</span>
        </button>
      </div>

      {/* Tab 1: User Accounts */}
      {activeSubTab === 'users' && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs sm:text-sm">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px] tracking-wider">
                  <th className="py-3 px-4">User Details</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Created Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900">{u.full_name}</div>
                      <div className="text-xs text-slate-500 font-mono">{u.email}</div>
                      <div className="text-[11px] text-slate-400">@{u.username}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u, e.target.value)}
                        disabled={u.id === currentUser?.id}
                        className={`text-xs font-bold px-2.5 py-1 rounded-lg border focus:outline-none focus:ring-1 focus:ring-blue-500 ${getRoleBadge(
                          u.role
                        )}`}
                      >
                        <option value="ADMIN">ADMIN (Full Access)</option>
                        <option value="MANAGER">MANAGER (Upload & Review)</option>
                        <option value="USER">USER (Standard Access)</option>
                        <option value="VIEWER">VIEWER (Read-Only)</option>
                      </select>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ${
                          u.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 text-xs">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {u.id !== currentUser?.id && (
                        <button
                          onClick={() => handleToggleStatus(u)}
                          className={`text-xs px-2.5 py-1 rounded-lg font-semibold border transition-colors ${
                            u.is_active
                              ? 'text-rose-600 border-rose-200 hover:bg-rose-50'
                              : 'text-emerald-600 border-emerald-200 hover:bg-emerald-50'
                          }`}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Audit Logs */}
      {activeSubTab === 'audit' && (
        <div className="space-y-4">
          {/* Audit Search Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="text"
                value={auditSearch}
                onChange={(e) => setAuditSearch(e.target.value)}
                placeholder="Search audit trail by user, action, or description..."
                className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={auditActionFilter}
              onChange={(e) => setAuditActionFilter(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-xl text-xs sm:text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Actions</option>
              <option value="LOGIN">LOGIN</option>
              <option value="UPLOAD_DOCUMENT">UPLOAD_DOCUMENT</option>
              <option value="APPROVE_RATE_ITEM">APPROVE_RATE_ITEM</option>
              <option value="UPDATE_RATE_ITEM">UPDATE_RATE_ITEM</option>
              <option value="DELETE_DOCUMENT">DELETE_DOCUMENT</option>
              <option value="USER_CREATED">USER_CREATED</option>
            </select>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px] tracking-wider">
                    <th className="py-3 px-4">Timestamp (UTC)</th>
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {filteredLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center py-8 text-slate-400 font-sans">
                        No audit records found matching your filter.
                      </td>
                    </tr>
                  ) : (
                    filteredLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-2.5 px-4 text-slate-500 whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="py-2.5 px-4 font-semibold text-slate-800">
                          {log.user_email || 'anonymous'}
                        </td>
                        <td className="py-2.5 px-4">
                          <span className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-700 font-bold text-[10px]">
                            {log.action}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 text-slate-600">
                          {log.entity_type} {log.entity_id ? `(#${log.entity_id})` : ''}
                        </td>
                        <td className="py-2.5 px-4 font-sans text-slate-700 max-w-xs sm:max-w-md truncate">
                          {log.description}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
            <h2 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-blue-600" />
              <span>Create New User Account</span>
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Add a new member and assign appropriate system permissions.
            </p>

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="e.g. Kasun Perera"
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs sm:text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="kasun@company.lk"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs sm:text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Username</label>
                  <input
                    type="text"
                    required
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="kasun_p"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs sm:text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs sm:text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">System Role</label>
                <select
                  value={newRole}
                  onChange={(e: any) => setNewRole(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs sm:text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="USER">USER (Standard QS - Search, Compare & Upload)</option>
                  <option value="MANAGER">MANAGER (Upload, Edit, Review Queue)</option>
                  <option value="VIEWER">VIEWER (Read-Only - Search & Compare)</option>
                  <option value="ADMIN">ADMIN (Full Administrative Control)</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-600 hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-xs disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
