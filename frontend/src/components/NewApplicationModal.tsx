import React, { useState } from 'react';
import { X, UserPlus, DollarSign, Mail, Phone, MapPin } from 'lucide-react';
import { CreateApplicationPayload } from '../types';

interface NewApplicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: CreateApplicationPayload) => Promise<void>;
}

export const NewApplicationModal: React.FC<NewApplicationModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [borrowerName, setBorrowerName] = useState('');
  const [borrowerEmail, setBorrowerEmail] = useState('');
  const [borrowerPhone, setBorrowerPhone] = useState('');
  const [loanAmount, setLoanAmount] = useState('');
  const [propertyAddress, setPropertyAddress] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const amount = parseFloat(loanAmount.replace(/[^0-9.]/g, ''));
    if (!borrowerName.trim()) {
      setError('Borrower name is required.');
      return;
    }
    if (!borrowerEmail.trim()) {
      setError('Borrower email is required.');
      return;
    }
    if (isNaN(amount) || amount <= 0) {
      setError('Please provide a valid loan amount greater than zero.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit({
        borrower_name: borrowerName.trim(),
        borrower_email: borrowerEmail.trim(),
        borrower_phone: borrowerPhone.trim() || undefined,
        loan_amount: amount,
        property_address: propertyAddress.trim() || undefined,
      });
      onClose();
      // Reset
      setBorrowerName('');
      setBorrowerEmail('');
      setBorrowerPhone('');
      setLoanAmount('');
      setPropertyAddress('');
    } catch (err: any) {
      setError(err.message || 'Failed to create application.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-100 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-blue-100 text-blue-700 rounded-xl">
              <UserPlus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-lg">New Loan Application</h3>
              <p className="text-xs text-slate-500">Initiate a mortgage application for underwriting</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Borrower Full Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Sarah Jenkins"
              value={borrowerName}
              onChange={(e) => setBorrowerName(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center">
                <Mail className="w-3.5 h-3.5 mr-1 text-slate-400" /> Email *
              </label>
              <input
                type="email"
                required
                placeholder="borrower@example.com"
                value={borrowerEmail}
                onChange={(e) => setBorrowerEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center">
                <Phone className="w-3.5 h-3.5 mr-1 text-slate-400" /> Phone
              </label>
              <input
                type="tel"
                placeholder="(555) 000-0000"
                value={borrowerPhone}
                onChange={(e) => setBorrowerPhone(e.target.value)}
                className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center">
              <DollarSign className="w-3.5 h-3.5 mr-1 text-slate-400" /> Requested Loan Amount ($) *
            </label>
            <input
              type="number"
              step="1000"
              required
              placeholder="350000"
              value={loanAmount}
              onChange={(e) => setLoanAmount(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center">
              <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" /> Subject Property Address
            </label>
            <input
              type="text"
              placeholder="742 Evergreen Terrace, Springfield, OR"
              value={propertyAddress}
              onChange={(e) => setPropertyAddress(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
          </div>

          {/* Footer buttons */}
          <div className="pt-4 flex items-center justify-end space-x-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-sm shadow-blue-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isSubmitting ? 'Creating...' : 'Create Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
