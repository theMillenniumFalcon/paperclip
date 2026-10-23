import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { DocsFrame } from "@/components/docs-frame";
import {
  flatPages,
  loadDoc,
  loadGroups,
  rewriteDocHref,
} from "@/lib/user-docs";

type DocsParams = { slug?: string[] };

function slugKey(slug: string[] | undefined): string {
  if (!slug || slug.length === 0) return "index";
  return slug.join("/");
}

export function generateStaticParams(): DocsParams[] {
  return flatPages().map((page) => ({
    slug: page.slug === "index" ? [] : page.slug.split("/"),
  }));
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<DocsParams>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = loadDoc(slugKey(slug));
  if (!doc) return { title: "Docs · paperclip" };
  return {
    title: `${doc.title} · paperclip`,
    description: doc.description,
  };
}

function markdownComponents(pages: Set<string>): Components {
  return {
    a: ({ href, children }) => {
      const next = href ? rewriteDocHref(href, pages) : undefined;
      if (next?.startsWith("/")) {
        return <Link href={next}>{children}</Link>;
      }
      return <a href={next}>{children}</a>;
    },
  };
}

export default async function DocsPage({
  params,
}: {
  params: Promise<DocsParams>;
}) {
  const { slug } = await params;
  const key = slugKey(slug);
  const doc = loadDoc(key);
  if (!doc) notFound();

  const groups = loadGroups();
  const pages = flatPages(groups);
  const known = new Set(pages.map((page) => page.slug));
  const index = pages.findIndex((page) => page.slug === key);
  const previous = index > 0 ? pages[index - 1] : null;
  const next = index >= 0 && index < pages.length - 1 ? pages[index + 1] : null;

  return (
    <DocsFrame groups={groups} current={key}>
      <main className="min-w-0 flex-1 px-6 py-10 md:px-12 md:py-12">
        <h1 className="text-stone-100 font-hammersmith mb-4">{doc.title}</h1>
        {doc.description ? (
          <p className="mt-6">
            <span className="font-fanwood text-xl italic">{doc.description}</span>
          </p>
        ) : null}
        <article className="docs-prose prose mt-8">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents(known)}
          >
            {doc.body}
          </ReactMarkdown>
        </article>
        {previous || next ? (
          <div className="mt-12 flex items-baseline justify-between border-t border-stone-800 pt-6 text-stone-500">
            <p className="m-0">
              {previous ? (
                <>
                  Previous <Link href={previous.href}>{previous.title}</Link>
                </>
              ) : null}
              {previous && next ? " · " : null}
              {next ? (
                <>
                  Next <Link href={next.href}>{next.title}</Link>
                </>
              ) : null}
            </p>
            <p className="prose m-0">
              <a
                href="https://github.com/theMillenniumFalcon/paperclip"
                target="_blank"
              >
                GitHub
              </a>
            </p>
          </div>
        ) : null}
      </main>
    </DocsFrame>
  );
}
