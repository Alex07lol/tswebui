import React, { useEffect, useState } from 'react';
import { ChevronLeft, Download, Calendar, Layers, ShieldCheck, FileText, Loader2 } from 'lucide-react';
import { PublicSiteConfig, DocumentDetail, fetchPublicDocument } from '../lib/publicApi';
import { PDFViewer } from '../components/PDFViewer';

interface DocumentDetailPageProps {
  site: PublicSiteConfig;
  documentId: string;
  onBack: () => void;
}

export const DocumentDetailPage: React.FC<DocumentDetailPageProps> = ({
  site,
  documentId,
  onBack,
}) => {
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    fetchPublicDocument(site.slug, documentId)
      .then((data) => {
        if (isMounted) setDoc(data);
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load document.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [site.slug, documentId]);

  if (loading) {
    return (
      <div className="py-24 text-center flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="text-sm text-zinc-400">Loading document details...</p>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="py-12 space-y-4">
        <button
          onClick={onBack}
          className="flex items-center space-x-1 text-xs text-zinc-400 hover:text-white"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to search</span>
        </button>
        <div className="p-6 bg-red-950/40 border border-red-800/60 rounded-xl text-red-300 text-sm">
          {error || 'Document could not be retrieved.'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 py-6">
      {/* Top Bar / Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-xs font-medium text-zinc-300 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to results</span>
        </button>

        <a
          href={doc.file_url}
          download={doc.filename}
          className="flex items-center space-x-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download Document</span>
        </a>
      </div>

      {/* Document Header Card */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-3">
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {doc.title}
              </h1>
              {doc.drawing_number && (
                <span className="px-2.5 py-1 rounded bg-blue-900/40 border border-blue-600/40 text-blue-300 font-mono text-xs font-bold">
                  {doc.drawing_number}
                </span>
              )}
            </div>
            <p className="text-xs text-zinc-400 font-mono">
              Filename: {doc.filename} • {doc.page_count} page{doc.page_count === 1 ? '' : 's'}
            </p>
          </div>

          <div className="flex items-center space-x-4 text-xs text-zinc-400">
            <div className="flex items-center space-x-1 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              <span>Public Record</span>
            </div>
            {doc.published_at && (
              <div className="flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-zinc-500" />
                <span>{new Date(doc.published_at).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </div>

        {/* Extracted Metadata Grid */}
        {Object.keys(doc.structured_fields).length > 0 && (
          <div className="mt-6 pt-5 border-t border-zinc-800">
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Extracted Specifications & Metadata
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {Object.entries(doc.structured_fields).map(([key, value]) => (
                <div key={key} className="p-3 bg-zinc-950/70 border border-zinc-800 rounded-lg">
                  <div className="text-[11px] text-zinc-500 font-medium uppercase tracking-wider">
                    {key.replace(/_/g, ' ')}
                  </div>
                  <div className="text-xs font-semibold text-zinc-100 mt-0.5 truncate font-mono">
                    {String(value) || '—'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* PDF / Document Viewer */}
      <div className="space-y-2">
        <h2 className="text-sm font-semibold text-zinc-300 flex items-center space-x-2">
          <FileText className="w-4 h-4 text-blue-400" />
          <span>Document Viewer</span>
        </h2>
        <PDFViewer
          fileUrl={doc.file_url}
          filename={doc.filename}
          mimeType={doc.mime_type}
          pageCount={doc.page_count}
        />
      </div>
    </div>
  );
};
