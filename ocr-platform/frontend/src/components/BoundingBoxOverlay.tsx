import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { OCRWord, BoundingBox } from '../lib/api';
import { ZoomIn, ZoomOut, RotateCcw, Crosshair } from 'lucide-react';

interface HighlightBox {
  bbox: BoundingBox;
  label?: string;
  color?: string;
}

interface BoundingBoxOverlayProps {
  imageUrl?: string;
  words: OCRWord[];
  pageWidth?: number;
  pageHeight?: number;
  highlightBoxes?: HighlightBox[];
  onSelectWord?: (word: OCRWord) => void;
  selectedWord?: OCRWord | null;
}

export const BoundingBoxOverlay: React.FC<BoundingBoxOverlayProps> = ({
  imageUrl,
  words,
  pageWidth = 1000,
  pageHeight = 1400,
  highlightBoxes = [],
  onSelectWord,
  selectedWord,
}) => {
  const [zoom, setZoom] = useState(1);
  const [hoveredWord, setHoveredWord] = useState<OCRWord | null>(null);
  const [showBoxes, setShowBoxes] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  // Compute scale factors
  const effectiveW = pageWidth || 1000;
  const effectiveH = pageHeight || 1400;

  const handleZoomIn = () => setZoom((z) => Math.min(2.5, z + 0.25));
  const handleZoomOut = () => setZoom((z) => Math.max(0.5, z - 0.25));
  const handleResetZoom = () => setZoom(1);

  return (
    <div className="flex flex-col h-full bg-[#09090b] border border-zinc-800 rounded-lg overflow-hidden">
      {/* Top Toolbar */}
      <div className="px-3 py-2 bg-[#0d0d10] border-b border-zinc-800 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="text-zinc-400 font-medium">Document View</span>
          <span className="font-mono text-zinc-400">({words.length} tokens)</span>
          {selectedWord && (
            <span className="font-mono text-zinc-200 bg-zinc-800 px-2 py-0.5 rounded border border-zinc-700">
              Selected: "{selectedWord.text}"
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBoxes(!showBoxes)}
            className={`px-2 py-1 rounded text-xs font-mono transition-colors ${
              showBoxes ? 'bg-zinc-800 text-white border border-zinc-700' : 'text-zinc-400 hover:text-white'
            }`}
          >
            {showBoxes ? 'Hide BBoxes' : 'Show BBoxes'}
          </button>

          <div className="h-4 w-px bg-zinc-800 mx-1" />

          <button
            onClick={handleZoomOut}
            className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="font-mono text-zinc-400 text-[11px] w-10 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800 transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Canvas Scroll Area */}
      <div
        ref={containerRef}
        className="relative flex-1 overflow-auto p-4 flex items-center justify-center bg-[#09090b]"
      >
        <motion.div
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'top center',
            transition: 'transform 0.15s ease-out',
          }}
          className="relative max-w-full shadow-elevated bg-[#0e0e12] border border-zinc-800 rounded overflow-hidden"
        >
          {imageUrl ? (
            <img
              src={imageUrl}
              alt="Document Page"
              className="block max-w-full h-auto select-none pointer-events-none"
              style={{ width: effectiveW, height: effectiveH }}
              onError={(e) => {
                // Fallback rendering placeholder if image not accessible
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          ) : (
            <div
              style={{ width: effectiveW, height: effectiveH }}
              className="bg-[#0b0b0e] flex items-center justify-center text-zinc-400 text-xs font-mono"
            >
              No Image Loaded (Dimensions: {effectiveW}x{effectiveH})
            </div>
          )}

          {/* SVG Bounding Boxes Overlay */}
          {showBoxes && (
            <svg
              className="absolute inset-0 w-full h-full pointer-events-auto"
              viewBox={`0 0 ${effectiveW} ${effectiveH}`}
              preserveAspectRatio="none"
            >
              {/* Render regular OCR words */}
              {words.map((w, idx) => {
                const isSelected = selectedWord?.word_index === w.word_index;
                const isHovered = hoveredWord?.word_index === w.word_index;

                // Color based on confidence
                let stroke = 'rgba(161, 161, 170, 0.4)';
                let fill = 'transparent';
                if (w.confidence >= 0.85) {
                  stroke = 'rgba(16, 185, 129, 0.6)';
                } else if (w.confidence >= 0.60) {
                  stroke = 'rgba(245, 158, 11, 0.6)';
                } else {
                  stroke = 'rgba(244, 63, 94, 0.6)';
                }

                if (isSelected) {
                  stroke = '#ffffff';
                  fill = 'rgba(255, 255, 255, 0.15)';
                } else if (isHovered) {
                  fill = 'rgba(255, 255, 255, 0.08)';
                }

                return (
                  <rect
                    key={idx}
                    x={w.bounding_box.x}
                    y={w.bounding_box.y}
                    width={w.bounding_box.width}
                    height={w.bounding_box.height}
                    fill={fill}
                    stroke={stroke}
                    strokeWidth={isSelected ? 2 : 1}
                    className="cursor-pointer transition-all duration-75"
                    onMouseEnter={() => setHoveredWord(w)}
                    onMouseLeave={() => setHoveredWord(null)}
                    onClick={() => onSelectWord?.(w)}
                  />
                );
              })}

              {/* Render rule extraction highlights */}
              {highlightBoxes.map((hb, i) => (
                <g key={`hl-${i}`}>
                  <rect
                    x={hb.bbox.x}
                    y={hb.bbox.y}
                    width={hb.bbox.width}
                    height={hb.bbox.height}
                    fill="rgba(56, 189, 248, 0.15)"
                    stroke={hb.color || '#38bdf8'}
                    strokeWidth={2}
                    strokeDasharray="4 2"
                  />
                  {hb.label && (
                    <text
                      x={hb.bbox.x}
                      y={Math.max(12, hb.bbox.y - 4)}
                      fill={hb.color || '#38bdf8'}
                      fontSize={11}
                      fontFamily="JetBrains Mono, monospace"
                      fontWeight="bold"
                    >
                      {hb.label}
                    </text>
                  )}
                </g>
              ))}
            </svg>
          )}
        </motion.div>
      </div>

      {/* Word Inspector Footer Bar */}
      <div className="px-3 py-2 bg-[#0c0c0e] border-t border-zinc-800 flex items-center justify-between text-xs font-mono text-zinc-400">
        <AnimatePresence mode="wait">
          {hoveredWord ? (
            <motion.div
              key={hoveredWord.word_index}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-4 text-zinc-300"
            >
              <div>
                <span className="text-zinc-400 mr-1">Token:</span>
                <span className="font-semibold text-white font-mono bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700">
                  {hoveredWord.text}
                </span>
              </div>
              <div>
                <span className="text-zinc-400 mr-1">Conf:</span>
                <span
                  className={
                    hoveredWord.confidence >= 0.85
                      ? 'text-emerald-400'
                      : hoveredWord.confidence >= 0.60
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }
                >
                  {Math.round(hoveredWord.confidence * 100)}%
                </span>
              </div>
              <div>
                <span className="text-zinc-400 mr-1">Box:</span>
                <span>
                  [{hoveredWord.bounding_box.x}, {hoveredWord.bounding_box.y},{' '}
                  {hoveredWord.bounding_box.width}, {hoveredWord.bounding_box.height}]
                </span>
              </div>
              <div>
                <span className="text-zinc-400 mr-1">Line:</span>
                <span>{hoveredWord.line_number}</span>
              </div>
            </motion.div>
          ) : (
            <div className="flex items-center gap-1 text-zinc-400">
              <Crosshair className="w-3.5 h-3.5" />
              <span>Hover over tokens to inspect OCR confidence and pixel coordinates</span>
            </div>
          )}
        </AnimatePresence>

        <div className="text-[11px] text-zinc-400">
          Page Size: {effectiveW} × {effectiveH} px
        </div>
      </div>
    </div>
  );
};
