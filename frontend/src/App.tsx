import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { ApplicationsList } from './components/ApplicationsList';
import { ApplicationWorkspace } from './components/ApplicationWorkspace';
import { NewApplicationModal } from './components/NewApplicationModal';
import { CreateApplicationPayload, LoanApplication } from './types';
import { createApplication, deleteApplication, fetchApplication, fetchApplications } from './services/api';

export const App: React.FC = () => {
  const [applications, setApplications] = useState<LoanApplication[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [selectedApp, setSelectedApp] = useState<LoanApplication | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadApplications = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const apps = await fetchApplications();
      setApplications(apps);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to connect to LoanFlow AI backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const handleSelectApplication = async (app: LoanApplication) => {
    setSelectedAppId(app.id);
    setSelectedApp(app);
    // Refresh to get latest documents
    try {
      const detailed = await fetchApplication(app.id);
      setSelectedApp(detailed);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRefreshCurrentApplication = async () => {
    if (!selectedAppId) return;
    try {
      const updated = await fetchApplication(selectedAppId);
      setSelectedApp(updated);
      // Also update in list
      setApplications((prev) =>
        prev.map((a) => (a.id === selectedAppId ? updated : a))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateApplication = async (payload: CreateApplicationPayload) => {
    const created = await createApplication(payload);
    await loadApplications();
    // Navigate straight to the new application workspace
    setSelectedAppId(created.id);
    setSelectedApp(created);
  };

  const handleDeleteApplication = async (id: string) => {
    try {
      await deleteApplication(id);
      if (selectedAppId === id) {
        setSelectedAppId(null);
        setSelectedApp(null);
      }
      await loadApplications();
    } catch (err: any) {
      alert(err.message || 'Failed to delete application.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        onHomeClick={() => {
          setSelectedAppId(null);
          setSelectedApp(null);
          loadApplications();
        }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {errorMessage && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-sm flex items-center justify-between">
            <span>{errorMessage}</span>
            <button
              onClick={loadApplications}
              className="text-xs font-bold underline hover:text-rose-950 ml-4"
            >
              Retry
            </button>
          </div>
        )}

        {selectedApp ? (
          <ApplicationWorkspace
            application={selectedApp}
            onBack={() => {
              setSelectedAppId(null);
              setSelectedApp(null);
              loadApplications();
            }}
            onRefreshApplication={handleRefreshCurrentApplication}
          />
        ) : (
          <ApplicationsList
            applications={applications}
            isLoading={isLoading}
            onSelectApplication={handleSelectApplication}
            onNewApplication={() => setIsNewModalOpen(true)}
            onDeleteApplication={handleDeleteApplication}
          />
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-400">
        <p>LoanFlow AI &bull; Intelligent Mortgage Underwriting Agent Platform &bull; Built with LangGraph &amp; FastAPI</p>
      </footer>

      <NewApplicationModal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        onSubmit={handleCreateApplication}
      />
    </div>
  );
};

export default App;
