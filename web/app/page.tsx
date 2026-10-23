import Link from "next/link";

export default function Home() {
  return (
    <div className="py-32 px-6 md:px-0">
      <div className="mx-auto max-w-2xl flex items-baseline justify-between">
        <h1 className="text-stone-100 font-hammersmith mb-4">Paperclip</h1>
        <p className="prose text-stone-500 m-0">
          <Link href="/docs">Docs</Link>
        </p>
      </div>

      <main className="mx-auto max-w-2xl space-y-12 mt-12">
        <div className="space-y-4 prose">
          <p>
            <span className="font-fanwood text-xl italic">
              Local personal assistant AI agent harness
            </span>
            .
          </p>
          <p>
            It runs on your computer. The same turn can chat, call a tool, and
            write memory. Nothing is synced to a hosted store.
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-stone-100 font-hammersmith text-lg! mb-4">
            Where you talk to it
          </h2>
          <div className="space-y-4 prose w-full max-w-none!">
          <p>Terminal, microphone, or Telegram. One assistant, three doors.</p>
          <pre className="w-full">
            <code>{`paperclip
paperclip voice
paperclip telegram`}</code>
          </pre>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-stone-100 font-hammersmith text-lg! mb-4">What it keeps</h2>
          <div className="space-y-4 prose">
            <p>
              Facts, dated episodes, and skills live in SQLite under{" "}
              <code>~/.paperclip</code>. A small model decides whether a turn needs
              a search. After a few exchanges it files what it learned, and
              rewrites a readable <code>MEMORY.md</code>.
            </p>
            <p>
              Calendar, notes, web search, GitHub, and a local outbox are the
              tools it can call. Public repositories are read even when the
              GitHub CLI is not installed. A dashboard on localhost reads the
              same database.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-stone-100 font-hammersmith text-lg! mb-4">Start</h2>
          <div className="space-y-4 prose">
          <pre>
            <code>{`uv tool install paperclip-agent
paperclip`}</code>
          </pre>
          <p>
            The first launch creates <code>~/.paperclip/.env</code>. Put{" "}
            <code>ANTHROPIC_API_KEY</code> there. OpenAI and OpenRouter are the
            other providers. <code>paperclip api</code> serves the local
            API.
          </p>
          </div>
        </div>

        <div className="flex items-baseline justify-between">
          <p className="text-stone-500 prose m-0">
            Built by{" "}
            <a href="https://github.com/themillenniumfalcon" target="_blank">
              themillenniumfalcon
            </a>
          </p>
          <p className="prose text-stone-500 m-0">
            <a
              href="https://github.com/theMillenniumFalcon/paperclip"
              target="_blank"
            >
              GitHub
            </a>
          </p>
        </div>
      </main>
    </div>
  );
}
