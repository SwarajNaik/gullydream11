import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-dream-bg-primary p-6">
      {/* Logo / Brand */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-dream-text-primary">
          Gully<span className="text-dream-accent-red">Dream11</span>
        </h1>
        <p className="mt-2 text-dream-text-secondary">
          Fantasy Cricket for Your Community
        </p>
      </div>

      {/* CTA Buttons */}
      <div className="flex w-full max-w-xs flex-col gap-4">
        <Link
          href="/login"
          className="rounded-button bg-dream-accent-red py-3 text-center font-semibold text-white transition-colors hover:bg-dream-accent-red-hover"
        >
          Login
        </Link>
        <Link
          href="/register"
          className="rounded-button border border-dream-border py-3 text-center font-semibold text-dream-text-primary transition-colors hover:bg-dream-bg-secondary"
        >
          Register
        </Link>
      </div>

      {/* Footer */}
      <p className="mt-12 text-sm text-dream-text-muted">
        Create teams. Join contests. Win big.
      </p>
    </main>
  );
}
