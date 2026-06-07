"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  type ReactNode,
} from "react";

interface DrawerProps {
  /** Whether the drawer is currently open. */
  open: boolean;
  /** Called when the user requests closing (Escape, overlay click). */
  onClose: () => void;
  /** Accessible label announced by screen readers. */
  "aria-label": string;
  /** Drawer content. */
  children: ReactNode;
}

/**
 * Accessible slide-in drawer built on native `<dialog>`.
 *
 * Features:
 * - Native `<dialog>` semantics (`showModal` / `close`) so the browser
 *   manages the top-layer, backdrop click-to-close, and focus trapping.
 * - Escape key closes via the browser's built-in `cancel` event.
 * - Scroll lock on `<body>` while open (`overflow: hidden`).
 * - Focus is returned to the previously-active element on close.
 * - Backdrop overlay with fade transition.
 *
 * No JavaScript-only hidden links — the trigger lives in `SiteHeader`
 * and the drawer renders real, focusable nav links.
 */
export function Drawer({ open, onClose, children, ...rest }: DrawerProps) {
  const dialogId = useId();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const triggerRef = useRef<Element | null>(null);

  /* ---- open / close side-effects ---- */

  const handleCancel = useCallback(
    (e: Event) => {
      // The browser fires "cancel" on Escape for <dialog>.
      e.preventDefault();
      onClose();
    },
    [onClose],
  );

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open) {
      // Remember what was focused so we can restore it.
      triggerRef.current = document.activeElement;
      document.body.style.overflow = "hidden";
      if (!dialog.open) {
        dialog.showModal();
      }
      dialog.addEventListener("cancel", handleCancel);
    } else if (dialog.open) {
      dialog.close();
    }

    return () => {
      dialog.removeEventListener("cancel", handleCancel);
      document.body.style.overflow = "";
    };
  }, [open, handleCancel]);

  // Restore focus to the trigger element after the dialog closes.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleDialogClose = () => {
      document.body.style.overflow = "";
      if (triggerRef.current instanceof HTMLElement) {
        triggerRef.current.focus();
      }
    };

    dialog.addEventListener("close", handleDialogClose);
    return () => dialog.removeEventListener("close", handleDialogClose);
  }, []);

  /* ---- overlay click: close when clicking the backdrop ---- */

  const handleDialogClick = useCallback(
    (e: React.MouseEvent<HTMLDialogElement>) => {
      // A click directly on the <dialog> (not a child) means backdrop click.
      if (e.target === dialogRef.current) {
        onClose();
      }
    },
    [onClose],
  );

  return (
    <dialog
      ref={dialogRef}
      id={dialogId}
      onClick={handleDialogClick}
      aria-modal="true"
      className="m-0 ml-auto h-dvh max-h-dvh w-[min(80vw,320px)] max-w-none border-none bg-[var(--ink)] p-0 text-[var(--paper-light)] backdrop:bg-black/50 backdrop:backdrop-blur-sm"
      {...rest}
    >
      <div className="flex h-full flex-col overflow-y-auto p-6">
        {children}
      </div>
    </dialog>
  );
}
