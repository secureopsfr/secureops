/**
 * Tiptap Image extension with resizable NodeView.
 * Extends @tiptap/extension-image by adding width/height attributes
 * and a custom React NodeView with drag-to-resize handles.
 */

import Image from "@tiptap/extension-image";
import { ReactNodeViewRenderer } from "@tiptap/react";
import ResizableImageView from "./ResizableImageView";

const ResizableImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: null,
        parseHTML: (el) => {
          const w =
            el.getAttribute("width") || el.style.width?.replace("px", "");
          return w ? Number(w) || w : null;
        },
        renderHTML: (attrs) => {
          if (!attrs.width) return {};
          return { width: attrs.width };
        },
      },
      height: {
        default: null,
        parseHTML: (el) => {
          const h =
            el.getAttribute("height") || el.style.height?.replace("px", "");
          return h ? Number(h) || h : null;
        },
        renderHTML: (attrs) => {
          if (!attrs.height) return {};
          return { height: attrs.height };
        },
      },
    };
  },

  addNodeView() {
    return ReactNodeViewRenderer(ResizableImageView);
  },
});

export default ResizableImage;
