import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { formatBytes } from '../lib/utils';

interface DropZoneProps {
  onFileSelected: (file: File) => void | Promise<void>;
  isUploading?: boolean;
  accept?: string;
  maxSizeMB?: number;
}

export const DropZone: React.FC<DropZoneProps> = ({
  onFileSelected,
  isUploading = false,
  accept = '.pdf,.png,.jpg,.jpeg,.tiff,.bmp',
  maxSizeMB = 50,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const validateAndProcessFile = async (file: File) => {
    setErrorMessage(null);

    // Validate size
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setErrorMessage(`File size exceeds limit (${maxSizeMB} MB)`);
      return;
    }

    setSelectedFile(file);
    try {
      await onFileSelected(file);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to upload document');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileInputChange}
        className="hidden"
      />

      <motion.div
        layout
        onClick={() => !isUploading && fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        animate={{
          scale: isDragOver ? 1.015 : 1,
          borderColor: isDragOver ? '#ffffff' : '#27272a',
          backgroundColor: isDragOver ? '#121215' : '#0c0c0e',
        }}
        transition={{ type: 'spring', stiffness: 350, damping: 25 }}
        className={`relative border-2 border-dashed rounded-xl p-8 cursor-pointer text-center select-none transition-colors duration-150 overflow-hidden ${
          isUploading ? 'opacity-80 cursor-wait' : 'hover:border-zinc-500'
        }`}
      >
        {/* Animated Dashed Indicator Strip when dragging */}
        {isDragOver && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-white/[0.02] pointer-events-none"
          />
        )}

        <div className="flex flex-col items-center justify-center space-y-3">
          {/* Animated Icon with Spring Bounce */}
          <motion.div
            animate={{
              y: isDragOver ? -8 : 0,
              scale: isDragOver ? 1.15 : 1,
            }}
            transition={{ type: 'spring', stiffness: 400, damping: 18 }}
            className="w-12 h-12 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300"
          >
            {isUploading ? (
              <Loader2 className="w-6 h-6 animate-spin text-zinc-100" />
            ) : isDragOver ? (
              <UploadCloud className="w-6 h-6 text-white" />
            ) : (
              <FileText className="w-6 h-6 text-zinc-400" />
            )}
          </motion.div>

          <div className="space-y-1">
            <p className="text-sm font-medium text-zinc-200">
              {isUploading ? (
                'Processing document...'
              ) : isDragOver ? (
                <span className="text-white font-semibold">Drop document here to upload</span>
              ) : (
                <>
                  Drag & drop your document here, or{' '}
                  <span className="text-zinc-100 underline underline-offset-4 decoration-zinc-600 hover:decoration-zinc-300">
                    browse
                  </span>
                </>
              )}
            </p>
            <p className="text-xs text-zinc-400 font-mono">
              PDF, PNG, JPG, TIFF, BMP (up to {maxSizeMB}MB)
            </p>
          </div>
        </div>

        {/* Selected File Chip preview */}
        <AnimatePresence>
          {selectedFile && !isUploading && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 350, damping: 25 }}
              className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-zinc-900 border border-zinc-700 text-xs text-zinc-200"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-medium truncate max-w-[220px]">{selectedFile.name}</span>
              <span className="text-zinc-400 font-mono">({formatBytes(selectedFile.size)})</span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Error display */}
      <AnimatePresence>
        {errorMessage && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-2 flex items-center gap-2 text-xs text-rose-400 bg-rose-950/20 border border-rose-900/60 rounded px-3 py-2"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
