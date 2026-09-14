import React, { useState } from 'react';
import { HardHat, Lock, User as UserIcon, Eye, EyeOff, AlertCircle, Loader2, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !password.trim()) {
      setErrorMessage('Please enter both your username/email and password.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await login(identifier.trim(), password);
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = (user: string, pass: string) => {
    setIdentifier(user);
    setPassword(pass);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-10 sm:px-6 lg:px-8 px-4 font-sans selection:bg-blue-600 selection:text-white">
      {/* Background ambient lighting */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-blue-600/10 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-amber-500/10 blur-3xl"></div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600 text-white shadow-xl shadow-blue-500/20 mb-4 border border-blue-400/30">
            <HardHat className="w-8 h-8" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            BSR Rate Hub
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-amber-400 font-semibold tracking-wide uppercase">
            Sri Lanka BOQ & Multi-Sector Engineering System
          </p>
          <p className="mt-2 text-xs text-slate-400">
            Building (BSR) • Highway (HSR) • Water Supply • Sewerage
          </p>
        </div>

        {/* Login Card */}
        <div className="mt-6 bg-slate-900 border border-slate-800 py-8 px-5 sm:px-10 shadow-2xl rounded-2xl">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {errorMessage && (
              <div className="p-3.5 bg-rose-500/15 border border-rose-500/30 rounded-xl flex items-start gap-3 text-xs text-rose-300">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="leading-snug">{errorMessage}</span>
              </div>
            )}

            {/* Username / Email */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Username or Email
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <UserIcon className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  autoComplete="username"
                  required
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="admin@bsrhub.lk or admin"
                  className="block w-full pl-10 pr-3.5 py-2.5 sm:py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-10 py-2.5 sm:py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <span>Sign In to System</span>
                )}
              </button>
            </div>
          </form>

          {/* Quick Demo Login Pills */}
          <div className="mt-7 pt-5 border-t border-slate-800/80">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 text-center">
              Quick Test Accounts (1-Click Fill)
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@bsrhub.lk', 'Admin@123456')}
                className="p-2 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 rounded-lg text-left transition-colors"
              >
                <div className="font-bold text-blue-400 flex items-center gap-1">
                  <span>Admin</span>
                  <ShieldCheck className="w-3 h-3 text-blue-400 ml-auto" />
                </div>
                <div className="text-[10px] text-slate-400 truncate">Full System Access</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('manager@bsrhub.lk', 'Manager@123456')}
                className="p-2 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 rounded-lg text-left transition-colors"
              >
                <div className="font-bold text-emerald-400 flex items-center gap-1">
                  <span>Manager</span>
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 ml-auto" />
                </div>
                <div className="text-[10px] text-slate-400 truncate">Upload & Review</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('qs@bsrhub.lk', 'User@123456')}
                className="p-2 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 rounded-lg text-left transition-colors"
              >
                <div className="font-bold text-amber-400 flex items-center gap-1">
                  <span>QS Engineer</span>
                </div>
                <div className="text-[10px] text-slate-400 truncate">Rates & BOQ Work</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('viewer@bsrhub.lk', 'Viewer@123456')}
                className="p-2 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 rounded-lg text-left transition-colors"
              >
                <div className="font-bold text-slate-300 flex items-center gap-1">
                  <span>Viewer</span>
                </div>
                <div className="text-[10px] text-slate-400 truncate">Read-Only Search</div>
              </button>
            </div>
          </div>
        </div>

        {/* Security & Multi-device note */}
        <p className="mt-4 text-center text-xs text-slate-500">
          Encrypted Session • Cloud Centralized • Multi-Device Protected
        </p>
      </div>
    </div>
  );
};
