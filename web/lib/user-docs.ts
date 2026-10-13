import fs from "node:fs";
import path from "node:path";

const root = path.join(process.cwd(), "user-docs");

type DocsConfig = {
  navigation: {
    groups: { group: string; pages: string[] }[];
  };
};

export type DocLink = {
  slug: string;
  href: string;
  title: string;
  description: string;
};

export type DocGroup = {
  group: string;
  pages: DocLink[];
};

export type DocPage = DocLink & {
  body: string;
};

function readConfig(): DocsConfig {
  const raw = fs.readFileSync(path.join(root, "docs.json"), "utf8");
  return JSON.parse(raw) as DocsConfig;
}

function pageFile(slug: string): string | null {
  if (!/^[a-z0-9/-]+$/.test(slug)) return null;
  for (const ext of [".mdx", ".md"]) {
    const file = path.join(root, `${slug}${ext}`);
    const resolved = path.resolve(file);
    if (!resolved.startsWith(path.resolve(root) + path.sep)) return null;
    if (fs.existsSync(resolved)) return resolved;
  }
  return null;
}

export function parseFrontmatter(raw: string): {
  data: Record<string, string>;
  body: string;
} {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) return { data: {}, body: raw };
  const data: Record<string, string> = {};
  for (const line of match[1].split(/\r?\n/)) {
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    data[key] = value;
  }
  return { data, body: raw.slice(match[0].length) };
}

export function hrefFor(slug: string): string {
  return slug === "index" ? "/docs" : `/docs/${slug}`;
}

function linkFor(slug: string): DocLink {
  const file = pageFile(slug);
  if (!file) {
    throw new Error(`user-docs navigation points at a missing page: ${slug}`);
  }
  const { data } = parseFrontmatter(fs.readFileSync(file, "utf8"));
  return {
    slug,
    href: hrefFor(slug),
    title: data.title || slug,
    description: data.description || "",
  };
}

export function loadGroups(): DocGroup[] {
  const config = readConfig();
  return config.navigation.groups.map((group) => ({
    group: group.group,
    pages: group.pages.map(linkFor),
  }));
}

export function flatPages(groups: DocGroup[] = loadGroups()): DocLink[] {
  return groups.flatMap((group) => group.pages);
}

export function loadDoc(slug: string): DocPage | null {
  const file = pageFile(slug);
  if (!file) return null;
  const { data, body } = parseFrontmatter(fs.readFileSync(file, "utf8"));
  return {
    slug,
    href: hrefFor(slug),
    title: data.title || slug,
    description: data.description || "",
    body,
  };
}

export function rewriteDocHref(href: string, pages: Set<string>): string {
  if (
    href.startsWith("http://") ||
    href.startsWith("https://") ||
    href.startsWith("mailto:") ||
    href.startsWith("#")
  ) {
    return href;
  }
  const clean = href
    .split("#")[0]
    .replace(/\.mdx?$/, "")
    .replace(/^\.\//, "")
    .replace(/^\//, "");
  const hash = href.includes("#") ? href.slice(href.indexOf("#")) : "";
  if (clean === "" || clean === "index") return `/docs${hash}`;
  if (pages.has(clean)) return `${hrefFor(clean)}${hash}`;
  return href;
}
