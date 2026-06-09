"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useState } from "react";

import { Drawer } from "@/components/ui/Drawer";
import { ProgressSelect } from "@/components/ui/ProgressSelect";

const NAV_LINKS: ReadonlyArray<{ href: string; label: string }> = [
  { href: "/graph", label: "关系图谱" },
  { href: "/timeline", label: "剧情时间线" },
  { href: "/characters", label: "人物卷宗" },
  { href: "/search", label: "搜索路径" },
  { href: "/submit", label: "补充线索" },
];

/**
 * Site header with desktop nav and mobile drawer.
 *
 * The mobile hamburger button is always visible at `< md` breakpoints.
 * The drawer renders the same nav links as real `<a>` elements — no
 * JS-only hidden-link pattern. Screen readers see the links inside a
 * labelled `<dialog>`.
 */
export function SiteHeader() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();

  const openDrawer = useCallback(() => setDrawerOpen(true), []);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--line)] bg-[rgba(21,19,15,.94)] shadow-[0_10px_35px_rgba(0,0,0,.22)] backdrop-blur-md">
      <div className="mx-auto flex max-w-[1500px] items-center justify-between px-5 py-4 lg:px-10">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
        >
          <span className="seal-mark !size-9 text-sm">
            燕
          </span>
          <span>
            <strong className="block tracking-[0.28em] text-[var(--paper-light)]">燕云卷宗</strong>
            <small className="text-[10px] tracking-[0.18em] text-[var(--fog)]">
              非官方剧情关系图谱
            </small>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav aria-label="主导航" className="hidden items-center gap-7 text-sm text-[var(--paper)] md:flex">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative py-2 tracking-[0.08em] transition hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)] ${
                  isActive
                    ? "nav-bookmark-active font-medium"
                    : "after:absolute after:bottom-0 after:left-1/2 after:h-px after:w-0 after:bg-[var(--cinnabar-bright)] after:transition-[left,width] hover:after:left-0 hover:after:w-full"
                }`}
              >
                {link.label}
                {isActive && (
                  <span
                    className="absolute bottom-[-17px] left-1/2 -translate-x-1/2 w-3.5 h-4 bg-[var(--cinnabar)] clip-bookmark-tail shadow-md pointer-events-none"
                    aria-hidden="true"
                  />
                )}
              </Link>
            );
          })}
          <ProgressSelect variant="compact" />
        </nav>

        {/* Mobile hamburger — always visible, real button, triggers Drawer */}
        <button
          type="button"
          onClick={openDrawer}
          aria-label="打开导航菜单"
          aria-haspopup="dialog"
          className="grid size-9 place-items-center border border-[var(--line)] text-[var(--paper)] transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)] md:hidden"
        >
          <svg
            aria-hidden="true"
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          >
            <line x1="2" y1="4" x2="16" y2="4" />
            <line x1="2" y1="9" x2="16" y2="9" />
            <line x1="2" y1="14" x2="16" y2="14" />
          </svg>
        </button>
        <noscript>
          <nav aria-label="无脚本导航" className="flex gap-3 text-xs md:hidden">
            {NAV_LINKS.slice(0, 3).map((link) => (
              <Link key={link.href} href={link.href}>
                {link.label}
              </Link>
            ))}
          </nav>
        </noscript>
      </div>

      {/* Mobile drawer */}
      <Drawer
        open={drawerOpen}
        onClose={closeDrawer}
        aria-label="移动端导航"
      >
        <div className="mb-6 flex items-center justify-between">
          <span className="text-sm font-semibold tracking-[0.2em] text-[var(--paper)]">
            导航
          </span>
          <button
            type="button"
            onClick={closeDrawer}
            aria-label="关闭导航菜单"
            className="grid size-8 place-items-center text-[var(--fog)] transition hover:text-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
          >
            <svg
              aria-hidden="true"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            >
              <line x1="3" y1="3" x2="13" y2="13" />
              <line x1="13" y1="3" x2="3" y2="13" />
            </svg>
          </button>
        </div>

        <nav aria-label="移动端导航" className="flex flex-col gap-1">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={closeDrawer}
                className={`py-3 text-sm tracking-wide transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--cinnabar-bright)] ${
                  isActive
                    ? "border-b border-[var(--cinnabar)] text-[var(--cinnabar-bright)] font-semibold pl-2"
                    : "border-b border-[var(--line)] text-[var(--paper)] hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-[var(--line)] pt-6">
          <ProgressSelect variant="compact" className="w-full" />
        </div>
      </Drawer>
    </header>
  );
}
