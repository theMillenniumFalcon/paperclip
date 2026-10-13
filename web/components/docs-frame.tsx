"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import type { DocGroup } from "@/lib/user-docs";

function DocsNav({
  groups,
  current,
  onNavigate,
}: {
  groups: DocGroup[];
  current: string;
  onNavigate?: () => void;
}) {
  return (
    <nav className="space-y-6 px-6 py-6" aria-label="Docs">
      {groups.map((group) => (
        <div key={group.group}>
          <p className="font-mono text-[11px] tracking-widest text-stone-500 uppercase">
            {group.group}
          </p>
          <ul className="mt-2 space-y-1">
            {group.pages.map((page) => (
              <li key={page.slug}>
                <Link
                  href={page.href}
                  aria-current={page.slug === current ? "page" : undefined}
                  onClick={onNavigate}
                >
                  {page.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function DocsFrame({
  groups,
  current,
  children,
}: {
  groups: DocGroup[];
  current: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col md:min-h-screen md:flex-row">
      <header className="sticky top-0 z-20 border-b border-stone-800 bg-stone-900 md:hidden">
        <div className="flex items-center justify-between px-6 py-4">
          <Link href="/" className="font-hammersmith text-stone-100">
            Paperclip
          </Link>
          <button
            type="button"
            className="border border-stone-800 p-2 text-stone-100 transition-colors duration-300 hover:text-purple-400"
            aria-expanded={open}
            aria-controls="docs-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? (
              <X className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Menu className="h-5 w-5" aria-hidden="true" />
            )}
          </button>
        </div>
        {open ? (
          <div
            id="docs-menu"
            className="absolute inset-x-0 top-full max-h-[70vh] overflow-y-auto border-b border-stone-800 bg-stone-900"
          >
            <DocsNav
              groups={groups}
              current={current}
              onNavigate={() => setOpen(false)}
            />
          </div>
        ) : null}
      </header>

      <aside className="hidden border-stone-800 md:sticky md:top-0 md:block md:h-screen md:w-60 md:shrink-0 md:overflow-y-auto md:border-r">
        <div className="px-6 pt-8">
          <Link href="/" className="font-hammersmith text-stone-100">
            Paperclip
          </Link>
          <p className="mt-1 text-xs text-stone-500">
            <Link href="/docs">Docs</Link>
          </p>
        </div>
        <DocsNav groups={groups} current={current} />
      </aside>

      {children}
    </div>
  );
}
