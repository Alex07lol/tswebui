import React, { useState } from 'react';
import { ZoomIn, ZoomOut, Maximize2, Download, ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react';

interface PDFViewerProps {
  fileUrl: string;
  filename: string;
  mimeType?: string;
  pageCount?: number;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  fileUrl,
  filename,
  mimeType = 'application/pdf',
  pageCount = 1,
}) => {
  const [zoom, setZoom] = useState<number>(100);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const isImage = mimeType.startsWith('image/');

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 250));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50));
  const handleZoomReset = () => setZoom(100);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className={`flex flex-col bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl ${isFullscreen ? 'fixed inset-0 z-50 rounded-none' : 'h-[750px]'}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-900/90 border-b border-zinc-800 text-zinc-300 select-none">
        {/* Page navigation */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage <= 1}
            className="p-1.5 rounded hover:bg-zinc-800 disabled:opacity-30 transition-colors"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-zinc-400">
            Page <span className="text-zinc-100 font-semibold">{currentPage}</span> of {pageCount}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(pageCount, p + 1))}
            disabled={currentPage >= pageCount}
            className="p-1.5 rounded hover:bg-zinc-800 disabled:opacity-30 transition-colors"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Zoom and Controls */}
        <div className="flex items-center space-x-1.5">
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono w-12 text-center text-zinc-300 font-medium">
            {zoom}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomReset}
            className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors ml-1"
            title="Reset Zoom (100%)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <div className="h-4 w-px bg-zinc-800 mx-2" />

          <button
            onClick={toggleFullscreen}
            className="p-1.5 rounded hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            <Maximize2 className="w-4 h-4" />
          </button>

          <a
            href={fileUrl}
            download={filename}
            className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition-colors shadow-sm ml-2"
          >
            <Download className="w-3.5 h-3.5 mr-1" />
            <span>Download</span>
          </a>
        </div>
      </div>

      {/* Document Viewport */}
      <div className="flex-1 overflow-auto bg-zinc-900/50 p-6 flex items-center justify-center">
        <div
          className="transition-transform duration-150 origin-center bg-white shadow-xl rounded"
          style={{ transform: `scale(${zoom / 100})` }}
        >
          {isImage ? (
            <img
              src={fileUrl}
              alt={filename}
              className="max-w-full max-h-full object-contain pointer-events-auto"
            />
          ) : (
            <iframe
              src={`${fileUrl}#page=${currentPage}`}
              title={filename}
              className="w-[850px] h-[1100px] border-0 rounded"
            />
          )}
        </div>
      </div>
    </div>
  );
};
