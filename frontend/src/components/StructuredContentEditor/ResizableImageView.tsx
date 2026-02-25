"use client";

/**
 * React NodeView for resizable images in Tiptap.
 * Renders an <img> with drag handles on corners/edges.
 */

import { useCallback, useRef, useState } from "react";
import { NodeViewWrapper } from "@tiptap/react";
import type { NodeViewProps } from "@tiptap/react";

export default function ResizableImageView({
  node,
  updateAttributes,
  selected,
}: NodeViewProps) {
  const { src, alt, title, width, height } = node.attrs as {
    src: string;
    alt?: string;
    title?: string;
    width?: number | string | null;
    height?: number | string | null;
  };

  const imgRef = useRef<HTMLImageElement>(null);
  const [resizing, setResizing] = useState(false);

  const onMouseDown = useCallback(
    (e: React.MouseEvent, direction: "right" | "bottom" | "corner") => {
      e.preventDefault();
      e.stopPropagation();
      setResizing(true);

      const img = imgRef.current;
      if (!img) return;

      const startX = e.clientX;
      const startY = e.clientY;
      const startWidth = img.offsetWidth;
      const startHeight = img.offsetHeight;
      const aspectRatio = startWidth / startHeight;

      const onMouseMove = (ev: MouseEvent) => {
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;

        let newWidth = startWidth;
        let newHeight = startHeight;

        if (direction === "right") {
          newWidth = Math.max(50, startWidth + dx);
          newHeight = Math.round(newWidth / aspectRatio);
        } else if (direction === "bottom") {
          newHeight = Math.max(50, startHeight + dy);
          newWidth = Math.round(newHeight * aspectRatio);
        } else {
          // corner: use the axis with the largest delta
          newWidth = Math.max(50, startWidth + dx);
          newHeight = Math.round(newWidth / aspectRatio);
        }

        updateAttributes({ width: newWidth, height: newHeight });
      };

      const onMouseUp = () => {
        setResizing(false);
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      };

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    },
    [updateAttributes],
  );

  const imgStyle: React.CSSProperties = {
    width: width
      ? typeof width === "number"
        ? `${width}px`
        : width
      : undefined,
    height: height
      ? typeof height === "number"
        ? `${height}px`
        : height
      : undefined,
    maxWidth: "100%",
    display: "block",
    borderRadius: "0.25rem",
  };

  return (
    <NodeViewWrapper
      as="div"
      className={`resizable-image-wrapper${selected ? " selected" : ""}${resizing ? " resizing" : ""}`}
      style={{ display: "inline-block", position: "relative", lineHeight: 0 }}
    >
      <img
        ref={imgRef}
        src={src}
        alt={alt || ""}
        title={title || undefined}
        style={imgStyle}
        draggable={false}
        loading="lazy"
        decoding="async"
      />

      {/* Resize handles – only visible when the node is selected */}
      {selected && (
        <>
          {/* Right edge */}
          <div
            className="resize-handle resize-handle-right"
            onMouseDown={(e) => onMouseDown(e, "right")}
          />
          {/* Bottom edge */}
          <div
            className="resize-handle resize-handle-bottom"
            onMouseDown={(e) => onMouseDown(e, "bottom")}
          />
          {/* Bottom-right corner */}
          <div
            className="resize-handle resize-handle-corner"
            onMouseDown={(e) => onMouseDown(e, "corner")}
          />
        </>
      )}
    </NodeViewWrapper>
  );
}
