export default function Home() {
  return (
    <div className="py-32 px-6 md:px-0">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-stone-100 font-hammersmith mb-4">Paperclip</h1>
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
            More coming soon...
          </p>
        </div>

        <p className="text-stone-500 prose">
          Built by{" "}
          <a href="https://github.com/themillenniumfalcon" target="_blank">
            themillenniumfalcon
          </a>
        </p>
      </main>
    </div>
  );
}